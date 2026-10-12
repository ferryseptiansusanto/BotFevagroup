import os
import re
import json
import asyncio
import shutil
from datetime import datetime
from openpyxl import Workbook, load_workbook
from config.settings import DATA_DIR, GROUP_REGISTRY_FILE

excel_lock = asyncio.Lock()

def sanitize_filename(name: str) -> str:
    clean_name = re.sub(r'[\\/*?:"<>|]', "", name).strip()
    return clean_name or "Unnamed_Group"

def load_registry() -> dict:
    if not os.path.exists(GROUP_REGISTRY_FILE):
        return {}
    try:
        with open(GROUP_REGISTRY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_registry(registry: dict):
    with open(GROUP_REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

def get_filepath(chat_id: int) -> str | None:
    filename = load_registry().get(str(chat_id))
    return os.path.join(DATA_DIR, filename) if filename else None

async def setup_excel(chat_id: int, group_title: str) -> str:
    async with excel_lock:
        registry = load_registry()
        filename = f"{sanitize_filename(group_title)}.xlsx"
        filepath = os.path.join(DATA_DIR, filename)

        if not os.path.exists(filepath):
            wb = Workbook()
            ws = wb.active
            ws.title = "Activity Logs"
            # HEADER FINAL: 9 Kolom (Termasuk Detail di ujung kanan)
            ws.append(["Timestamp", "User ID", "Username", "Nama Lengkap", "User Level", "Tipe", "Keterangan", "Satuan", "Jumlah", "Detail"])
            wb.save(filepath)

        registry[str(chat_id)] = filename
        save_registry(registry)
        return filepath


async def append_data(chat_id: int, user_id: int, username: str, full_name: str, level: str, tipe_trx: str, keterangan: str,
                      satuan: str, jumlah: str, detail: str = "-") -> tuple[bool, int]:
    filepath = get_filepath(chat_id)
    if not filepath or not os.path.exists(filepath):
        return False, 0

    async with excel_lock:
        wb = load_workbook(filepath)
        ws = wb.active
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # MENYIMPAN KE 10 KOLOM: Termasuk variabel 'detail'
        ws.append(
            [timestamp, str(user_id), f"@{username}" if username else "-", full_name, level, tipe_trx, keterangan, satuan, jumlah,
             detail])
        wb.save(filepath)

        # MENGEMBALIKAN ID BARIS: (Baris Excel - 1)
        user_row_id = ws.max_row - 1
        return True, user_row_id


async def edit_data(chat_id: int, row: int, tipe_trx: str, keterangan: str, satuan: str, jumlah: str, detail: str,
                    require_same_day: bool = False) -> tuple[bool, str]:
    filepath = get_filepath(chat_id)
    if not filepath or not os.path.exists(filepath):
        return False, "File log tidak ditemukan."

    async with excel_lock:
        wb = load_workbook(filepath)
        ws = wb.active

        # TRIK MATEMATIKA: Kompensasi Header
        excel_row = row + 1

        if excel_row <= 1 or excel_row > ws.max_row:
            return False, f"Nomor baris tidak valid. Saat ini hanya ada data dari baris 1 hingga {ws.max_row - 1}."

        # VALIDASI TANGGAL (HARI EDIT)
        if require_same_day:
            cell_value = ws.cell(row=excel_row, column=1).value
            if not cell_value:
                return False, "Baris yang dipilih tidak memiliki data tanggal."

            try:
                if isinstance(cell_value, datetime):
                    entry_date = cell_value.date()
                else:
                    entry_date = datetime.strptime(str(cell_value).strip(), "%Y-%m-%d %H:%M:%S").date()

                try:
                    max_days = int(os.getenv("MAX_EDIT_DAYS", 0))
                except ValueError:
                    max_days = 0

                current_date = datetime.now().date()
                delta_days = (current_date - entry_date).days

                if delta_days > max_days:
                    pesan_waktu = "HARI INI" if max_days == 0 else f"{max_days} HARI terakhir"
                    return False, f"User Input hanya diizinkan mengedit data pada {pesan_waktu}."
                elif delta_days < 0:
                    return False, "Gagal: Data memiliki tanggal masa depan yang tidak valid."

            except Exception:
                return False, "Format tanggal pada baris tersebut tidak dapat divalidasi."

        # EDIT 4 KOLOM UTAMA (Termasuk Detail di kolom ke-10)
        ws.cell(row=excel_row, column=6, value=tipe_trx)
        ws.cell(row=excel_row, column=7, value=keterangan)
        ws.cell(row=excel_row, column=8, value=satuan)
        ws.cell(row=excel_row, column=9, value=jumlah)
        ws.cell(row=excel_row, column=10, value=detail)
        wb.save(filepath)

        return True, "Sukses"


async def delete_data(chat_id: int, row: int) -> tuple[bool, str]:
    filepath = get_filepath(chat_id)
    if not filepath or not os.path.exists(filepath):
        return False, "File log tidak ditemukan."

    async with excel_lock:
        wb = load_workbook(filepath)
        ws = wb.active

        # TRIK MATEMATIKA: Kompensasi Header
        excel_row = row + 1

        if excel_row <= 1 or excel_row > ws.max_row:
            return False, f"Nomor baris tidak valid. Saat ini hanya ada data dari baris 1 hingga {ws.max_row - 1}."

        ws.delete_rows(excel_row)
        wb.save(filepath)

        return True, "Sukses"


async def reset_excel_data(chat_id: int) -> tuple[bool, str]:
    filepath = get_filepath(chat_id)
    if not filepath or not os.path.exists(filepath):
        return False, "File log Excel tidak ditemukan. Gunakan /setup terlebih dahulu."

    async with excel_lock:
        try:
            wb = load_workbook(filepath)

            # 1. Dapatkan nama sheet yang aktif (misal: "Activity Logs")
            active_sheet_name = wb.active.title

            # 2. Hapus sheet tersebut secara total untuk membuang semua data lama dan kotoran cache
            del wb[active_sheet_name]

            # 3. Buat ulang sheet-nya di urutan pertama (index=0)
            ws = wb.create_sheet(title=active_sheet_name, index=0)

            # 4. Tulis ulang Header format TERBARU (9 Kolom)
            ws.append(
                ["Timestamp", "User ID", "Username", "Nama Lengkap", "User Level", "Tipe","Keterangan", "Satuan", "Jumlah",
                 "Detail"])

            wb.save(filepath)
            return True, "Berhasil mereset Excel."

        except Exception as e:
            return False, f"Terjadi kesalahan saat mereset Excel: {e}"

async def get_pivot_summary(chat_id: int) -> tuple[bool, dict | str]:
    filepath = get_filepath(chat_id)
    if not filepath or not os.path.exists(filepath):
        return False, "File log tidak ditemukan. Belum ada data."

    summary = {}
    async with excel_lock:
        wb = load_workbook(filepath, data_only=True)
        ws = wb.active

        # Mulai dari baris ke-2 untuk melewati Header
        for row_data in ws.iter_rows(min_row=2, min_col=6, max_col=9, values_only=True):
            tipe, keterangan, satuan, jumlah = row_data

            # Abaikan baris jika keterangan atau jumlah kosong
            if not keterangan or jumlah is None or not tipe:
                continue

            # Konversi jumlah menjadi angka (float)
            try:
                jumlah_float = float(jumlah)
            except (ValueError, TypeError):
                continue

            key = (str(keterangan).strip(), str(satuan).strip() if satuan else "-")
            if key not in summary:
                summary[key] = {"IN": 0.0, "OUT": 0.0}

            t_up = str(tipe).strip().upper()
            if t_up in ["IN", "OUT"]:
                summary[key][t_up] += jumlah_float

    return True, summary


async def generate_export_file(chat_id: int) -> tuple[bool, str]:
    filepath = get_filepath(chat_id)
    if not filepath or not os.path.exists(filepath):
        return False, "File log tidak ditemukan. Pastikan /setup sudah dijalankan."

    export_path = filepath.replace(".xlsx", "_Export.xlsx")

    async with excel_lock:
        try:
            shutil.copy2(filepath, export_path)

            wb = load_workbook(export_path, data_only=True)
            ws_log = wb.active
            summary = {}

            for row_data in ws_log.iter_rows(min_row=2, min_col=6, max_col=9, values_only=True):
                tipe, keterangan, satuan, jumlah = row_data

                if not keterangan or jumlah is None or not tipe:
                    continue

                try:
                    jumlah_float = float(jumlah)
                except (ValueError, TypeError):
                    continue

                key = (str(keterangan).strip(), str(satuan).strip() if satuan else "-")
                if key not in summary:
                    summary[key] = {"IN": 0.0, "OUT": 0.0}
                t_up = str(tipe).strip().upper()
                if t_up in ["IN", "OUT"]:
                    summary[key][t_up] += jumlah_float

            if "Rekap" in wb.sheetnames:
                del wb["Rekap"]

            ws_rekap = wb.create_sheet(title="Rekap")
            ws_rekap.append(["No", "Kode Barang", "Satuan", "Total Masuk (IN)", "Total Keluar (OUT)", "Sisa Saldo"])

            sorted_keys = sorted(summary.keys(), key=lambda x: x[0].lower())
            for index, (ket, sat) in enumerate(sorted_keys, start=1):
                in_val = summary[(ket, sat)]["IN"]
                out_val = summary[(ket, sat)]["OUT"]
                sisa_val = in_val - out_val

                def fmt(v): return int(v) if v.is_integer() else round(v, 2)

                ws_rekap.append([index, ket, sat, fmt(in_val), fmt(out_val), fmt(sisa_val)])

            wb.save(export_path)
            wb.close()

            return True, export_path

        except Exception as e:
            return False, str(e)
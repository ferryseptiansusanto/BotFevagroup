import os
import re
import json
import asyncio
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
    with open(GROUP_REGISTRY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

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
            # Header baru sesuai permintaan
            ws.append(["Timestamp", "User ID", "Username", "Nama Lengkap", "User Level", "Keterangan", "Satuan", "Jumlah"])
            wb.save(filepath)

        registry[str(chat_id)] = filename
        save_registry(registry)
        return filepath

async def append_data(chat_id: int, user_id: int, username: str, full_name: str, level: str, keterangan: str, satuan: str, jumlah: str) -> bool:
    filepath = get_filepath(chat_id)
    if not filepath or not os.path.exists(filepath): return False

    async with excel_lock:
        wb = load_workbook(filepath)
        ws = wb.active
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Memasukkan data ke 8 kolom
        ws.append([timestamp, str(user_id), f"@{username}" if username else "-", full_name, level, keterangan, satuan, jumlah])
        wb.save(filepath)
        return True

async def edit_data(chat_id: int, row: int, keterangan: str, satuan: str, jumlah: str, require_same_day: bool = False) -> tuple[bool, str]:
    filepath = get_filepath(chat_id)
    if not filepath or not os.path.exists(filepath): return False, "File log tidak ditemukan."

    async with excel_lock:
        wb = load_workbook(filepath)
        ws = wb.active
        if row <= 1 or row > ws.max_row: return False, "Nomor baris tidak valid."

        if require_same_day:
            entry_ts = str(ws.cell(row=row, column=1).value)
            try:
                entry_date = datetime.strptime(entry_ts, "%Y-%m-%d %H:%M:%S").date()
                if entry_date != datetime.now().date():
                    return False, "User_Input hanya boleh mengedit data hari yang sama."
            except Exception:
                pass

        # Timpa kolom 6 (Keterangan), 7 (Satuan), dan 8 (Jumlah)
        ws.cell(row=row, column=6, value=f"[Edited] {keterangan}")
        ws.cell(row=row, column=7, value=satuan)
        ws.cell(row=row, column=8, value=jumlah)
        wb.save(filepath)
        return True, "Sukses"

async def delete_data(chat_id: int, row: int) -> bool:
    filepath = get_filepath(chat_id)
    if not filepath or not os.path.exists(filepath): return False

    async with excel_lock:
        wb = load_workbook(filepath)
        ws = wb.active
        if row <= 1 or row > ws.max_row: return False
        ws.delete_rows(row)
        wb.save(filepath)
        return True
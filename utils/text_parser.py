import re
from datetime import datetime
from utils.math_utils import calculate_dimension

def parse_item_input(raw_text: str) -> tuple[bool, str, str, str, str, str, str, str, str]:
    """
    Mengurai teks format: {in/out}, kode barang, satuan, jumlah, (detail)
    Kurung (...) bebas ditempatkan di mana saja.
    Return: (sukses, tipe, keterangan, satuan, jumlah, detail, rumus, custom_ts, err_msg)
    """

    # 1. Ekstraksi Timestamp Custom menggunakan simbol '@' (Contoh: @12102026 atau @12102026 14:30)
    # Mencari pola '@' diikuti oleh 8 digit angka, dan opsional diikuti spasi dan waktu HH:MM
    match_ts = re.search(r'@(\d{8}(?:\s+\d{2}:\d{2})?)', raw_text)
    if match_ts:
        ts_str = match_ts.group(1).strip()
        # Hapus bagian tanggal dari teks mentah
        raw_text = re.sub(r'@\d{8}(?:\s+\d{2}:\d{2})?', '', raw_text).strip()
        raw_text = re.sub(r',\s*,+', ',', raw_text).strip(' ,')

        try:
            # Parse Format: DDMMYYYY
            if len(ts_str) == 8:
                parsed_date = datetime.strptime(ts_str, "%d%m%Y")
                custom_ts = parsed_date.strftime("%Y-%m-%d %H:%M:%S")
            # Parse Format: DDMMYYYY HH:MM
            else:
                parsed_date = datetime.strptime(ts_str, "%d%m%Y %H:%M")
                custom_ts = parsed_date.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            return False, "", "", "", "", "", "", None, f"Format tanggal '@{ts_str}' salah. Gunakan @DDMMYYYY"


    # 2. Ekstraksi Detail di mana pun posisinya
    if ('(' in raw_text and ')' not in raw_text) or (')' in raw_text and '(' not in raw_text):
        return False, "", "", "", "", "", "", None, "Tanda kurung tidak lengkap"

    match = re.search(r'\((.*?)\)', raw_text)
    if match:
        detail = match.group(1).replace('[', '').replace(']', '').strip()
        text_clean = re.sub(r'\(.*?\)', '', raw_text).strip()
        # Bersihkan koma ganda berulang akibat penghapusan bracket
        text_clean = re.sub(r',\s*,+', ',', text_clean).strip(' ,')
    else:
        detail = "-"
        text_clean = raw_text.strip()

    # 3. Membagi 4 kolom utama dari kanan: tipe, keterangan, satuan, jumlah
    parts = [p.strip() for p in text_clean.rsplit(',', 3)]
    if len(parts) != 4:
        return False, "", "", "", "", "", "", None, "Format salah. Gunakan: in/out, Kode Barang, Satuan, Jumlah"

    tipe_trx, keterangan, satuan, jumlah_mentah = parts
    tipe_upper = tipe_trx.upper()

    if tipe_upper not in ["IN", "OUT"]:
        return False, "", "", "", "", "", "", None, f"Tipe '{tipe_trx}' tidak valid. Gunakan 'in' atau 'out'"

    jumlah_final, rumus_asli = calculate_dimension(jumlah_mentah)
    return True, tipe_upper, keterangan, satuan, jumlah_final, detail, rumus_asli, custom_ts, ""
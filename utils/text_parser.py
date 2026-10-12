import re
from utils.math_utils import calculate_dimension

def parse_item_input(raw_text: str) -> tuple[bool, str, str, str, str, str, str, str]:
    """
    Mengurai teks format: {in/out}, kode barang, satuan, jumlah [detail]
    Kurung siku [...] bebas ditempatkan di mana saja.
    Return: (sukses, tipe, keterangan, satuan, jumlah, detail, rumus, err_msg)
    """
    if ('[' in raw_text and ']' not in raw_text) or (']' in raw_text and '[' not in raw_text):
        return False, "", "", "", "", "", "", "Tanda kurung siku tidak lengkap"

    # Ekstraksi Detail di mana pun posisinya
    match = re.search(r'\[(.*?)\]', raw_text)
    if match:
        detail = match.group(1).replace('[', '').replace(']', '').strip()
        text_clean = re.sub(r'\[.*?\]', '', raw_text).strip()
        # Bersihkan koma ganda berulang akibat penghapusan bracket
        text_clean = re.sub(r',\s*,+', ',', text_clean).strip(' ,')
    else:
        detail = "-"
        text_clean = raw_text.strip()

    # Membagi 4 kolom utama dari kanan: tipe, keterangan, satuan, jumlah
    parts = [p.strip() for p in text_clean.rsplit(',', 3)]
    if len(parts) != 4:
        return False, "", "", "", "", "", "", "Format salah. Gunakan: in/out, Kode Barang, Satuan, Jumlah"

    tipe_trx, keterangan, satuan, jumlah_mentah = parts
    tipe_upper = tipe_trx.upper()

    if tipe_upper not in ["IN", "OUT"]:
        return False, "", "", "", "", "", "", f"Tipe '{tipe_trx}' tidak valid. Gunakan 'in' atau 'out'"

    jumlah_final, rumus_asli = calculate_dimension(jumlah_mentah)
    return True, tipe_upper, keterangan, satuan, jumlah_final, detail, rumus_asli, ""
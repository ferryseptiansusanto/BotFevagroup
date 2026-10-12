import re
from utils.math_utils import calculate_dimension

def parse_item_input(raw_text: str) -> tuple[bool, str, str, str, str, str, str]:
    """
    Mengurai teks mentah menjadi komponen data barang.
    Return: (Sukses_Parsing, Keterangan, Satuan, Jumlah, Detail, Rumus_Asli, Pesan_Error)
    """
    # 1. Proteksi kurung siku yang tidak lengkap
    if ('[' in raw_text and ']' not in raw_text) or (']' in raw_text and '[' not in raw_text):
        return False, "", "", "", "", "", "Tanda kurung siku tidak lengkap"

    # 2. Ekstraksi Detail menggunakan RegEx
    match = re.search(r'\[(.*?)\]', raw_text)
    if match:
        detail = match.group(1).replace('[', '').replace(']', '').strip()
        text_clean = re.sub(r'\[.*?\]', '', raw_text).strip()
    else:
        detail = "-"
        text_clean = raw_text

    # 3. Pembelahan teks berdasarkan koma dari kanan
    parts = [p.strip() for p in text_clean.rsplit(',', 2)]
    if len(parts) != 3:
        return False, "", "", "", "", "", "Format kurang tepat atau kurang koma"

    keterangan, satuan, jumlah_mentah = parts

    # 4. Kalkulasi dimensi
    jumlah_final, rumus_asli = calculate_dimension(jumlah_mentah)

    return True, keterangan, satuan, jumlah_final, detail, rumus_asli, ""
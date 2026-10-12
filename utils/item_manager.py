import json
import os
from config.settings import ITEMS_FILE

def load_items() -> list:
    if not os.path.exists(ITEMS_FILE):
        # Otomatis membuat struktur awal jika file belum ada
        with open(ITEMS_FILE, "w", encoding="utf-8") as f:
            json.dump({"barang": []}, f, indent=2)
        return []
    try:
        with open(ITEMS_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("barang", [])
    except Exception:
        return []


def is_item_valid(nama_barang: str) -> bool:
    items = load_items()
    if not items:
        return False  # Bypass sementara jika database barang masih kosong sama sekali

    # Pengecekan case-insensitive (huruf besar/kecil diabaikan)
    valid_items = [item.lower().strip() for item in items]
    return nama_barang.strip().lower() in valid_items


def add_new_item(nama_barang: str) -> bool:
    items = load_items()
    if nama_barang.lower().strip() in [item.lower().strip() for item in items]:
        return False  # Barang sudah ada

    items.append(nama_barang.strip())
    with open(ITEMS_FILE, "w", encoding="utf-8") as f:
        json.dump({"barang": items}, f, indent=2)
    return True

def rename_item(old_name: str, new_name: str) -> tuple[bool, str]:
    items = load_items()
    old_name_clean = old_name.strip().lower()
    new_name_clean = new_name.strip()

    # Cari index barang yang akan diubah
    idx_to_rename = -1
    for i, item in enumerate(items):
        # Tambahkan .strip() agar aman dari spasi tersembunyi di database
        if item.strip().lower() == old_name_clean:
            idx_to_rename = i
            break

    if idx_to_rename == -1:
        return False, f"Barang '{old_name.strip()}' tidak ditemukan di database."

    # Validasi apakah nama baru sudah dipakai oleh barang lain
    if new_name_clean.lower() in [item.strip().lower() for item in items]:
        return False, f"Barang dengan nama '{new_name_clean}' sudah ada."

    items[idx_to_rename] = new_name_clean
    with open(ITEMS_FILE, "w", encoding="utf-8") as f:
        json.dump({"barang": items}, f, indent=2)
    return True, "Sukses"

def delete_item(item_name: str) -> tuple[bool, str]:
    items = load_items()
    item_name_clean = item_name.strip().lower()

    idx_to_delete = -1
    for i, item in enumerate(items):
        # Tambahkan .strip() agar aman dari spasi tersembunyi di database
        if item.strip().lower() == item_name_clean:
            idx_to_delete = i
            break

    if idx_to_delete == -1:
        return False, f"Barang '{item_name.strip()}' tidak ditemukan."

    deleted_item = items.pop(idx_to_delete)
    with open(ITEMS_FILE, "w", encoding="utf-8") as f:
        json.dump({"barang": items}, f, indent=2)
    return True, f"Barang '{deleted_item}' berhasil dihapus."

def reset_master_items() -> tuple[bool, str]:
    try:
        # Menimpa file dengan dictionary barang yang kosong
        with open(ITEMS_FILE, "w", encoding="utf-8") as f:
            json.dump({"barang": []}, f, indent=2)
        return True, "Master Data Barang berhasil dikosongkan secara keseluruhan."
    except Exception as e:
        return False, f"Terjadi kesalahan saat mereset Master Data: {e}"
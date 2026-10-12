from telegram import Update
from telegram.ext import ContextTypes
from utils.user_manager import require_role, Role, get_user_role
from utils.excel_manager import append_data, edit_data, delete_data
from utils.item_manager import is_item_valid
from utils.text_parser import parse_item_input  # <--- Impor modul parser baru
from utils.excel_manager import get_pivot_summary

@require_role(Role.USER_INPUT)
async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_text = " ".join(context.args)
    if not raw_text:
        pesan_bantuan = (
            "⚠️ Format salah!\n\n"
            "*Format:* `/tambah Barang, Satuan, Jumlah [Detail]`\n"
            "*Contoh:* `/tambah Semen Tonasa, Sak, 10 [Gudang A]`"
        )
        return await update.effective_message.reply_text(pesan_bantuan, parse_mode="Markdown")

    user = update.effective_user
    chat = update.effective_chat
    role_name = get_user_role(chat.id, user.id).name
    entries = [e.strip() for e in raw_text.split(';') if e.strip()]

    berhasil_list = []
    gagal = 0
    pesan_error = ""

    for entry in entries:
        # --- PANGGIL FUNGSI PARSER ---
        sukses_parse, keterangan, satuan, jumlah_final, detail, rumus_asli, err_msg = parse_item_input(entry)

        if not sukses_parse:
            gagal += 1
            pesan_error += f"\n- ❌ `{entry}` ({err_msg})"
            continue

        if not is_item_valid(keterangan):
            gagal += 1
            pesan_error += f"\n- ❌ `{entry}` (Barang '{keterangan}' tidak terdaftar)"
            continue

        sukses, row_id = await append_data(chat.id, user.id, user.username, user.full_name, role_name, keterangan,
                                           satuan, jumlah_final, detail)

        if sukses:
            teks_detail = f" | {detail}" if detail != "-" else ""
            teks_rumus = f" [dari {rumus_asli}]" if rumus_asli else ""
            berhasil_list.append(f"ID {row_id} : {keterangan} ({jumlah_final} {satuan}){teks_detail}{teks_rumus}")
        else:
            gagal += 1
            pesan_error += f"\n- ❌ `{entry}` (Gagal simpan ke Excel)"

    if berhasil_list:
        msg = f"✅ **Sukses menyimpan {len(berhasil_list)} data:**\n"
        for item in berhasil_list:
            msg += f"🔹 `{item}`\n"
    else:
        msg = "⚠️ **Tidak ada data yang berhasil disimpan.**"

    if gagal > 0:
        msg += f"\n⚠️ **Gagal:** {gagal} data ditolak.{pesan_error}"

    await update.effective_message.reply_text(msg, parse_mode="Markdown")


@require_role(Role.USER_INPUT)
async def edit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        return await update.effective_message.reply_text("Format: `/edit <baris> Barang, Satuan, Jumlah [Detail]`",
                                                         parse_mode="Markdown")

    try:
        row = int(context.args[0])
    except ValueError:
        return

    raw_text = " ".join(context.args[1:])

    # --- PANGGIL FUNGSI PARSER ---
    sukses_parse, keterangan, satuan, jumlah_final, detail, rumus_asli, err_msg = parse_item_input(raw_text)

    if not sukses_parse:
        return await update.effective_message.reply_text(f"⚠️ Gagal: {err_msg}", parse_mode="Markdown")

    if not is_item_valid(keterangan):
        return await update.effective_message.reply_text(
            f"⚠️ Gagal: Barang *{keterangan}* tidak terdaftar di Master Data.", parse_mode="Markdown")

    user_role = get_user_role(update.effective_chat.id, update.effective_user.id)
    require_same_day = (user_role == Role.USER_INPUT)

    sukses, pesan = await edit_data(update.effective_chat.id, row, keterangan, satuan, jumlah_final, detail,
                                    require_same_day)

    if sukses:
        teks_rumus = f" [dari {rumus_asli}]" if rumus_asli else ""
        teks_detail = f" | {detail}" if detail != "-" else ""
        msg = f"✅ Baris {row} berhasil diubah menjadi: {keterangan} ({jumlah_final} {satuan}){teks_detail}{teks_rumus}"
    else:
        msg = f"⛔ Gagal: {pesan}"

    await update.effective_message.reply_text(msg, parse_mode="Markdown")
@require_role(Role.USER_ADMIN)
async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        row = int(context.args[0])
    except:
        return await update.effective_message.reply_text("Format: `/hapus <baris>`", parse_mode="Markdown")

    sukses = await delete_data(update.effective_chat.id, row)
    msg = f"🗑️ Baris {row} dihapus." if sukses else "⚠️ Gagal hapus data."
    await update.effective_message.reply_text(msg)


@require_role(Role.VIEWER)
async def rekap_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    loading_msg = await update.effective_message.reply_text("⏳ Sedang menghitung rekapitulasi data...")

    sukses, hasil = await get_pivot_summary(chat.id)

    if not sukses:
        return await loading_msg.edit_text(f"⚠️ {hasil}")

    if not hasil:
        return await loading_msg.edit_text("📉 Belum ada data transaksi yang bisa direkap.")

    pesan = f"📊 *REKAPITULASI DATA: {chat.title}*\n"
    pesan += "============================\n\n"

    # Mengurutkan berdasarkan nama barang (abjad)
    for item_key in sorted(hasil.keys()):
        total = hasil[item_key]

        # Hilangkan angka .0 jika bilangan bulat murni (misal 280.0 jadi 280)
        total_str = f"{int(total):,}" if total.is_integer() else f"{total:,.2f}"

        pesan += f"📦 *{item_key}* : `{total_str}`\n"

    # Hapus pesan loading dan kirim hasil akhir
    await loading_msg.delete()
    await update.effective_message.reply_text(pesan.strip(), parse_mode="Markdown")
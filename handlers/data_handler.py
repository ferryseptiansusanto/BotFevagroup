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
            "*Format:* `/tambah in/out, Kode Barang, Satuan, Jumlah [Detail]`\n"
            "*Contoh:* `/tambah in, Semen Tonasa, Sak, 50 [Gudang A]`\n"
            "*Multi:* `/tambah in, Semen Tonasa, Sak, 10; out, Semen Tonasa, Sak, 5`"
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
        sukses_parse, tipe, keterangan, satuan, jumlah_final, detail, rumus_asli, err_msg = parse_item_input(entry)

        if not sukses_parse:
            gagal += 1
            pesan_error += f"\n- ❌ `{entry}` ({err_msg})"
            continue

        if not is_item_valid(keterangan):
            gagal += 1
            pesan_error += f"\n- ❌ `{entry}` (Barang '{keterangan}' tidak terdaftar)"
            continue

        sukses, row_id = await append_data(chat.id, user.id, user.username, user.full_name, role_name, tipe, keterangan,
                                           satuan, jumlah_final, detail)

        if sukses:
            tanda = "📥 IN" if tipe == "IN" else "📤 OUT"
            teks_detail = f" | {detail}" if detail != "-" else ""
            teks_rumus = f" [dari {rumus_asli}]" if rumus_asli else ""
            berhasil_list.append(f"ID {row_id} | {tanda} : {keterangan} ({jumlah_final} {satuan}){teks_detail}{teks_rumus}")
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
        return await update.effective_message.reply_text("Format: `/edit <ID> in/out, Kode Barang, Satuan, Jumlah [Detail]`", parse_mode="Markdown")

    try:
        row = int(context.args[0])
    except ValueError:
        return await update.effective_message.reply_text("ID baris harus berupa angka.")

    raw_text = " ".join(context.args[1:])

    # --- PANGGIL FUNGSI PARSER ---
    sukses_parse, tipe, keterangan, satuan, jumlah_final, detail, rumus_asli, err_msg = parse_item_input(raw_text)

    if not sukses_parse:
        return await update.effective_message.reply_text(f"⚠️ Gagal: {err_msg}", parse_mode="Markdown")

    if not is_item_valid(keterangan):
        return await update.effective_message.reply_text(
            f"⚠️ Gagal: Barang *{keterangan}* tidak terdaftar di Master Data.", parse_mode="Markdown")

    user_role = get_user_role(update.effective_chat.id, update.effective_user.id)
    require_same_day = (user_role == Role.USER_INPUT)

    sukses, pesan = await edit_data(update.effective_chat.id, row, tipe, keterangan, satuan, jumlah_final, detail,
                                    require_same_day)

    if sukses:
        tanda = "📥 IN" if tipe == "IN" else "📤 OUT"
        teks_rumus = f" [dari {rumus_asli}]" if rumus_asli else ""
        teks_detail = f" | {detail}" if detail != "-" else ""
        await update.effective_message.reply_text(f"✅ Baris ID {row} diubah: {tanda} {keterangan} ({jumlah_final} {satuan}){teks_detail}{teks_rumus}", parse_mode="Markdown")
    else:
        await update.effective_message.reply_text(f"⛔ Gagal: {pesan}", parse_mode="Markdown")

@require_role(Role.USER_ADMIN)
async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.effective_message.reply_text("Format: `/hapus <ID>`", parse_mode="Markdown")
    try:
        row = int(context.args[0])
    except ValueError:
        return await update.effective_message.reply_text("ID baris harus berupa angka.")

    if await delete_data(update.effective_chat.id, row):
        await update.effective_message.reply_text(f"🗑️ Baris ID {row} berhasil dihapus.", parse_mode="Markdown")
    else:
        await update.effective_message.reply_text("⚠️ Gagal menghapus baris.", parse_mode="Markdown")


@require_role(Role.VIEWER)
async def rekap_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    sukses, inventory = await get_pivot_summary(chat.id)

    if not sukses or not inventory:
        return await update.effective_message.reply_text("📉 Belum ada pergerakan stok barang.")

    pesan = f"📦 *REKAPITULASI STOK: {chat.title}*\n"
    pesan += "============================\n"

    for (ket, sat), qty in sorted(inventory.items()):
        total_in, total_out = qty["IN"], qty["OUT"]
        sisa = total_in - total_out

        def fmt(n): return f"{int(n):,}" if n.is_integer() else f"{n:,.2f}"

        pesan += f"\n🔹 *{ket}* ({sat})\n"
        pesan += f"   ├ Masuk  : `{fmt(total_in)}`\n"
        pesan += f"   ├ Keluar : `{fmt(total_out)}`\n"
        pesan += f"   └ *Saldo*  : *`{fmt(sisa)}`*\n"

    await update.effective_message.reply_text(pesan, parse_mode="Markdown")
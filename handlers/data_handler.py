from telegram import Update
from telegram.ext import ContextTypes
from utils.user_manager import require_role, Role, get_user_role
from utils.excel_manager import append_data, edit_data, delete_data
from utils.item_manager import is_item_valid


@require_role(Role.USER_INPUT)
async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_text = " ".join(context.args)
    if not raw_text:
        pesan_bantuan = (
            "⚠️ Format salah!\n\n"
            "*Single Input:* `/tambah Keterangan, Satuan, Jumlah`\n"
            "*Multiple Input:* `/tambah Ket1, Sat1, Jml1; Ket2, Sat2, Jml2`\n\n"
            "*Contoh:* `/tambah Pipa PVC, Batang, 10; Semen Tonasa, Sak, 5`"
        )
        return await update.effective_message.reply_text(pesan_bantuan, parse_mode="Markdown")

    user = update.effective_user
    chat = update.effective_chat
    role_name = get_user_role(chat.id, user.id).name

    # 1. Pisahkan menjadi beberapa baris data berdasarkan titik koma (;)
    entries = [e.strip() for e in raw_text.split(';') if e.strip()]

    berhasil = 0
    gagal = 0
    pesan_error = ""

    # 2. Proses setiap baris secara berurutan
    for entry in entries:
        # Gunakan rsplit(',', 2) memisahkan maksimal 2 koma dari kanan.
        # Ini mengamankan tanda koma yang tidak sengaja diketik di dalam Keterangan.
        parts = [p.strip() for p in entry.rsplit(',', 2)]

        if len(parts) != 3:
            gagal += 1
            pesan_error += f"\n- ❌ `{entry}` (Kurang tanda koma)"
            continue

        keterangan, satuan, jumlah = parts

        # --- TAMBAHAN BARU: Validasi Master Data ---
        if not is_item_valid(keterangan):
            gagal += 1
            pesan_error += f"\n- ❌ `{entry}` (Barang '{keterangan}' tidak terdaftar)"
            continue
        # -------------------------------------------

        sukses = await append_data(chat.id, user.id, user.username, user.full_name, role_name, keterangan, satuan,
                                   jumlah)

        if sukses:
            berhasil += 1
        else:
            gagal += 1
            pesan_error += f"\n- ❌ `{entry}` (Gagal menyimpan ke Excel)"

    # 3. Laporan hasil eksekusi
    msg = f"✅ **Sukses:** {berhasil} baris data tersimpan."
    if gagal > 0:
        msg += f"\n⚠️ **Gagal:** {gagal} data ditolak.{pesan_error}"

    await update.effective_message.reply_text(msg, parse_mode="Markdown")


@require_role(Role.USER_INPUT)
async def edit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        return await update.effective_message.reply_text("Format: `/edit <baris> <Keterangan>, <Satuan>, <Jumlah>`",
                                                         parse_mode="Markdown")

    try:
        row = int(context.args[0])
    except ValueError:
        return

    raw_text = " ".join(context.args[1:])

    # Sama seperti add, gunakan rsplit 2 kali dari kanan
    parts = [p.strip() for p in raw_text.rsplit(',', 2)]

    if len(parts) != 3:
        return await update.effective_message.reply_text("⚠️ Format salah! Gunakan koma: `/edit 2 Kabel NYM, Roll, 10`",
                                                         parse_mode="Markdown")

    keterangan, satuan, jumlah = parts
    user_role = get_user_role(update.effective_chat.id, update.effective_user.id)
    require_same_day = (user_role == Role.USER_INPUT)

    sukses, pesan = await edit_data(update.effective_chat.id, row, keterangan, satuan, jumlah, require_same_day)
    msg = f"✅ Baris {row} berhasil diubah." if sukses else f"⛔ Gagal: {pesan}"
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
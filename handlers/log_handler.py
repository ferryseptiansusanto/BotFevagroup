from telegram import Update
from telegram.ext import ContextTypes
from utils.user_manager import get_user_role
from utils.excel_manager import append_data

async def auto_log_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    # Pastikan pesan berasal dari grup dan berupa teks
    if not chat or chat.type not in ["group", "supergroup"]:
        return
    if not message or not message.text:
        return

    # Dapatkan role pengguna untuk dimasukkan ke kolom "User Level"
    role_name = get_user_role(chat.id, user.id).name

    # Proses simpan ke Excel secara asinkron (diabaikan jika grup belum di-setup)
    await append_data(
        chat_id=chat.id,
        user_id=user.id,
        username=user.username or "",
        full_name=user.full_name,
        level=role_name,
        keterangan=message.text,
        satuan="-",
        jumlah="-"
    )
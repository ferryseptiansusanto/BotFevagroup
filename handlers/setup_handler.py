from telegram import Update
from telegram.ext import ContextTypes
from utils.user_manager import require_role, Role
from utils.excel_manager import setup_excel

@require_role(Role.USER_ADMIN)
async def setup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type not in ["group", "supergroup"]:
        await update.effective_message.reply_text("Perintah ini khusus untuk grup.")
        return

    filepath = await setup_excel(chat.id, chat.title)
    await update.effective_message.reply_text(
        f"✅ **Grup Berhasil Diinisialisasi!**\n\n"
        f"📌 **Nama File:** `{filepath}`\n"
        f"File siap menampung data transaksi.",
        parse_mode="Markdown"
    )
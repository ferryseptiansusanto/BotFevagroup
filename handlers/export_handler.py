import os
from telegram import Update
from telegram.ext import ContextTypes
from utils.user_manager import require_role, Role
from utils.excel_manager import get_filepath

@require_role(Role.VIEWER)
async def getlogs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type not in ["group", "supergroup"]: return

    filepath = get_filepath(chat.id)
    if not filepath or not os.path.exists(filepath):
        return await update.effective_message.reply_text("⚠️ Grup belum disetup.")

    with open(filepath, "rb") as f:
        await context.bot.send_document(
            chat_id=chat.id,
            document=f,
            caption=f"📊 Log: *{chat.title}*",
            parse_mode="Markdown"
        )
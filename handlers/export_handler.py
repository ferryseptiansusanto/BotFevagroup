import os
from telegram import Update
from telegram.ext import ContextTypes
from utils.user_manager import require_role, Role
from utils.excel_manager import generate_export_file  # Pastikan ini diimpor


@require_role(Role.VIEWER)
async def get_logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    loading_msg = await update.effective_message.reply_text("⏳ Sedang menyiapkan file Excel dan Rekapitulasi...")

    # Memanggil sistem Export yang membuat salinan file + Sheet Rekap
    sukses, result = await generate_export_file(chat.id)

    if not sukses:
        return await loading_msg.edit_text(
            f"⚠️ *GAGAL MENYIAPKAN FILE EXCEL*\n\n"
            f"Penyebab: `{result}`"
            , parse_mode="Markdown"
        )

    export_path = result  # result berisi lokasi file sementara (Export)

    try:
        # Kirim file temporary tersebut ke Telegram
        with open(export_path, 'rb') as doc:
            await context.bot.send_document(
                chat_id=chat.id,
                document=doc,
                filename=os.path.basename(export_path),
                caption="📊 *File Log & Rekapitulasi Otomatis*\nSilakan periksa sheet 'Rekap' di dalam file ini.",
                parse_mode="Markdown"
            )
        await loading_msg.delete()
    except Exception as e:
        await loading_msg.edit_text(f"⚠️ Gagal mengirim file: {e}")
    finally:
        # PEMBERSIHAN OTOMATIS: Hapus file salinan setelah dikirim
        if os.path.exists(export_path):
            os.remove(export_path)
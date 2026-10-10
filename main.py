import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from config.settings import BOT_TOKEN
from handlers.setup_handler import setup_command

from handlers.data_handler import add_command, edit_command, delete_command
from handlers.export_handler import getlogs_command
from handlers.log_handler import auto_log_message
from handlers.admin_mgmt_handler import (
    set_role_command, check_role_command, get_id_command,
    add_item_command, edit_item_command, delete_item_command, list_item_command,
    help_command
)

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Registrasi Command
    app.add_handler(CommandHandler("setup", setup_command))
    app.add_handler(CommandHandler("setrole", set_role_command))
    app.add_handler(CommandHandler("cekakses", check_role_command))
    app.add_handler(CommandHandler("tambah", add_command))
    app.add_handler(CommandHandler("edit", edit_command))
    app.add_handler(CommandHandler("hapus", delete_command))
    app.add_handler(CommandHandler("getlogs", getlogs_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), auto_log_message))
    app.add_handler(CommandHandler("id", get_id_command))
    app.add_handler(CommandHandler("tambahbarang", add_item_command))
    app.add_handler(CommandHandler("editbarang", edit_item_command))
    app.add_handler(CommandHandler("hapusbarang", delete_item_command))
    app.add_handler(CommandHandler("listbarang", list_item_command))

    # Daftarkan command help dan menu (mengarah ke fungsi yang sama)
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("menu", help_command))

    logging.info("BotFevagroup Asynchronous berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()
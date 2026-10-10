import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN belum disetel di file .env")

DATA_DIR = "data_logs"
USERS_FILE = "database/users.json"
GROUP_REGISTRY_FILE = "database/group_registry.json"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs("database", exist_ok=True)
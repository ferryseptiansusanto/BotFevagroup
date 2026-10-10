import json
import os
from enum import IntEnum
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from config.settings import USERS_FILE


class Role(IntEnum):
    VIEWER = 1  # Member: Hanya lihat/ekspor data (Default)
    USER_INPUT = 2  # Member Aktif: Input & Edit hari yang sama
    USER_ADMIN = 3  # Group Admin: Input, Edit bebas, Hapus data, Setup
    SUPERADMIN = 4  # Superadmin: Hak penuh & Manajemen User


def load_user_db() -> dict:
    default_db = {"superadmins": [], "groups": {}}
    if not os.path.exists(USERS_FILE):
        return default_db
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            db = json.load(f)
            # Memperbaiki struktur JSON secara otomatis jika ada key yang terhapus manual
            if "superadmins" not in db:
                db["superadmins"] = []
            if "groups" not in db:
                db["groups"] = {}
            return db
    except Exception:
        return default_db


def save_user_db(data: dict):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_user_role(chat_id: int, user_id: int) -> Role:
    db = load_user_db()

    if user_id in db.get("superadmins", []):
        return Role.SUPERADMIN

    group_roles = db.get("groups", {}).get(str(chat_id), {})
    if user_id in group_roles.get("user_admins", []):
        return Role.USER_ADMIN
    if user_id in group_roles.get("user_inputs", []):
        return Role.USER_INPUT

    return Role.VIEWER


def require_role(min_role: Role):
    """Decorator membatasi akses berdasarkan hierarki level user."""

    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            if not update.effective_chat or not update.effective_user:
                return

            chat_id = update.effective_chat.id
            user_id = update.effective_user.id
            current_role = get_user_role(chat_id, user_id)

            if current_role < min_role:
                await update.effective_message.reply_text(
                    f"⛔ Akses ditolak. Anda membutuhkan hak akses minimal: *{min_role.name}*.",
                    parse_mode="Markdown"
                )
                return
            return await func(update, context, *args, **kwargs)

        return wrapper

    return decorator

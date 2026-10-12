from telegram import Update
from telegram.ext import ContextTypes
from utils.user_manager import require_role, Role, load_user_db, save_user_db, get_user_role
from utils.item_manager import add_new_item, rename_item, delete_item, load_items, reset_master_items
from utils.excel_manager import reset_excel_data, get_filepath
import os

@require_role(Role.SUPERADMIN)
async def set_role_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type not in ["group", "supergroup"]: return

    if len(context.args) < 2:
        await update.effective_message.reply_text("Format: `/setrole <user_id> <user_admin|user_input|viewer>`", parse_mode="Markdown")
        return

    try:
        user_id = int(context.args[0])
        role = context.args[1].lower()
    except ValueError:
        return await update.effective_message.reply_text("User ID harus angka.")

    if role not in ["user_admin", "user_input", "viewer"]:
        return await update.effective_message.reply_text("Role tidak valid.")

    db = load_user_db()
    chat_str = str(chat.id)
    if chat_str not in db["groups"]: db["groups"][chat_str] = {"user_admins": [], "user_inputs": []}

    # Bersihkan ID dari role lama
    for key in ["user_admins", "user_inputs"]:
        if user_id in db["groups"][chat_str][key]:
            db["groups"][chat_str][key].remove(user_id)

    # Set role baru
    if role == "user_admin": db["groups"][chat_str]["user_admins"].append(user_id)
    elif role == "user_input": db["groups"][chat_str]["user_inputs"].append(user_id)

    save_user_db(db)
    await update.effective_message.reply_text(f"✅ User {user_id} diset sebagai {role.upper()}")


async def check_role_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type not in ["group", "supergroup"]:
        await update.effective_message.reply_text("Perintah ini hanya dapat dijalankan di dalam grup.")
        return

    # Ambil role user di grup tersebut
    current_role = get_user_role(chat.id, user.id)

    # Menggunakan HTML agar kebal terhadap karakter khusus (seperti _ atau *) pada nama pengguna
    pesan = (
        f"👤 <b>Informasi Akses Anda</b>\n\n"
        f"🔹 <b>Nama:</b> {user.full_name}\n"
        f"🔹 <b>ID Telegram:</b> <code>{user.id}</code>\n"
        f"🔹 <b>Level Akses:</b> <b>{current_role.name}</b>\n"
    )

    try:
        await update.effective_message.reply_text(pesan, parse_mode="HTML")
    except Exception as e:
        print(f"Gagal mengirim pesan /cekakses: {e}")

async def get_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Jika Anda membalas pesan orang lain di grup
    if update.effective_message.reply_to_message:
        target_user = update.effective_message.reply_to_message.from_user
        pesan = f"👤 ID {target_user.full_name}: `{target_user.id}`"
    else:
        # Jika Anda hanya mengetik /id tanpa membalas pesan siapa pun
        user = update.effective_user
        pesan = f"👤 ID Anda ({user.full_name}): `{user.id}`"

    await update.effective_message.reply_text(pesan, parse_mode="Markdown")


@require_role(Role.USER_ADMIN)
async def add_item_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_text = " ".join(context.args)
    if not raw_text:
        pesan_bantuan = (
            "⚠️ Format salah!\n\n"
            "*Single Input:* `/addbarang Nama Barang`\n"
            "*Multiple Input:* `/addbarang Barang1; Barang2; Barang3`\n\n"
            "*Contoh:* `/addbarang Aggr A; Aggr B; ACBC; ACWC`"
        )
        return await update.effective_message.reply_text(pesan_bantuan, parse_mode="Markdown")

    # Memisahkan input berdasarkan titik koma (;) dan mengabaikan spasi kosong
    items_to_add = [item.strip() for item in raw_text.split(';') if item.strip()]

    berhasil = []
    gagal = []

    # Proses setiap barang secara berurutan
    for nama_barang in items_to_add:
        sukses = add_new_item(nama_barang)
        if sukses:
            berhasil.append(nama_barang)
        else:
            gagal.append(nama_barang)

    # Menyusun pesan laporan eksekusi
    msg = ""
    if berhasil:
        msg += f"✅ *Berhasil ditambahkan:* {', '.join(berhasil)}\n"
    if gagal:
        msg += f"⚠️ *Sudah ada di database:* {', '.join(gagal)}"

    await update.effective_message.reply_text(msg.strip(), parse_mode="Markdown")

@require_role(Role.USER_ADMIN)
async def edit_item_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_text = " ".join(context.args)
    parts = [p.strip() for p in raw_text.split('|')]

    if len(parts) != 2:
        pesan = (
            "⚠️ Format salah!\n\n"
            "Gunakan garis vertikal `|` sebagai pemisah.\n"
            "*Format:* `/editbarang Nama Lama | Nama Baru`\n"
            "*Contoh:* `/editbarang Semen Padang | Semen Tonasa`"
        )
        return await update.effective_message.reply_text(pesan, parse_mode="Markdown")

    old_name, new_name = parts
    sukses, pesan = rename_item(old_name, new_name)

    if sukses:
        # PERBAIKAN: Menutup tanda * pada old_name dan new_name
        await update.effective_message.reply_text(
            f"✅ Berhasil mengubah *{old_name}* menjadi *{new_name}* di Master Data.",
            parse_mode="Markdown"
        )
    else:
        await update.effective_message.reply_text(f"⛔ Gagal: {pesan}")

@require_role(Role.USER_ADMIN)
async def delete_item_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nama_barang = " ".join(context.args)
    if not nama_barang:
        return await update.effective_message.reply_text("Format: `/hapusbarang <Nama Barang>`", parse_mode="Markdown")

    sukses, pesan = delete_item(nama_barang)
    if sukses:
        await update.effective_message.reply_text(f"🗑️ {pesan}")
    else:
        await update.effective_message.reply_text(f"⛔ Gagal: {pesan}")


@require_role(Role.VIEWER)  # Mengizinkan semua orang melihat daftar barang
async def list_item_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    items = load_items()

    if not items:
        await update.effective_message.reply_text("📦 *Master Data Barang* saat ini masih kosong.",
                                                  parse_mode="Markdown")
        return

    # Mengurutkan barang berdasarkan abjad (A-Z) agar rapi saat dibaca
    items.sort(key=str.lower)

    # Menyusun pesan daftar barang
    pesan = "📦 *Daftar Master Data Barang:*\n\n"
    for i, item in enumerate(items, start=1):
        pesan += f"{i}. {item}\n"

    pesan += "\n💡 _Gunakan perintah /tambahbarang, /editbarang atau /hapusbarang dengan nama barang di atas._"

    await update.effective_message.reply_text(pesan, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pesan = (
        "🤖 <b>Menu Bantuan BotFevagroup</b> 🤖\n"
        "Berikut adalah daftar perintah berdasarkan Hak Akses:\n\n"

        "🟢 <b>UMUM (Semua Anggota / Viewer)</b>\n"
        "• <code>/help</code> atau <code>/menu</code> : Menampilkan pesan ini\n"
        "• <code>/cekakses</code> : Mengetahui level akses Anda saat ini\n"
        "• <code>/id</code> : Melihat ID Telegram (Ketik langsung atau reply pesan orang)\n"
        "• <code>/listbarang</code> : Melihat daftar lengkap Master Data Barang\n"
        "• <code>/getlogs</code> : Mengunduh file Excel laporan grup ini\n\n"
        "• <code>/rekap</code> : Merekap seluruh aktivitas berdasar nama barang dan satuan lalu menampilkan hasil rekap digrup ini\n\n"
        "🟡 <b>KONTRIBUTOR (User Input)</b>\n"
        "• <code>/tambah</code> : Memasukkan data ke Excel.\n"
        "  <i>Format: /tambah Keterangan,Sat, Jml, (Detail)</i> (Gunakan <code>;</code> untuk banyak input sekaligus)\n"
        "• <code>/edit</code> : Mengubah data di baris tertentu.\n"
        "  <i>Format: /edit &lt;baris&gt; Keterangan, (Detail), Sat, Jml</i>\n\n"

        "🟠 <b>ADMIN GRUP (User Admin)</b>\n"
        "• <code>/setup</code> : Inisialisasi grup dan membuat file Excel baru\n"
        "• <code>/hapus</code> : Menghapus baris data di Excel (<i>/hapus &lt;baris&gt;</i>)\n"
        "• <code>/addbarang</code> : Menambah barang ke Master Data (Gunakan <code>;</code> untuk banyak input)\n"
        "• <code>/editbarang</code> : Mengubah nama barang (<i>/editbarang Lama | Baru</i>)\n"
        "• <code>/hapusbarang</code> : Menghapus Master Barang (<i>/hapusbarang Nama</i>)\n\n"

        "🔴 <b>SUPERADMIN</b>\n"
        "• <code>/setrole</code> : Mengubah hak akses pengguna.\n"
        "  <i>Format: /setrole &lt;User_ID&gt; &lt;user_admin|user_input|viewer&gt;</i>"
        "• <code>/resetdatabase</code> : Menghapus data.\n"
        "  <i>Format: /resetdatabase &lt;excel&gt; &lt;excel|master&gt;</i>"
    )

    # Menggunakan HTML dan menerjemahkan simbol < > menjadi &lt; dan &gt;
    await update.effective_message.reply_text(pesan, parse_mode="HTML")


@require_role(Role.SUPERADMIN)
async def reset_database_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    args = context.args

    # Proteksi: Minta konfirmasi jika dipanggil tanpa argumen yang jelas
    if not args or args[0].lower() not in ["excel", "master"]:
        pesan = (
            "⚠️ *PERINGATAN: TINDAKAN BERBAHAYA (SUPERADMIN ONLY)* ⚠️\n\n"
            "Perintah ini akan menghapus data secara permanen. "
            "Silakan pilih database mana yang ingin direset:\n\n"
            "1. `/resetdatabase excel` - Menghapus semua riwayat input di Excel grup ini (Header dipertahankan).\n"
            "2. `/resetdatabase master` - Menghapus SEMUA daftar Master Data Barang."
        )
        return await update.effective_message.reply_text(pesan, parse_mode="Markdown")

    target = args[0].lower()

    if target == "excel":
        sukses, pesan = await reset_excel_data(chat.id)
        await update.effective_message.reply_text(f"📊 *Reset Excel Grup:*\n{pesan}", parse_mode="Markdown")

    elif target == "master":
        sukses, pesan = reset_master_items()
        await update.effective_message.reply_text(f"📦 *Reset Master Barang:*\n{pesan}", parse_mode="Markdown")



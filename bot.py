import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ===== AMBIL DARI ENVIRONMENT VARIABLES =====
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
AGNES_API_KEY = os.getenv("AGNES_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "downloads")

# Buat direktori downloads
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== FUNGSI MENU =====
def get_main_menu():
    """Menu utama bot"""
    keyboard = [
        [
            InlineKeyboardButton("📷 Image-to-Video", callback_data="image_to_video"),
            InlineKeyboardButton("🎞️ Text-to-Video", callback_data="text_to_video"),
        ],
        [
            InlineKeyboardButton("✨ Prompt Enhancer", callback_data="prompt_enhancer"),
            InlineKeyboardButton("🎯 Pilih Model", callback_data="choose_model"),
        ],
        [
            InlineKeyboardButton("❓ Bantuan", callback_data="help"),
            InlineKeyboardButton("⚙️ Pengaturan", callback_data="settings"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_model_menu():
    """Menu pilihan model AI"""
    keyboard = [
        [
            InlineKeyboardButton("🤖 Agnes-Video-2.5 (Gratis)", callback_data="model_agnes"),
            InlineKeyboardButton("🌱 Seedance 2.0 (Kredit)", callback_data="model_seedance"),
        ],
        [
            InlineKeyboardButton("⭐ Veo 3.1 (Berbayar)", callback_data="model_veo"),
        ],
        [
            InlineKeyboardButton("🔙 Kembali", callback_data="back_to_main"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_duration_menu():
    """Menu pilihan durasi video"""
    keyboard = [
        [
            InlineKeyboardButton("5 detik", callback_data="duration_5"),
            InlineKeyboardButton("10 detik", callback_data="duration_10"),
            InlineKeyboardButton("15 detik", callback_data="duration_15"),
        ],
        [
            InlineKeyboardButton("🔙 Kembali", callback_data="back_to_main"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_settings_menu():
    """Menu pengaturan"""
    keyboard = [
        [
            InlineKeyboardButton("🎬 Resolusi", callback_data="set_resolution"),
            InlineKeyboardButton("⏱️ Durasi Default", callback_data="set_duration"),
        ],
        [
            InlineKeyboardButton("📐 Aspect Ratio", callback_data="set_aspect"),
        ],
        [
            InlineKeyboardButton("🔙 Kembali", callback_data="back_to_main"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

# ===== HANDLER COMMAND =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk perintah /start"""
    welcome_text = (
        "🎬 **Selamat Datang di AI Video Creator Bot!**\n\n"
        "Saya bisa membantu kamu membuat video dari gambar dan prompt dengan bantuan AI.\n\n"
        "📌 **Cara Penggunaan:**\n"
        "1. Upload gambar (opsional)\n"
        "2. Tulis prompt atau deskripsi video\n"
        "3. Pilih model AI dan durasi\n"
        "4. Tunggu proses generasi (1-3 menit)\n"
        "5. Video akan dikirim otomatis ke chat ini\n\n"
        "🔹 **Contoh Prompt:**\n"
        "\"Buat video pendek produk skincare dengan gerakan kamera slow-motion dan latar putih bersih\"\n\n"
        "⚡ **Fitur:**\n"
        "• 📷 Image-to-Video (dari gambar)\n"
        "• 🎞️ Text-to-Video (tanpa gambar)\n"
        "• ✨ Prompt Enhancer (bantu bikin prompt lebih baik)\n"
        "• 🎯 Multi Model (Agnes, Veo, Seedance)\n\n"
        "**Pilih menu di bawah:**"
    )
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_menu(),
        parse_mode="Markdown",
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk perintah /help"""
    help_text = (
        "❓ **Bantuan & FAQ**\n\n"
        "📖 **Panduan Singkat:**\n"
        "1. Pilih menu yang diinginkan\n"
        "2. Ikuti instruksi (kirim gambar/prompt)\n"
        "3. Tunggu proses (1-3 menit)\n"
        "4. Video akan dikirim otomatis\n\n"
        "❓ **Pertanyaan Umum:**\n"
        "Q: Berapa durasi video maksimal?\n"
        "A: 5-15 detik (tergantung model)\n\n"
        "Q: Apakah ada biaya?\n"
        "A: Agnes dan Seedance gratis (dengan kuota harian)\n\n"
        "Q: Bisa upload lebih dari 1 gambar?\n"
        "A: Bisa! Kirimkan beberapa gambar sekaligus.\n\n"
        "Q: Bagaimana jika hasil tidak sesuai?\n"
        "A: Gunakan Prompt Enhancer untuk hasil lebih baik.\n\n"
        "📞 **Butuh bantuan?** Hubungi @seeshoopsolution"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

# ===== HANDLER CALLBACK =====
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk semua tombol inline"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    # ===== MENU UTAMA =====
    if data == "back_to_main":
        await query.edit_message_text(
            "🏠 **Menu Utama**\n\nPilih menu di bawah:",
            reply_markup=get_main_menu(),
            parse_mode="Markdown",
        )
    
    elif data == "image_to_video":
        text = (
            "📷 **Image-to-Video**\n\n"
            "Kirimkan **gambar** + **prompt** untuk membuat video.\n\n"
            "📌 **Langkah:**\n"
            "1. Upload gambar (bisa lebih dari 1)\n"
            "2. Tulis prompt (atau biarkan AI yang membuat)\n"
            "3. Pilih durasi (5-10-15 detik)\n"
            "4. Tunggu video jadi\n\n"
            "🖼️ **Contoh Gambar:**\n"
            "Foto produk, foto model, atau ilustrasi.\n\n"
            "✏️ **Contoh Prompt:**\n"
            "\"Buat video animasi dari gambar ini dengan gerakan kamera zoom in pelan, latar gradasi biru\"\n\n"
            "**Kirim gambar + prompt sekarang:**"
        )
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Kembali", callback_data="back_to_main")]
            ]),
            parse_mode="Markdown",
        )
        context.user_data['mode'] = 'image_to_video'
    
    elif data == "text_to_video":
        text = (
            "🎞️ **Text-to-Video**\n\n"
            "Buat video dari teks tanpa gambar.\n\n"
            "📌 **Langkah:**\n"
            "1. Tulis deskripsi video yang kamu inginkan\n"
            "2. Pilih gaya visual (cinematic, anime, realistis)\n"
            "3. Pilih durasi (5-10-15 detik)\n"
            "4. Tunggu video jadi\n\n"
            "✏️ **Contoh Prompt:**\n"
            "\"Seorang wanita berjalan di taman bunga matahari saat matahari terbenam, gaya cinematic, slow motion\"\n\n"
            "**Kirim prompt kamu:**"
        )
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Kembali", callback_data="back_to_main")]
            ]),
            parse_mode="Markdown",
        )
        context.user_data['mode'] = 'text_to_video'
    
    elif data == "prompt_enhancer":
        text = (
            "✨ **Prompt Enhancer**\n\n"
            "Kirimkan prompt video yang kamu miliki, dan AI akan menyempurnakannya menjadi lebih detail dan profesional.\n\n"
            "📝 **Contoh Input:**\n"
            "\"Produk skincare di meja putih\"\n\n"
            "📤 **Contoh Output:**\n"
            "\"9:16 vertical product close-up of a skincare bottle on a clean white podium that slowly rotates as light moves across the label, minimal studio background, premium ecommerce lighting, sharp focus, no extra text, no logo distortion\"\n\n"
            "**Kirim prompt kamu sekarang:**"
        )
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Kembali", callback_data="back_to_main")]
            ]),
            parse_mode="Markdown",
        )
        context.user_data['mode'] = 'prompt_enhancer'
    
    elif data == "choose_model":
        await query.edit_message_text(
            "🎯 **Pilih Model AI untuk Video**\n\n"
            "Pilih model AI yang ingin kamu gunakan:\n\n"
            "1. **Agnes-Video-2.5** (Gratis, 5-15 detik)\n"
            "   ✅ Stabil, cocok untuk produk\n"
            "   ✅ Support image-to-video\n"
            "   ⏱️ Durasi: 5-15 detik\n\n"
            "2. **Seedance 2.0** (Kredit harian)\n"
            "   ✅ Kualitas cinematic\n"
            "   ✅ Bisa 1080p\n"
            "   ⏱️ Durasi: 5-12 detik\n"
            "   💰 25 kredit/hari gratis\n\n"
            "3. **OpenRouter (Veo 3.1)** (Berbayar)\n"
            "   ✅ Kualitas terbaik\n"
            "   ✅ 4K resolution\n"
            "   ⏱️ Durasi: 5-10 detik\n"
            "   💰 $0.10/detik\n\n"
            "**Pilih model:**",
            reply_markup=get_model_menu(),
            parse_mode="Markdown",
        )
    
    elif data == "help":
        await query.edit_message_text(
            "❓ **Bantuan & FAQ**\n\n"
            "📖 **Panduan Singkat:**\n"
            "1. Pilih menu yang diinginkan\n"
            "2. Ikuti instruksi (kirim gambar/prompt)\n"
            "3. Tunggu proses (1-3 menit)\n"
            "4. Video akan dikirim otomatis\n\n"
            "❓ **Pertanyaan Umum:**\n"
            "Q: Berapa durasi video maksimal?\n"
            "A: 5-15 detik (tergantung model)\n\n"
            "Q: Apakah ada biaya?\n"
            "A: Agnes dan Seedance gratis (dengan kuota harian)\n\n"
            "Q: Bisa upload lebih dari 1 gambar?\n"
            "A: Bisa! Kirimkan beberapa gambar sekaligus.\n\n"
            "Q: Bagaimana jika hasil tidak sesuai?\n"
            "A: Gunakan Prompt Enhancer untuk hasil lebih baik.\n\n"
            "📞 **Butuh bantuan?** Hubungi @seeshoopsolution",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Kembali", callback_data="back_to_main")]
            ]),
            parse_mode="Markdown",
        )
    
    elif data == "settings":
        await query.edit_message_text(
            "⚙️ **Pengaturan**\n\n"
            "Pilih preferensi kamu:",
            reply_markup=get_settings_menu(),
            parse_mode="Markdown",
        )
    
    elif data.startswith("model_"):
        model = data.replace("model_", "")
        model_names = {
            "agnes": "Agnes-Video-2.5 (Gratis)",
            "seedance": "Seedance 2.0 (Kredit Harian)",
            "veo": "Veo 3.1 (Berbayar)",
        }
        context.user_data['model'] = model
        await query.edit_message_text(
            f"✅ Model dipilih: **{model_names.get(model, model)}**\n\n"
            "Sekarang pilih durasi video yang diinginkan:",
            reply_markup=get_duration_menu(),
            parse_mode="Markdown",
        )
    
    elif data.startswith("duration_"):
        duration = int(data.replace("duration_", ""))
        context.user_data['duration'] = duration
        await query.edit_message_text(
            f"✅ Durasi dipilih: **{duration} detik**\n\n"
            "📤 **Sekarang kirimkan gambar dan/atau prompt kamu!**\n\n"
            f"Model: {context.user_data.get('model', 'Belum dipilih')}\n"
            f"Durasi: {duration} detik",
            parse_mode="Markdown",
        )
    
    elif data in ["set_resolution", "set_duration", "set_aspect"]:
        await query.edit_message_text(
            f"⚙️ **Fitur ini sedang dalam pengembangan.**\n\n"
            "Untuk saat ini, resolusi default: **1080p**, Aspect Ratio: **9:16 (Vertical)**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Kembali", callback_data="back_to_main")]
            ]),
            parse_mode="Markdown",
        )

# ===== HANDLER PESAN =====
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk semua pesan (teks, foto, dokumen)"""
    user_id = update.effective_user.id
    mode = context.user_data.get('mode', '')
    
    # Cek apakah user sedang dalam mode tertentu
    if mode == 'image_to_video':
        # Proses gambar + prompt
        caption = update.message.caption or ""
        photos = update.message.photo
        
        if photos:
            # Ambil foto terbesar
            photo = photos[-1]
            file = await photo.get_file()
            file_path = os.path.join(DOWNLOAD_DIR, f"user_{user_id}_input.jpg")
            await file.download_to_drive(file_path)
            
            await update.message.reply_text(
                f"📥 Gambar diterima! Sekarang kirimkan prompt atau deskripsi video yang kamu inginkan.\n\n"
                f"📝 Prompt saat ini: {caption[:100] if caption else '(kosong)'}"
            )
            context.user_data['image_path'] = file_path
            context.user_data['prompt'] = caption
            
        elif caption and not photos:
            # Hanya prompt tanpa gambar
            context.user_data['prompt'] = caption
            await update.message.reply_text(
                "📝 Prompt diterima!\n\n"
                "Sekarang pilih model dan durasi untuk memulai generasi video.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎯 Pilih Model", callback_data="choose_model")]
                ])
            )
        else:
            await update.message.reply_text(
                "❌ Kirimkan **gambar** (foto) dan **prompt** (caption) untuk memulai.\n\n"
                "Contoh: Upload foto produk + tulis 'Buat video animasi dari gambar ini'"
            )
    
    else:
        # Tampilkan menu utama jika tidak dalam mode tertentu
        await update.message.reply_text(
            "🏠 **Menu Utama**\n\n"
            "Pilih menu di bawah untuk memulai:",
            reply_markup=get_main_menu(),
            parse_mode="Markdown",
        )

# ===== MAIN =====
def main():
    """Main function untuk menjalankan bot"""
    # Validasi TELEGRAM_TOKEN
    if not TELEGRAM_TOKEN:
        logger.error("❌ TELEGRAM_TOKEN tidak ditemukan! Set di Environment Variables Railway.")
        return
    
    # Inisialisasi aplikasi
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Daftarkan handler
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.ALL, handle_message))
    
    # Jalankan bot
    logger.info("🤖 Bot AI Video berjalan...")
    application.run_polling()

if __name__ == "__main__":
    main()

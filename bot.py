import os
import logging
import aiohttp
import asyncio
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

# ===== FUNGSI GENERATE VIDEO DENGAN AGNES AI =====
async def generate_video_with_agnes(prompt: str, image_path: str = None, duration: int = 5, model: str = "agnes") -> str:
    """Generate video menggunakan Agnes AI API"""
    
    API_URL = "https://apihub.agnes-ai.com/v1/video"
    
    headers = {
        "Authorization": f"Bearer {AGNES_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "agnes-video-2.5-preview",
        "prompt": prompt,
        "duration": duration,
        "resolution": "720p"
    }
    
    # Jika ada gambar, upload ke Agnes
    if image_path and os.path.exists(image_path):
        upload_url = "https://apihub.agnes-ai.com/v1/upload"
        try:
            async with aiohttp.ClientSession() as session:
                with open(image_path, 'rb') as f:
                    form_data = aiohttp.FormData()
                    form_data.add_field('file', f, filename='image.jpg')
                    async with session.post(upload_url, headers={"Authorization": f"Bearer {AGNES_API_KEY}"}, data=form_data) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            image_url = data.get('url')
                            if image_url:
                                payload['image'] = image_url
                                logger.info(f"Upload gambar berhasil: {image_url}")
                            else:
                                logger.warning(f"Upload gambar berhasil tapi tidak ada URL: {data}")
                        else:
                            error_text = await resp.text()
                            logger.warning(f"Upload gambar gagal: {resp.status} - {error_text}")
        except Exception as e:
            logger.error(f"Error upload gambar: {str(e)}")
    
    # Panggil API generate video
    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, headers=headers, json=payload) as response:
            if response.status == 200:
                result = await response.json()
                task_id = result.get('task_id')
                
                if not task_id:
                    logger.error(f"No task_id in response: {result}")
                    return None
                
                # Polling status
                status_url = f"https://apihub.agnes-ai.com/v1/video/{task_id}"
                for _ in range(60):  # 60x polling, 3 detik interval = 3 menit
                    await asyncio.sleep(3)
                    try:
                        async with session.get(status_url, headers=headers) as status_resp:
                            if status_resp.status == 200:
                                status_data = await status_resp.json()
                                status = status_data.get('status')
                                if status == 'completed':
                                    video_url = status_data.get('urls', [])
                                    if video_url and isinstance(video_url, list):
                                        return video_url[0]
                                    elif status_data.get('url'):
                                        return status_data.get('url')
                                elif status == 'failed':
                                    error_msg = status_data.get('error', 'Unknown error')
                                    raise Exception(f"Generasi video gagal: {error_msg}")
                    except Exception as e:
                        logger.error(f"Error polling status: {str(e)}")
                        await asyncio.sleep(3)
                        continue
                
                raise Exception("Timeout: Video tidak selesai dalam 3 menit")
            else:
                error_text = await response.text()
                logger.error(f"API error: {response.status} - {error_text}")
                return None

async def download_video(url: str, path: str):
    """Download video dari URL"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                with open(path, 'wb') as f:
                    while True:
                        chunk = await response.content.read(1024)
                        if not chunk:
                            break
                        f.write(chunk)
            else:
                raise Exception(f"Download gagal: {response.status}")

# ===== FUNGSI MENU =====
def get_main_menu():
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
    keyboard = [
        [
            InlineKeyboardButton("🤖 Agnes-Video-2.5 (Gratis)", callback_data="model_agnes"),
            InlineKeyboardButton("🌱 Seedance 2.0 (Kredit)", callback_data="model_seedance"),
        ],
        [
            InlineKeyboardButton("🔙 Kembali", callback_data="back_to_main"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_duration_menu():
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
    welcome_text = (
        "🎬 **Selamat Datang di AI Video Creator Bot!**\n\n"
        "Saya bisa membantu kamu membuat video dari gambar dan prompt dengan bantuan AI.\n\n"
        "📌 **Cara Penggunaan:**\n"
        "1. Kirim **gambar + caption** (prompt) dalam SATU pesan\n"
        "2. Atau kirim prompt tanpa gambar (text-to-video)\n"
        "3. Pilih model AI dan durasi\n"
        "4. Tunggu proses generasi (1-3 menit)\n"
        "5. Video akan dikirim otomatis\n\n"
        "📝 **Contoh:**\n"
        "Upload foto produk + tulis 'Buat video animasi slow motion dengan latar putih'\n\n"
        "**Pilih menu di bawah:**"
    )
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_menu(),
        parse_mode="Markdown",
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "❓ **Bantuan & FAQ**\n\n"
        "📖 **Panduan Singkat:**\n"
        "1. Kirim gambar + caption dalam satu pesan\n"
        "2. Atau kirim prompt tanpa gambar\n"
        "3. Pilih model & durasi\n"
        "4. Tunggu video jadi (1-3 menit)\n\n"
        "❓ **Pertanyaan Umum:**\n"
        "Q: Berapa durasi video maksimal?\n"
        "A: 5-15 detik (tergantung model)\n\n"
        "Q: Apakah ada biaya?\n"
        "A: Agnes dan Seedance gratis (dengan kuota harian)\n\n"
        "📞 **Butuh bantuan?** Hubungi @seeshoopsolution"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "✅ **Proses dibatalkan!**\n\n"
        "Kirim /start untuk memulai lagi.",
        parse_mode="Markdown",
    )

# ===== HANDLER CALLBACK =====
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "back_to_main":
        await query.edit_message_text(
            "🏠 **Menu Utama**\n\nPilih menu di bawah:",
            reply_markup=get_main_menu(),
            parse_mode="Markdown",
        )
    
    elif data == "image_to_video":
        text = (
            "📷 **Image-to-Video**\n\n"
            "Kirimkan **gambar + caption** dalam SATU pesan.\n\n"
            "📌 **Langkah:**\n"
            "1. Upload gambar\n"
            "2. Tulis prompt di caption\n"
            "3. Kirim dalam satu pesan\n"
            "4. Pilih model & durasi\n"
            "5. Tunggu video jadi\n\n"
            "📝 **Contoh:**\n"
            "Upload foto produk + tulis 'Buat video animasi slow motion'\n\n"
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
            "1. Tulis deskripsi video\n"
            "2. Kirim sebagai pesan teks\n"
            "3. Pilih model & durasi\n"
            "4. Tunggu video jadi\n\n"
            "📝 **Contoh Prompt:**\n"
            "\"Seorang wanita berjalan di taman bunga matahari saat matahari terbenam, gaya cinematic\"\n\n"
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
            "Kirimkan prompt video yang kamu miliki, AI akan menyempurnakannya.\n\n"
            "📝 **Contoh Input:**\n"
            "\"Produk skincare di meja putih\"\n\n"
            "📤 **Contoh Output:**\n"
            "\"9:16 vertical product close-up of a skincare bottle on a clean white podium that slowly rotates as light moves across the label, minimal studio background, premium ecommerce lighting\"\n\n"
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
            "🎯 **Pilih Model AI**\n\n"
            "1. **Agnes-Video-2.5** (Gratis, 5-15 detik)\n"
            "   ✅ Stabil, cocok untuk produk\n"
            "   ✅ Support image-to-video\n\n"
            "2. **Seedance 2.0** (Kredit harian)\n"
            "   ✅ Kualitas cinematic\n"
            "   ✅ Bisa 1080p\n"
            "   ⏱️ 5-12 detik\n"
            "   💰 25 kredit/hari gratis\n\n"
            "**Pilih model:**",
            reply_markup=get_model_menu(),
            parse_mode="Markdown",
        )
    
    elif data.startswith("model_"):
        model = data.replace("model_", "")
        context.user_data['model'] = model
        model_names = {
            "agnes": "Agnes-Video-2.5 (Gratis)",
            "seedance": "Seedance 2.0 (Kredit Harian)",
        }
        await query.edit_message_text(
            f"✅ Model dipilih: **{model_names.get(model, model)}**\n\n"
            "Pilih durasi video:",
            reply_markup=get_duration_menu(),
            parse_mode="Markdown",
        )
    
    elif data.startswith("duration_"):
        duration = int(data.replace("duration_", ""))
        context.user_data['duration'] = duration
        
        user_id = update.effective_user.id
        image_path = context.user_data.get('image_path')
        prompt = context.user_data.get('prompt', '')
        model = context.user_data.get('model', 'agnes')
        
        status_msg = await query.edit_message_text(
            f"⏳ **Memproses video...**\n\n"
            f"📝 Prompt: {prompt[:100] if prompt else '(kosong)'}\n"
            f"🎬 Durasi: {duration} detik\n"
            f"🤖 Model: {model}\n"
            f"🖼️ Gambar: {'✅ Ada' if image_path else '❌ Tidak ada'}\n\n"
            f"Ini akan memakan waktu 1-3 menit. Bot akan mengirim video otomatis setelah selesai.",
            parse_mode="Markdown",
        )
        
        try:
            # Panggil API Agnes
            video_url = await generate_video_with_agnes(
                prompt=prompt,
                image_path=image_path,
                duration=duration,
                model=model
            )
            
            if video_url:
                # Download video
                video_filename = f"user_{user_id}_output.mp4"
                video_path = os.path.join(DOWNLOAD_DIR, video_filename)
                await download_video(video_url, video_path)
                
                # Kirim video ke user
                with open(video_path, 'rb') as f:
                    await query.message.reply_video(
                        video=f,
                        caption=f"🎬 **Video selesai!**\n\n"
                                f"📝 Prompt: {prompt[:100]}\n"
                                f"🎬 Durasi: {duration} detik\n"
                                f"🤖 Model: {model}"
                    )
                
                # Hapus file
                os.remove(video_path)
                if image_path and os.path.exists(image_path):
                    os.remove(image_path)
                
                await status_msg.delete()
            else:
                await status_msg.edit_text("❌ Gagal generate video. Coba lagi nanti.")
                
        except Exception as e:
            logger.error(f"Error generate video: {str(e)}")
            await status_msg.edit_text(f"❌ Error: {str(e)[:200]}")
    
    elif data == "help":
        await query.edit_message_text(
            "❓ **Bantuan**\n\n"
            "1. Kirim gambar + prompt dalam satu pesan\n"
            "2. Pilih model & durasi\n"
            "3. Tunggu video jadi\n\n"
            "📞 **Butuh bantuan?** Hubungi @seeshoopsolution",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Kembali", callback_data="back_to_main")]
            ]),
            parse_mode="Markdown",
        )
    
    elif data == "settings":
        await query.edit_message_text(
            "⚙️ **Pengaturan**\n\n"
            "Resolusi default: **1080p**\n"
            "Aspect Ratio: **9:16 (Vertical)**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Kembali", callback_data="back_to_main")]
            ]),
            parse_mode="Markdown",
        )
    
    elif data in ["set_resolution", "set_duration", "set_aspect"]:
        await query.edit_message_text(
            "⚙️ **Fitur ini sedang dalam pengembangan.**\n\n"
            "Resolusi default: **1080p**, Aspect Ratio: **9:16 (Vertical)**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Kembali", callback_data="back_to_main")]
            ]),
            parse_mode="Markdown",
        )

# ===== HANDLER PESAN =====
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    caption = update.message.caption or ""
    photos = update.message.photo
    text = update.message.text or ""
    
    if photos:
        photo = photos[-1]
        file = await photo.get_file()
        file_path = os.path.join(DOWNLOAD_DIR, f"user_{user_id}_input.jpg")
        await file.download_to_drive(file_path)
        
        context.user_data['image_path'] = file_path
        context.user_data['prompt'] = caption
        
        prompt_preview = caption[:100] if caption else "(kosong)"
        await update.message.reply_text(
            f"✅ **Gambar dan prompt diterima!**\n\n"
            f"📝 **Prompt:** {prompt_preview}\n\n"
            f"Sekarang pilih model dan durasi untuk memulai generasi video.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎯 Pilih Model & Durasi", callback_data="choose_model")]
            ]),
            parse_mode="Markdown",
        )
    
    elif text and not photos:
        context.user_data['prompt'] = text
        await update.message.reply_text(
            f"✅ **Prompt diterima!**\n\n"
            f"📝 **Prompt:** {text[:200]}\n\n"
            f"Lanjutkan dengan text-to-video?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎯 Pilih Model & Durasi", callback_data="choose_model")]
            ]),
            parse_mode="Markdown",
        )
    
    else:
        await update.message.reply_text(
            "❌ **Kirimkan gambar + prompt dalam satu pesan!**\n\n"
            "📌 **Contoh:**\n"
            "Upload foto + tulis 'Buat video animasi slow motion'\n\n"
            "Ketik /start untuk melihat menu.",
            parse_mode="Markdown",
        )

# ===== MAIN =====
async def ping_agnes_api():
    """Cek koneksi ke Agnes AI API"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://apihub.agnes-ai.com/v1/health") as resp:
                return resp.status == 200
    except:
        return False

def main():
    if not TELEGRAM_TOKEN:
        logger.error("❌ TELEGRAM_TOKEN tidak ditemukan!")
        return
    
    if not AGNES_API_KEY:
        logger.warning("⚠️ AGNES_API_KEY tidak ditemukan! Fitur video tidak akan berfungsi.")
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.PHOTO | filters.TEXT, handle_message))
    
    logger.info("🤖 Bot AI Video berjalan...")
    application.run_polling()

if __name__ == "__main__":
    main()

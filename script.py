from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext
import yt_dlp
import os
import shutil

# Ambil TOKEN dari env
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    print("❌ TOKEN tidak ditemukan! Pastikan sudah diset di Railway.")
    exit(1)

# Cek FFmpeg
FFMPEG_PATH = shutil.which("ffmpeg")
if not FFMPEG_PATH:
    print("⚠️ FFmpeg tidak ditemukan! Install dulu sebelum jalanin bot.")
    exit(1)

# Terjemahan
translations = {
    "start": {
        "id": "Kirim link video IG, TT, YT, atau FB di sini ygy 🤪",
        "en": "Send the video link from IG, TT, YT, or FB here 🤪"
    },
    "invalid_link": {
        "id": "❌ Link tidak valid! Coba kirim link yang benar.",
        "en": "❌ Invalid link! Please send a valid link."
    },
    "choose_format": {
        "id": "Pilih format yang mau lo download:",
        "en": "Choose the format you want to download:"
    },
    "downloading": {
        "id": "🔄 Sedang mendownload...",
        "en": "🔄 Downloading..."
    },
    "choose_language": {
        "id": "Pilih bahasa bot:",
        "en": "Choose the bot language:"
    },
    "language_changed": {
        "id": "✅ Bahasa telah diubah ke Indonesia",
        "en": "✅ Language has been changed to English"
    }
}

def get_language_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇮🇩 Bahasa Indonesia", callback_data="lang_id"),
         InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")]
    ])

async def start(update: Update, context: CallbackContext):
    lang = context.user_data.get("lang", "id")
    await update.message.reply_text(translations["start"][lang], reply_markup=get_language_keyboard())

async def change_language(update: Update, context: CallbackContext):
    query = update.callback_query
    lang = query.data.split("_")[1]
    context.user_data["lang"] = lang

    await query.answer()
    await query.edit_message_text(translations["language_changed"][lang])

async def ask_format(update: Update, context: CallbackContext):
    lang = context.user_data.get("lang", "id")
    url = update.message.text.strip()

    if not url.startswith(("http://", "https://")):
        await update.message.reply_text(translations["invalid_link"][lang])
        return

    context.user_data["url"] = url

    keyboard = [
        [InlineKeyboardButton("🎥 Video", callback_data="video")],
        [InlineKeyboardButton("🎵 Audio", callback_data="audio")],
        [InlineKeyboardButton("❌ Batal", callback_data="cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(translations["choose_format"][lang], reply_markup=reply_markup)

async def ask_resolution(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    context.user_data["format_type"] = query.data  # video atau audio
    if query.data == "audio":
        await download_media(update, context)
        return

    lang = context.user_data.get("lang", "id")
    keyboard = [
        [InlineKeyboardButton("360p", callback_data="res_360p"),
         InlineKeyboardButton("720p", callback_data="res_720p"),
         InlineKeyboardButton("1080p", callback_data="res_1080p")],
        [InlineKeyboardButton("❌ Batal", callback_data="cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(translations["choose_format"][lang], reply_markup=reply_markup)

async def download_media(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    lang = context.user_data.get("lang", "id")
    url = context.user_data.get("url")
    format_type = context.user_data.get("format_type")

    if query.data == "cancel":
        await query.edit_message_text("🚫 Download dibatalkan.")
        return

    await query.edit_message_text(translations["downloading"][lang])

    filename = "media"
    ydl_opts = {
        'format': 'bestaudio/best' if format_type == "audio" else 'bestvideo+bestaudio/best',
        'outtmpl': f"{filename}.%(ext)s",
        'noplaylist': True,
    }

    if format_type == "audio":
        ydl_opts["postprocessors"] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    await query.edit_message_text(f"✅ Download selesai! Cek file `{filename}`.")

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("language", change_language))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ask_format))
    app.add_handler(CallbackQueryHandler(ask_resolution, pattern="^(video|audio)$"))
    app.add_handler(CallbackQueryHandler(download_media, pattern="^res_"))

    print("🚀 Bot berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()

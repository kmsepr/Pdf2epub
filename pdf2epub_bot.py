import os
import asyncio
import subprocess
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    document = message.document

    if document.mime_type != "application/pdf":
        await message.reply_text("Please forward a PDF document.")
        return

    pdf_file_path = os.path.join(DOWNLOAD_DIR, document.file_name)
    await document.get_file().download_to_drive(pdf_file_path)
    await message.reply_text("PDF downloaded, converting to EPUB...")

    epub_file_path = pdf_file_path.replace(".pdf", ".epub")
    try:
        subprocess.run(["pdf2epub", pdf_file_path, epub_file_path], check=True)
    except subprocess.CalledProcessError:
        await message.reply_text("Failed to convert PDF to EPUB.")
        return

    await message.reply_document(document=open(epub_file_path, "rb"), filename=os.path.basename(epub_file_path))

    os.remove(pdf_file_path)
    os.remove(epub_file_path)

async def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("No TELEGRAM_BOT_TOKEN found in environment variables")

    app = ApplicationBuilder().token(token).build()

    forwarded_filter = filters.MessageFilter(lambda message: message.forward_date is not None)

    app.add_handler(MessageHandler(filters.Document.ALL & forwarded_filter, handle_document))

    print("Bot is running...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
import os
import subprocess
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

DOWNLOAD_DIR = "/tmp"

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
        # Use your PDF to EPUB conversion command here
        subprocess.run(["pdf2epub", pdf_file_path, epub_file_path], check=True)
    except subprocess.CalledProcessError:
        await message.reply_text("Failed to convert PDF to EPUB.")
        return

    await message.reply_document(document=open(epub_file_path, "rb"), filename=os.path.basename(epub_file_path))

    # Clean up files
    os.remove(pdf_file_path)
    os.remove(epub_file_path)

if __name__ == "__main__":
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN environment variable not set")
        exit(1)

    app = ApplicationBuilder().token(token).build()

    # Filter for forwarded messages
    forwarded_filter = filters.Document.ALL & filters.Message(lambda msg: msg.forward_date is not None)

    app.add_handler(MessageHandler(forwarded_filter, handle_document))

    print("Bot is running...")
    app.run_polling()
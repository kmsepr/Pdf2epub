import os
import fitz  # PyMuPDF
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
import subprocess

# === Configuration ===
TOKEN = os.getenv("TELEGRAM_TOKEN")  # Set this as an environment variable
WATERMARK_KEYWORDS = [
    "Licensed to",
    "This PDF was generated for",
    "Confidential",
    "Watermarked Copy",
    "For XYZ only"
]

# === Logging ===
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


# === Step 1: Remove watermark text from PDF ===
def remove_watermark_text(input_pdf, output_pdf):
    doc = fitz.open(input_pdf)
    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            if "lines" not in b:
                continue
            for line in b["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    if any(keyword.lower() in text.lower() for keyword in WATERMARK_KEYWORDS):
                        rect = fitz.Rect(span["bbox"])
                        page.add_redact_annot(rect, fill=(1, 1, 1))  # White fill
        page.apply_redactions()
    doc.save(output_pdf)
    doc.close()


# === Step 2: Convert to EPUB using Calibre ===
def convert_pdf_to_epub(pdf_path):
    clean_pdf = pdf_path.replace(".pdf", "_clean.pdf")
    epub_path = pdf_path.replace(".pdf", ".epub")

    remove_watermark_text(pdf_path, clean_pdf)

    result = subprocess.run(["ebook-convert", clean_pdf, epub_path])

    if result.returncode == 0 and os.path.exists(epub_path):
        return epub_path
    return None


# === Step 3: Telegram Bot ===
async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document

    if not document or not document.file_name.lower().endswith(".pdf"):
        await update.message.reply_text("Please send a valid PDF file.")
        return

    await update.message.reply_text("📥 Downloading and processing your PDF...")

    # Save the uploaded file
    file_path = f"/tmp/{document.file_name}"
    new_file = await context.bot.get_file(document.file_id)
    await new_file.download_to_drive(file_path)

    # Convert the file
    await update.message.reply_text("🔄 Removing watermarks and converting to EPUB...")
    epub_path = convert_pdf_to_epub(file_path)

    if epub_path:
        await update.message.reply_document(document=open(epub_path, "rb"),
                                            filename=os.path.basename(epub_path),
                                            caption="✅ Here is your EPUB file!")
    else:
        await update.message.reply_text("❌ Failed to convert the PDF to EPUB.")


# === Start the Bot ===
def main():
    if not TOKEN:
        print("❌ TELEGRAM_TOKEN environment variable is not set.")
        return

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))

    print("🤖 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()

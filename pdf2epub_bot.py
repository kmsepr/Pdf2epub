import os
import tempfile
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import fitz  # PyMuPDF
from ebooklib import epub

# Get your bot token from environment variable for security
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("Please set TELEGRAM_BOT_TOKEN environment variable")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me a forwarded PDF file, and I'll convert it to EPUB!")

def pdf_to_epub(pdf_path, epub_path):
    # Open PDF
    doc = fitz.open(pdf_path)

    book = epub.EpubBook()
    book.set_identifier('id123456')
    book.set_title('Converted PDF to EPUB')
    book.set_language('en')

    # Add a default chapter for each page with text content
    chapters = []
    for i, page in enumerate(doc):
        text = page.get_text()
        c = epub.EpubHtml(title=f'Page {i+1}', file_name=f'chap_{i+1}.xhtml', lang='en')
        # Simple HTML formatting, replace newlines with <br> for better layout
        html_content = '<br>'.join(text.split('\n'))
        c.content = f'<h1>Page {i+1}</h1><p>{html_content}</p>'
        book.add_item(c)
        chapters.append(c)

    # Define Table Of Contents and Spine
    book.toc = tuple(chapters)
    book.spine = ['nav'] + chapters

    # Add navigation files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Write to EPUB
    epub.write_epub(epub_path, book)

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    # Check if message is forwarded and has document
    if message.forward_date and message.document:
        doc = message.document
        if doc.mime_type != 'application/pdf':
            await message.reply_text("Please send a PDF file.")
            return

        # Download PDF to temp file
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, 'input.pdf')
            epub_path = os.path.join(tmpdir, 'output.epub')

            await doc.get_file().download_to_drive(pdf_path)

            # Convert PDF to EPUB
            try:
                pdf_to_epub(pdf_path, epub_path)
            except Exception as e:
                await message.reply_text(f"Failed to convert PDF to EPUB: {e}")
                return

            # Send EPUB back
            with open(epub_path, 'rb') as f:
                await message.reply_document(InputFile(f, filename='converted.epub'))

    else:
        await message.reply_text("Please forward a PDF document to convert.")

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL & filters.Forwarded, handle_document))

    print("Bot is running...")
    await app.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
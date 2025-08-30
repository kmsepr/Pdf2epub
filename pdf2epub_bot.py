import os
import asyncio
import logging
from pyrogram import Client, filters
from pdf2image import convert_from_path
import pytesseract
from ebooklib import epub
from aiohttp import web

# ---------------- Logging ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- Bot Credentials ----------------
API_ID = int(os.getenv("API_ID", "123456"))        # replace with your API_ID or env var
API_HASH = os.getenv("API_HASH", "your_api_hash")  # replace with your API_HASH or env var
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token")

bot = Client("pdf2epub_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ---------------- Helpers ----------------
async def pdf_to_epub(pdf_path, output_path, use_ocr=False):
    book = epub.EpubBook()
    book.set_identifier("pdf2epub")
    book.set_title("Converted Book")
    book.set_language("en")

    if use_ocr:
        logger.info("Running OCR on PDF...")
        pages = convert_from_path(pdf_path)
        text_content = ""
        for page in pages:
            text_content += pytesseract.image_to_string(page, lang="eng") + "\n"
    else:
        # Fallback: extract text with PyPDF2
        import PyPDF2
        reader = PyPDF2.PdfReader(open(pdf_path, "rb"))
        text_content = "\n".join([p.extract_text() or "" for p in reader.pages])

    # Add text to EPUB
    chapter = epub.EpubHtml(title="Content", file_name="content.xhtml", lang="en")
    chapter.content = f"<h1>Converted PDF</h1><p>{text_content}</p>"
    book.add_item(chapter)

    # TOC & navigation
    book.toc = (epub.Link("content.xhtml", "Content", "content"),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    epub.write_epub(output_path, book)
    return output_path

# ---------------- Bot Handlers ----------------
@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("👋 Send me a PDF and I will convert it to EPUB (with OCR support).")

@bot.on_message(filters.document & filters.file_mime_type("application/pdf"))
async def handle_pdf(client, message):
    try:
        pdf_file = await message.download()
        epub_file = pdf_file.replace(".pdf", ".epub")

        # Run OCR only if user says "ocr"
        use_ocr = "ocr" in (message.caption or "").lower()

        await message.reply_text("📚 Converting your PDF... Please wait ⏳")

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, pdf_to_epub, pdf_file, epub_file, use_ocr)

        await message.reply_document(epub_file, caption="✅ Here is your EPUB!")

        os.remove(pdf_file)
        os.remove(epub_file)

    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        await message.reply_text(f"❌ Failed to convert: {e}")

# ---------------- Dummy Web Server ----------------
async def healthcheck(request):
    return web.Response(text="Bot is alive!")

def run_web():
    app = web.Application()
    app.router.add_get("/", healthcheck)
    web.run_app(app, port=int(os.getenv("PORT", 8080)))

# ---------------- Run Both ----------------
if __name__ == "__main__":
    import threading
    t = threading.Thread(target=run_web, daemon=True)
    t.start()
    bot.run()
import os
import asyncio
import logging
from pyrogram import Client, filters
from pdf2image import convert_from_path, pdfinfo_from_path
import pytesseract
from ebooklib import epub
from flask import Flask
from langdetect import detect

# ---------------- Logging ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- Bot Credentials ----------------
API_ID = int(os.getenv("API_ID", "123456"))        # replace with your API_ID or env var
API_HASH = os.getenv("API_HASH", "your_api_hash")  # replace with your API_HASH or env var
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token")

bot = Client("pdf2epub_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ---------------- Helpers ----------------
def clean_ocr_text(raw_text: str):
    """Filter only English and split into headlines/content."""
    lines = raw_text.split("\n")
    english_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            if detect(line) == "en":  # keep only English
                english_lines.append(line)
        except:
            continue

    headlines = []
    content_blocks = []
    current_block = []

    for line in english_lines:
        if line.isupper() or (len(line.split()) <= 6 and line.istitle()):
            if current_block:  # save current block
                content_blocks.append(" ".join(current_block))
                current_block = []
            headlines.append(line)
        else:
            current_block.append(line)

    if current_block:
        content_blocks.append(" ".join(current_block))

    return headlines, content_blocks

def pdf_to_epub(pdf_path, output_path):
    book = epub.EpubBook()
    book.set_identifier("pdf2epub")
    book.set_title("Converted Book")
    book.set_language("en")

    headlines = []
    contents = []

    logger.info("Running OCR on PDF page by page...")

    # Get total pages
    info = pdfinfo_from_path(pdf_path)
    total_pages = info["Pages"]

    for page_number in range(1, total_pages + 1):
        pages = convert_from_path(
            pdf_path, dpi=200, first_page=page_number, last_page=page_number
        )
        page_image = pages[0]
        raw_text = pytesseract.image_to_string(page_image, lang="eng")

        page_headlines, page_contents = clean_ocr_text(raw_text)
        headlines.extend(page_headlines)
        contents.extend(page_contents)

        # Free memory
        del page_image
        del pages

    # Build EPUB chapters
    chapters = []
    for idx, content in enumerate(contents):
        title = headlines[idx] if idx < len(headlines) else f"Chapter {idx+1}"
        chapter = epub.EpubHtml(title=title, file_name=f"chap_{idx+1}.xhtml", lang="en")
        chapter.content = f"<h2>{title}</h2><p>{content}</p>"
        book.add_item(chapter)
        chapters.append(chapter)

    # TOC & navigation
    book.toc = tuple(chapters)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav"] + chapters

    epub.write_epub(output_path, book)
    return output_path

# ---------------- Bot Handlers ----------------
@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text(
        "👋 Send me a PDF and I will OCR it and convert to EPUB (English only)."
    )

@bot.on_message(filters.document)
async def handle_pdf(client, message):
    if not message.document.file_name.lower().endswith(".pdf"):
        return await message.reply_text("❌ Please send a valid PDF file.")

    try:
        pdf_file = await message.download()
        epub_file = pdf_file.replace(".pdf", ".epub")

        await message.reply_text("📚 Running OCR and converting your PDF... Please wait ⏳")

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, pdf_to_epub, pdf_file, epub_file)

        await message.reply_document(epub_file, caption="✅ Here is your EPUB!")

        os.remove(pdf_file)
        os.remove(epub_file)

    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        await message.reply_text(f"❌ Failed to convert: {e}")

# ---------------- Flask Health Server ----------------
flask_app = Flask(__name__)

@flask_app.route("/")
def healthcheck():
    return "Bot is alive!", 200

def run_flask():
    port = int(os.getenv("PORT", 5000))
    flask_app.run(host="0.0.0.0", port=port)

# ---------------- Run Both ----------------
if __name__ == "__main__":
    import threading
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()
    bot.run()
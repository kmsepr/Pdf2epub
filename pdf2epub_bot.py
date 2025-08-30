import os
import asyncio
import logging
import tempfile
import time
from pyrogram import Client, filters
from ebooklib import epub
from flask import Flask
from langdetect import detect
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
import pytesseract
import threading

# ---------------- Logging ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- Bot Credentials ----------------
API_ID = int(os.getenv("API_ID", "123456"))
API_HASH = os.getenv("API_HASH", "your_api_hash")
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token")

bot = Client("pdf2epub_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ---------------- Conversion Tracking ----------------
conversion_tasks = {}  # chat_id -> threading.Event

# ---------------- Helpers ----------------
def clean_text(raw_text: str):
    """Filter only English and split into headlines/content."""
    lines = raw_text.split("\n")
    english_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            if detect(line) == "en":
                english_lines.append(line)
        except:
            continue

    headlines, content_blocks, current_block = [], [], []
    for line in english_lines:
        if line.isupper() or (len(line.split()) <= 6 and line.istitle()):
            if current_block:
                content_blocks.append(" ".join(current_block))
                current_block = []
            headlines.append(line)
        else:
            current_block.append(line)
    if current_block:
        content_blocks.append(" ".join(current_block))

    return headlines, content_blocks

# ---------------- PDF to EPUB ----------------
async def pdf_to_epub(pdf_path, output_path, client=None, chat_id=None, cancel_flag=None):
    book = epub.EpubBook()
    book.set_identifier("pdf2epub")
    book.set_title("Converted Book")
    book.set_language("en")

    reader = PdfReader(pdf_path)
    headlines, contents = [], []

    total_pages = len(reader.pages)
    progress_msg = None
    if client and chat_id:
        progress_msg = await client.send_message(chat_id, "Starting PDF conversion...")

    start_time = time.time()

    for page_number, page in enumerate(reader.pages, start=1):
        if cancel_flag and cancel_flag.is_set():
            if progress_msg:
                await progress_msg.edit_text("❌ Conversion cancelled by user.")
            logger.info(f"Conversion cancelled: {chat_id}")
            return None

        raw_text = page.extract_text()
        if raw_text and raw_text.strip():
            page_headlines, page_contents = clean_text(raw_text)
            page_type = "text-based"
        else:
            page_type = "image-based (OCR)"
            with tempfile.TemporaryDirectory() as tmpdir:
                pages = convert_from_path(
                    pdf_path,
                    dpi=200,
                    first_page=page_number,
                    last_page=page_number,
                    fmt="png",
                    output_folder=tmpdir,
                )
                page_image = pages[0]
                raw_text = pytesseract.image_to_string(page_image, lang="eng")
                page_headlines, page_contents = clean_text(raw_text)
                del page_image
                del pages

        headlines.extend(page_headlines)
        contents.extend(page_contents)

        # Progress and ETA
        elapsed = time.time() - start_time
        avg_time = elapsed / page_number
        remaining_pages = total_pages - page_number
        eta_seconds = int(avg_time * remaining_pages)
        eta_text = time.strftime("%M:%S", time.gmtime(eta_seconds))

        percent = int((page_number / total_pages) * 100)
        bar_length = 20
        filled_length = int(bar_length * percent // 100)
        bar = "█" * filled_length + "─" * (bar_length - filled_length)

        progress_text = (
            f"📄 Page {page_number}/{total_pages} ({page_type})\n"
            f"[{bar}] {percent}%\n⏳ ETA: {eta_text}"
        )

        if progress_msg:
            try:
                await progress_msg.edit_text(progress_text)
            except Exception as e:
                logger.warning(f"Failed to edit progress message: {e}")

    # Build EPUB chapters
    chapters = []
    for idx, content in enumerate(contents):
        title = headlines[idx] if idx < len(headlines) else f"Chapter {idx+1}"
        chapter = epub.EpubHtml(title=title, file_name=f"chap_{idx+1}.xhtml", lang="en")
        chapter.content = f"<h2>{title}</h2><p>{content}</p>"
        book.add_item(chapter)
        chapters.append(chapter)

    book.toc = tuple(chapters)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav"] + chapters

    epub.write_epub(output_path, book)
    logger.info(f"EPUB created successfully: {output_path}")

    if progress_msg:
        try:
            await progress_msg.edit_text(f"✅ Conversion complete! EPUB ready.")
        except:
            pass

    return output_path

# ---------------- Bot Handlers ----------------
@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text(
        "👋 Send me a PDF and I will convert it to EPUB. OCR is used only if needed.\n"
        "You can send /cancel to stop an ongoing conversion."
    )

@bot.on_message(filters.document)
async def handle_pdf(client, message):
    if not message.document.file_name.lower().endswith(".pdf"):
        return await message.reply_text("❌ Please send a valid PDF file.")

    cancel_flag = threading.Event()
    conversion_tasks[message.chat.id] = cancel_flag

    try:
        pdf_file = await message.download()
        epub_file = pdf_file.replace(".pdf", ".epub")

        await message.reply_text("📚 Converting your PDF... Please wait ⏳")

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, 
            lambda: asyncio.run(pdf_to_epub(pdf_file, epub_file, client, message.chat.id, cancel_flag))
        )

        if cancel_flag.is_set():
            if os.path.exists(pdf_file):
                os.remove(pdf_file)
            if os.path.exists(epub_file):
                os.remove(epub_file)
            return

        await message.reply_document(epub_file, caption="✅ Here is your EPUB!")

        os.remove(pdf_file)
        os.remove(epub_file)

    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        await message.reply_text(f"❌ Failed to convert: {e}")
    finally:
        conversion_tasks.pop(message.chat.id, None)

@bot.on_message(filters.command("cancel"))
async def cancel_conversion(client, message):
    chat_id = message.chat.id
    flag = conversion_tasks.get(chat_id)
    if flag:
        flag.set()
        await message.reply_text("🛑 Conversion cancelled.")
    else:
        await message.reply_text("❌ No ongoing conversion to cancel.")

# ---------------- Flask Health Server ----------------
flask_app = Flask(__name__)

@flask_app.route("/")
def healthcheck():
    return "Bot is alive!", 200

def run_flask():
    port = int(os.getenv("PORT", 5000))
    flask_app.run(host="0.0.0.0", port=port)

# ---------------- Keep-Alive Ping ----------------
def keep_alive_ping():
    import requests
    URL = "https://your-koyeb-app-url/"  # replace with your Flask healthcheck URL
    while True:
        try:
            r = requests.get(URL)
            print(f"{time.ctime()} - Pinged, status: {r.status_code}")
        except Exception as e:
            print(f"{time.ctime()} - Failed: {e}")
        time.sleep(300)  # every 5 minutes

# ---------------- Run Both ----------------
if __name__ == "__main__":
    # Start Flask
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()

    # Start keep-alive ping
    ping_thread = threading.Thread(target=keep_alive_ping, daemon=True)
    ping_thread.start()

    # Run the bot
    bot.run()
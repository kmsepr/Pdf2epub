import os
import tempfile
from pyrogram import Client, filters
from pyrogram.types import Message
from PyPDF2 import PdfReader
from ebooklib import epub

# ==============================
# 🔑 Config
# ==============================
API_ID = int(os.environ.get("API_ID", "12345"))
API_HASH = os.environ.get("API_HASH", "your_api_hash")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_bot_token")

app = Client(
    "pdf2epub_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ==============================
# Custom forwarded filter
# ==============================
forwarded_filter = filters.document & filters.create(
    lambda flt, cli, msg: msg.forward_date is not None
)

# ==============================
# PDF → EPUB conversion function
# ==============================
def pdf_to_epub(pdf_path, epub_path):
    reader = PdfReader(pdf_path)

    # Create EPUB book
    book = epub.EpubBook()
    book.set_identifier("pdf2epub")
    book.set_title("Converted PDF")
    book.set_language("en")

    # Add a simple chapter per page
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        chapter = epub.EpubHtml(
            title=f"Page {i}",
            file_name=f"page_{i}.xhtml",
            lang="en"
        )
        chapter.content = f"<html><body><pre>{text}</pre></body></html>"
        book.add_item(chapter)
        book.spine.append(chapter)

    # Default NCX/nav
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Write EPUB
    epub.write_epub(epub_path, book, {})

# ==============================
# Handlers
# ==============================
@app.on_message(filters.command("start"))
async def start_handler(client: Client, message: Message):
    await message.reply_text("👋 Hello! Send me a PDF (or forward one) and I will convert it to EPUB.")

@app.on_message(filters.document)
async def handle_document(client: Client, message: Message):
    if message.document.mime_type == "application/pdf":
        await message.reply_text("📥 Downloading PDF...")

        # Save PDF temporarily
        pdf_file = await message.download()
        epub_file = tempfile.mktemp(suffix=".epub")

        try:
            pdf_to_epub(pdf_file, epub_file)
            await message.reply_document(
                epub_file,
                caption="✅ Converted to EPUB"
            )
        except Exception as e:
            await message.reply_text(f"❌ Conversion failed: {e}")
        finally:
            os.remove(pdf_file)
            if os.path.exists(epub_file):
                os.remove(epub_file)
    else:
        await message.reply_text("⚠️ Only PDF files are supported.")

@app.on_message(forwarded_filter)
async def handle_forwarded_document(client: Client, message: Message):
    # Forwarded PDFs go here (same logic as above)
    await handle_document(client, message)

# ==============================
# Run
# ==============================
if __name__ == "__main__":
    print("🤖 Bot is starting...")
    app.run()
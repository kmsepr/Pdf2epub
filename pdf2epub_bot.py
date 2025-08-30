import os
from pyrogram import Client, filters
from pyrogram.types import Message
from PyPDF2 import PdfReader
from ebooklib import epub
import pytesseract
from pdf2image import convert_from_path
from PIL import Image

# Load from environment
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Client("pdf2epub_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


def pdf_to_epub(pdf_path, epub_path):
    reader = PdfReader(pdf_path)
    book = epub.EpubBook()
    book.set_identifier("pdf2epub")
    book.set_title("Converted PDF")
    book.set_language("en")

    has_text = False

    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            has_text = True
        chapter = epub.EpubHtml(
            title=f"Page {i}",
            file_name=f"page_{i}.xhtml",
            lang="en"
        )
        chapter.content = f"<html><body><pre>{text}</pre></body></html>"
        book.add_item(chapter)
        book.spine.append(chapter)

    # OCR fallback
    if not has_text:
        images = convert_from_path(pdf_path, dpi=200)
        book = epub.EpubBook()
        book.set_identifier("pdf2epub")
        book.set_title("Converted PDF (OCR)")
        book.set_language("en")

        for i, img in enumerate(images, start=1):
            text = pytesseract.image_to_string(img, lang="eng+mal")  # OCR English + Malayalam
            chapter = epub.EpubHtml(
                title=f"Page {i}",
                file_name=f"page_{i}.xhtml",
                lang="en"
            )
            chapter.content = f"<html><body><pre>{text}</pre></body></html>"
            book.add_item(chapter)
            book.spine.append(chapter)

        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        epub.write_epub(epub_path, book, {})
        return

    # Normal text PDF
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    epub.write_epub(epub_path, book, {})


@bot.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply_text("👋 Hello! Send me a PDF (or forward one) and I will convert it to EPUB (supports OCR).")


@bot.on_message(filters.document.mime_type("application/pdf"))
async def handle_pdf(client, message: Message):
    file = await message.download()
    epub_file = file.replace(".pdf", ".epub")

    await message.reply_text("📄 Received PDF! Converting...")

    try:
        pdf_to_epub(file, epub_file)
        await message.reply_document(epub_file, caption="✅ Here is your EPUB file")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")
    finally:
        if os.path.exists(file):
            os.remove(file)
        if os.path.exists(epub_file):
            os.remove(epub_file)


if __name__ == "__main__":
    bot.run()
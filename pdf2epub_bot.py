import os
from pyrogram import Client, filters
from pyrogram.types import Message

# ==============================
# 🔑 Configuration
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
# ✅ Forwarded filter for documents
# ==============================
forwarded_filter = filters.document & filters.create(
    lambda flt, cli, msg: msg.forward_date is not None
)

# ==============================
# 🚀 Handlers
# ==============================
@app.on_message(filters.command("start"))
async def start_handler(client: Client, message: Message):
    await message.reply_text("👋 Hello! Send me a PDF (or forward one) and I will convert it to EPUB.")

@app.on_message(filters.document)
async def handle_document(client: Client, message: Message):
    if message.document.mime_type == "application/pdf":
        await message.reply_text("📄 Received PDF! (Normal document, not forwarded)")
        # TODO: convert pdf → epub here
    else:
        await message.reply_text("⚠️ Only PDF files are supported.")

@app.on_message(forwarded_filter)
async def handle_forwarded_document(client: Client, message: Message):
    if message.document.mime_type == "application/pdf":
        await message.reply_text("📄 Received *forwarded* PDF!")
        # TODO: convert pdf → epub here
    else:
        await message.reply_text("⚠️ Only PDF files are supported.")

# ==============================
# ▶️ Run
# ==============================
if __name__ == "__main__":
    print("🤖 Bot is starting...")
    app.run()
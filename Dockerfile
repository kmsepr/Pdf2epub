FROM python:3.11-slim

# Install system dependencies for OCR and PDF handling
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY pdf2epub_bot.py .

# Expose port for aiohttp healthcheck
EXPOSE 5000

# Run the bot
CMD ["python", "pdf2epub_bot.py"]
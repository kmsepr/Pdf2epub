# Use a lightweight Python image
FROM python:3.11-slim

# Install system dependencies for OCR (tesseract + poppler for pdf2image)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements first (for caching layers)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot script
COPY pdf2epub_bot.py .

# Expose Flask port
EXPOSE 5000

# Run the bot
CMD ["python", "pdf2epub_bot.py"]
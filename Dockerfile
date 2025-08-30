# Use Python base image
FROM python:3.11-slim

# Install system dependencies for pdf2image & pytesseract
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements.txt
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY . .

# Set environment variables (Pyrogram needs these)
ENV PYTHONUNBUFFERED=1

# Run the bot
CMD ["python", "pdf2epub_bot.py"]
# Use official Python base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (for OCR and PDF handling)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    ghostscript \
    libxml2 \
    libxslt1.1 \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt first (for caching layers)
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy your bot script
COPY pdf2epub_bot.py /app/

# Expose port 5000
EXPOSE 5000

# Run the app
CMD ["python", "pdf2epub_bot.py"]
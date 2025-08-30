# Use lightweight Python image
FROM python:3.10-slim

# Install system dependencies (poppler for pdf2image, tesseract for OCR)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements (if you have one)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY pdf2epub_bot.py .

# Expose port (if needed, e.g. webhook mode)
EXPOSE 8080

# Run bot
CMD ["python", "pdf2epub_bot.py"]
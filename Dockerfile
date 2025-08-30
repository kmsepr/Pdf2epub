FROM python:3.11-slim

# Install system dependencies for Calibre and general tools
RUN apt-get update && apt-get install -y \
    wget \
    xz-utils \
    libgl1 \
    libegl1 \
    libopengl0 \
    libglib2.0-0 \
    libxcb-cursor0 \
    && rm -rf /var/lib/apt/lists/*

# Install Calibre CLI (ebook-convert)
RUN wget -nv -O- https://download.calibre-ebook.com/linux-installer.sh | sh /dev/stdin

# Set working directory
WORKDIR /app

# Copy the bot script into the container
COPY pdf2epub_bot.py /app/pdf2epub_bot.py

# Install Python dependencies
RUN pip install --no-cache-dir python-telegram-bot==20.6 PyMuPDF

# Set environment variable for Telegram Bot Token
ENV TELEGRAM_TOKEN="REPLACE_THIS_WITH_ENV"

# Run the bot
CMD ["python", "pdf2epub_bot.py"]
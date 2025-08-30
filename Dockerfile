FROM python:3.11-slim

# Install Calibre dependencies and Calibre
RUN apt-get update && apt-get install -y \
    wget \
    xz-utils \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Calibre CLI (ebook-convert)
RUN wget -nv -O- https://download.calibre-ebook.com/linux-installer.sh | sh /dev/stdin

# Set working directory
WORKDIR /app

# Copy the Python bot script
COPY pdf2epub_bot.py /app/pdf2epub_bot.py

# Install required Python libraries
RUN pip install --no-cache-dir python-telegram-bot==20.6 PyMuPDF

# Environment variable (set properly in Koyeb dashboard)
ENV TELEGRAM_TOKEN="your_bot_token_here"

# Run the bot
CMD ["python", "pdf2epub_bot.py"]
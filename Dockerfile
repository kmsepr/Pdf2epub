FROM python:3.11-slim

# Install system dependencies required for Calibre
RUN apt-get update && apt-get install -y \
    wget \
    xz-utils \
    libgl1 \
    libegl1 \
    libopengl0 \
    libglib2.0-0 \
    libxcb-cursor0 \
    libfreetype6 \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxfixes3 \
    libxi6 \
    libxtst6 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libcups2 \
    libxrandr2 \
    libgtk-3-0 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Calibre
RUN wget -nv -O- https://download.calibre-ebook.com/linux-installer.sh | sh /dev/stdin

# Set working directory
WORKDIR /data

# Default command
CMD ["ebook-convert", "--help"]
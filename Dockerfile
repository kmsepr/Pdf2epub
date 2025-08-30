# Use official Python base image
FROM python:3.11-slim

# Install dependencies for Calibre ebook-convert
RUN apt-get update && apt-get install -y \
    wget \
    xz-utils \
    libglu1-mesa \
    libxrender1 \
    libxext6 \
    libsm6 \
    libfontconfig1 \
    libfreetype6 \
    libx11-6 \
    libxrender1 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Download and install Calibre (ebook-convert)
RUN wget -nv -O- https://download.calibre-ebook.com/linux-installer.sh | sh /dev/stdin

# Set working directory inside container
WORKDIR /app

# Copy your Python bot script and requirements
COPY pdf2epub_bot.py /app/
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create folders for uploads and converted files
RUN mkdir uploads converted

# Expose port 5000 for the Flask app
EXPOSE 5000

# Run the Flask app
CMD ["python", "pdf2epub_bot.py"]
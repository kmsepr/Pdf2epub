# Use official Python image as base
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot script
COPY pdf2epub_bot.py .

# Set environment variable for Telegram token (can override at runtime)
ENV TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN_HERE"

# Run the bot
CMD ["python", "pdf2epub_bot.py"]
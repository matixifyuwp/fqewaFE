#!/bin/bash
echo "Deploying Discord Bot..."

# Install dependencies
pip install -r requirements.txt

# Install tesseract (for Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-eng

# Set environment variables (replace with your actual token)
export DISCORD_BOT_TOKEN="MTQxMDM4ODg2MzMzMDk0MzAyNw.GP1MIP.dzy3EKxwIV6xUf2pXEiLSImY-3MKBPrrkXV7TY"

# Run bot
python bot.py

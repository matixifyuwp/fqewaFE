import discord
from discord.ext import commands
import asyncio
import re
from PIL import Image
import pytesseract
import requests
from io import BytesIO
import os
import platform
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

# Configure Tesseract for different platforms
def setup_tesseract():
    if platform.system() == "Windows":
        possible_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        ]
        for path in possible_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                return True
    else:
        # Linux/Unix systems (most cloud providers)
        try:
            pytesseract.get_tesseract_version()
            return True
        except:
            pass
    return False

# Setup tesseract
if not setup_tesseract():
    print("Warning: Tesseract not found, but continuing...")

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Configuration - Use environment variables for security
VERIFY_CHANNEL_ID = int(os.getenv('VERIFY_CHANNEL_ID', '1410337754168168529'))
VERIFY_ROLE_ID = int(os.getenv('VERIFY_ROLE_ID', '1408105302599012374'))
BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

if not BOT_TOKEN:
    print("Error: DISCORD_BOT_TOKEN environment variable not set!")
    exit(1)

@bot.event
async def on_ready():
    print(f'{bot.user} has logged in!')
    print(f'Bot is ready to verify subscriptions!')
    
    # Test Tesseract
    try:
        version = pytesseract.get_tesseract_version()
        print(f'✅ Tesseract OCR is working! Version: {version}')
    except Exception as e:
        print(f'⚠️ Tesseract OCR not available: {e}')

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    if message.channel.id != VERIFY_CHANNEL_ID:
        return
    
    if not message.attachments:
        await message.delete()
        temp_msg = await message.channel.send(f"{message.author.mention}, please upload a screenshot of your YouTube subscription to @Axis-Hub!")
        await asyncio.sleep(5)
        await temp_msg.delete()
        return
    
    for attachment in message.attachments:
        if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
            try:
                response = requests.get(attachment.url)
                image = Image.open(BytesIO(response.content))
                
                try:
                    extracted_text = pytesseract.image_to_string(image)
                except Exception as ocr_error:
                    print(f"OCR Error: {ocr_error}")
                    # Fallback: check filename or use basic image analysis
                    extracted_text = attachment.filename.lower()
                
                if await is_valid_subscription(extracted_text, message.author):
                    await verify_user(message)
                    return
                else:
                    await message.delete()
                    temp_msg = await message.channel.send(
                        f"{message.author.mention}, your screenshot doesn't show a valid subscription to @Axis-Hub. "
                        f"Please make sure you're subscribed and the screenshot is clear."
                    )
                    await asyncio.sleep(10)
                    await temp_msg.delete()
                    return
                    
            except Exception as e:
                print(f"Error processing image: {e}")
                await message.delete()
                temp_msg = await message.channel.send(f"{message.author.mention}, there was an error processing your image. Please try again.")
                await asyncio.sleep(5)
                await temp_msg.delete()
                return

async def is_valid_subscription(text, user):
    text_lower = text.lower()
    
    subscription_keywords = ["subscribed", "subscribe", "axis-hub", "axis hub", "@axis-hub"]
    youtube_indicators = ["youtube", "subscribers", "videos", "notification", "bell"]
    
    has_subscription = any(keyword in text_lower for keyword in subscription_keywords)
    has_youtube = any(indicator in text_lower for indicator in youtube_indicators)
    has_axis_hub = any(term in text_lower for term in ["axis-hub", "axis hub"])
    
    return has_subscription and (has_youtube or has_axis_hub)

async def verify_user(message):
    try:
        guild = message.guild
        member = message.author
        
        verify_role = guild.get_role(VERIFY_ROLE_ID)
        if not verify_role:
            print(f"Could not find role with ID {VERIFY_ROLE_ID}")
            return
        
        await member.add_roles(verify_role)
        await message.delete()
        
        success_msg = await message.channel.send(
            f"✅ {member.mention} has been successfully verified! "
            f"Thank you for subscribing to @Axis-Hub!"
        )
        
        verify_channel = bot.get_channel(VERIFY_CHANNEL_ID)
        if verify_channel:
            await verify_channel.set_permissions(member, read_messages=False, send_messages=False)
        
        await asyncio.sleep(5)
        await success_msg.delete()
        
        print(f"Successfully verified user: {member.name}")
        
    except Exception as e:
        print(f"Error verifying user: {e}")

# Keep bot alive
@bot.event
async def on_error(event, *args, **kwargs):
    print(f"An error occurred: {event}")

# Run the bot
if __name__ == "__main__":
    try:
        bot.run(BOT_TOKEN)
    except Exception as e:
        print(f"Failed to start bot: {e}")

import logging
import signal
import sys
import requests
import json
from telegram import Update, ChatMember
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
)
import os
from flask import Flask
import threading

# Handle graceful shutdown
def signal_handler(signum, frame):
    logging.info("Bot shutting down gracefully...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Flask app to keep web service alive
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Bot is running successfully!"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Load environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CHANNEL_USERNAME = "@premiumlinkers"

# Function to call Gemini API using HTTP (100% working)
def call_gemini_api(user_input):
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": user_input
                        }
                    ]
                }
            ]
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text']
        
    except Exception as e:
        logging.error(f"Gemini API error: {str(e)}")
        return None

# Function to check channel membership
async def is_member(user_id: int, context: CallbackContext) -> bool:
    try:
        chat_member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return chat_member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logging.error(f"Error checking channel membership: {e}")
        return False

# Start command
async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name
    
    if await is_member(user_id, context):
        await update.message.reply_text(
            f"👋 Hello {user_name}!\n\n"
            f"✅ You are a member of {CHANNEL_USERNAME}\n"
            f"🎉 You can now start using the AI bot!\n\n"
            f"**Just send any message to chat with AI!**"
        )
    else:
        await update.message.reply_text(
            f"❌ Access Denied!\n\n"
            f"Hello {user_name}, to use this AI bot you need to join our channel first.\n\n"
            f"📢 **Please join:** {CHANNEL_USERNAME}\n"
            f"🔗 Join here: https://t.me/premiumlinkers\n\n"
            f"**After joining:**\n"
            f"1. Wait a few seconds\n"
            f"2. Send /start again\n"
            f"3. Start chatting with AI!"
        )

# Handle messages
async def handle_message(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    # Check channel membership for every message
    if not await is_member(user_id, context):
        await update.message.reply_text(
            f"❌ Please join {CHANNEL_USERNAME} to use this bot.\n\n"
            f"Join here: https://t.me/premiumlinkers\n\n"
            f"After joining, send /start again."
        )
        return

    user_input = update.message.text

    # Call Gemini API using HTTP
    reply = call_gemini_api(user_input)
    
    if reply:
        await update.message.reply_text(reply)
    else:
        await update.message.reply_text("Sorry, I couldn't generate a response. Please try again.")

# Set group command
async def set_group(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    
    # Check membership for group command too
    if not await is_member(user_id, context):
        await update.message.reply_text(
            f"❌ Please join {CHANNEL_USERNAME} to use this bot.\n\n"
            f"Join here: https://t.me/premiumlinkers"
        )
        return
        
    group_name = " ".join(context.args)

    if not group_name:
        await update.message.reply_text("Please provide a group name. Usage: /setgroup <group_name>")
        return

    await update.message.reply_text(f"Group '{group_name}' set. Please make the bot an admin in the group.")

# Main function
if __name__ == "__main__":
    logging.info("Starting bot...")
    try:
        # Start Flask server in a separate thread
        flask_thread = threading.Thread(target=run_flask)
        flask_thread.daemon = True
        flask_thread.start()

        # Start the bot
        application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
        logging.info("Bot application built successfully.")

        # Handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("setgroup", set_group))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        logging.info("Starting polling...")
        application.run_polling()
    except Exception as e:
        logging.error(f"Bot failed to start: {e}")
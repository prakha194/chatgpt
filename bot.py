import logging
from telegram import Update, ChatMember
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
)
import google.generativeai as genai
import os
from flask import Flask
import threading

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

# Initialize Gemini API
try:
    genai.configure(api_key=GEMINI_API_KEY)
    logging.info("Gemini API initialized successfully.")
except Exception as e:
    logging.error(f"Failed to initialize Gemini API: {e}")

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

    # Call Gemini API
    try:
        logging.info("Calling Gemini API...")
        model = genai.GenerativeModel('gemini-2.5-flash')  # Updated to 2.5-flash
        response = model.generate_content(user_input)
        logging.info(f"Gemini API response: {response.text}")
        reply = response.text
    except Exception as e:
        logging.error(f"Gemini API error: {e}")
        reply = "Sorry, I couldn't generate a response. Please try again."

    await update.message.reply_text(reply)

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
        import threading
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
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
)
import google.generativeai as genai
import os
from flask import Flask, request

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Load environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CHANNEL_USERNAME = "@premiumlinkers"  # Your channel username

# Initialize Gemini API
try:
    genai.configure(api_key=GEMINI_API_KEY)
    logging.info("Gemini API initialized successfully.")
except Exception as e:
    logging.error(f"Failed to initialize Gemini API: {e}")

# Function to check channel membership
async def is_member(user_id: int, context: CallbackContext) -> bool:
    try:
        # Use the getChatMember method to check if the user is a member of the channel
        chat_member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        # Return True if the user is a member, administrator, or creator
        return chat_member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logging.error(f"Error checking channel membership: {e}")
        return False

# Start command
async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if await is_member(user_id, context):
        await update.message.reply_text("Welcome! You can start using the bot.")
    else:
        await update.message.reply_text(
            f"Please join {CHANNEL_USERNAME} to use this bot. Join here: https://t.me/premiumlinkers"
        )

# Handle messages
async def handle_message(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    # Check channel membership
    if not await is_member(user_id, context):
        await update.message.reply_text(
            f"Please join {CHANNEL_USERNAME} to use this bot. Join here: https://t.me/premiumlinkers"
        )
        return

    user_input = update.message.text

    # Call Gemini API
    try:
        logging.info("Calling Gemini API...")
        model = genai.GenerativeModel('gemini-2.0-flash')  # Updated model name
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
    group_name = " ".join(context.args)

    if not group_name:
        await update.message.reply_text("Please provide a group name. Usage: /setgroup <group_name>")
        return

    # Add logic to make the bot an admin in the group
    await update.message.reply_text(f"Group '{group_name}' set. Please make the bot an admin in the group.")

# Flask app to keep the bot alive
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# Main function
if __name__ == "__main__":
    logging.info("Starting bot...")
    try:
        # Start Flask server in a separate thread
        import threading
        flask_thread = threading.Thread(target=run_flask)
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
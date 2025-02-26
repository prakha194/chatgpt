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

# Start command
async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    logging.info(f"User {user_id} started the bot.")
    await update.message.reply_text("Welcome! You can start using the bot.")

# Handle messages
async def handle_message(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_input = update.message.text
    logging.info(f"User {user_id} sent: {user_input}")

    try:
        logging.info("Calling Gemini API...")
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(user_input)
        logging.info(f"Gemini API response: {response.text}")
        reply = response.text
    except Exception as e:
        logging.error(f"Gemini API error: {e}")
        reply = "Sorry, I couldn't generate a response. Please try again."

    logging.info(f"Sending reply to user {user_id}: {reply}")
    await update.message.reply_text(reply)

# Main function
if __name__ == "__main__":
    logging.info("Starting bot...")
    try:
        application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
        logging.info("Bot application built successfully.")

        # Handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        logging.info("Starting polling...")
        application.run_polling()
    except Exception as e:
        logging.error(f"Bot failed to start: {e}")

import logging
from telegram import Update, ChatMember
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
)
import google.generativeai as genai  # For Gemini API
import os  # For environment variables

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

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Store user membership status
user_data = {}

# Check if user is a member of the channel
async def is_member(user_id: int, context: CallbackContext) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER]
    except Exception as e:
        logging.error(f"Error checking membership: {e}")
        return False

# Start command
async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if await is_member(user_id, context):
        await update.message.reply_text("Welcome! You can start using the bot.")
    else:
        await update.message.reply_text(f"Please join {CHANNEL_USERNAME} to use this bot.")

# Handle messages
async def handle_message(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    # Check channel membership
    if not await is_member(user_id, context):
        await update.message.reply_text(f"Please join {CHANNEL_USERNAME} to use this bot.")
        return

    user_input = update.message.text

    # Call Gemini API
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(user_input)
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

# Main function
if __name__ == "__main__":
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("setgroup", set_group))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot
    application.run_polling()

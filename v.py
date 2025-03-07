import os
import subprocess
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "7204456254:AAG_E_SfVryRcmYcgbRIqk5zE56RPYU1OTU"
CHANNEL_ID = "@seedhe_maut"

# Function to check if user is a member of the channel
async def is_user_joined(update: Update) -> bool:
    user_id = update.message.from_user.id
    try:
        chat_member = await update.message.bot.get_chat_member(CHANNEL_ID, user_id)
        return chat_member.status in ["member", "administrator", "creator"]
    except:
        return False

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_joined(update):
        await update.message.reply_text(f"आपको पहले हमारे चैनल से जुड़ना होगा: {CHANNEL_ID}")
        return
    await update.message.reply_text("बॉट में आपका स्वागत है! अब आप कमांड का उपयोग कर सकते हैं।")

# Host command
async def host(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_joined(update):
        await update.message.reply_text(f"आपको पहले हमारे चैनल से जुड़ना होगा: {CHANNEL_ID}")
        return
    await update.message.reply_text("Python फ़ाइल भेजें (example.py) जिसे होस्ट करना है।")

# Handle received Python files
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_joined(update):
        await update.message.reply_text(f"आपको पहले हमारे चैनल से जुड़ना होगा: {CHANNEL_ID}")
        return

    file = update.message.document
    if not file.file_name.endswith(".py"):
        await update.message.reply_text("कृपया केवल .py फ़ाइल भेजें!")
        return

    file_path = f"./{file.file_name}"
    new_file = await file.get_file()
    await new_file.download_to_drive(file_path)
    await update.message.reply_text(f"फ़ाइल '{file.file_name}' होस्ट की जा रही है...")

    # Running the Python file
    try:
        output = subprocess.run(["python3", file_path], capture_output=True, text=True)
        await update.message.reply_text(f"Execution Output:\n{output.stdout or 'No Output'}")
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

# Main function
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("host", host))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))  # ✅ सही सिंटैक्स

    app.run_polling()

if __name__ == "__main__":
    main()

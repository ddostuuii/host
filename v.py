import os
import subprocess
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

TOKEN = "8021272491:AAEfIJ0UK1esSQZeRsrVhKm4zImxmpyZD68"
CHANNEL_USERNAME = "seedhe_maut"  # अपने चैनल का यूजरनेम
CHANNEL_ID = -1002363906868  # चैनल की Numeric ID

# ✅ चैनल जॉइन चेक करने का फंक्शन
async def is_user_joined(update: Update) -> bool:
    user_id = update.message.from_user.id
    try:
        chat_member = await update.message.bot.get_chat_member(CHANNEL_ID, user_id)
        return chat_member.status in ["member", "administrator", "creator"]
    except:
        return False

# ✅ "Join Channel" का मैसेज भेजने का फंक्शन
async def send_join_message(update: Update) -> None:
    keyboard = [
        [InlineKeyboardButton("🔗 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME}")],
        [InlineKeyboardButton("✅ मैंने जॉइन कर लिया", callback_data="check_join")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🚀 पहले हमारे चैनल से जुड़ें ताकि बॉट का इस्तेमाल कर सकें!",
        reply_markup=reply_markup
    )

# ✅ स्टार्ट कमांड
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_joined(update):
        await send_join_message(update)
        return
    await update.message.reply_text("🎉 बॉट में आपका स्वागत है! अब आप कमांड का उपयोग कर सकते हैं।")

# ✅ "✅ मैंने जॉइन कर लिया" बटन का हैंडलर
async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    try:
        chat_member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        if chat_member.status in ["member", "administrator", "creator"]:
            await query.answer("✅ आपने चैनल जॉइन कर लिया है!", show_alert=True)
            await query.message.edit_text("🎉 बॉट में आपका स्वागत है! अब आप कमांड का उपयोग कर सकते हैं।")
        else:
            await query.answer("🚫 पहले चैनल जॉइन करें!", show_alert=True)
    except:
        await query.answer("🚫 पहले चैनल जॉइन करें!", show_alert=True)

# ✅ /host कमांड (अब सही मैसेज भेजेगा)
async def host(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_joined(update):
        await send_join_message(update)
        return

    await update.message.reply_text("📂 **Put your Python file (.py) here.**", parse_mode="Markdown")

# ✅ Python फ़ाइल होस्ट करने का फंक्शन
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_joined(update):
        await send_join_message(update)
        return

    file = update.message.document
    if not file.file_name.endswith(".py"):
        await update.message.reply_text("⚠️ **Please send a valid .py file!**", parse_mode="Markdown")
        return

    file_path = f"./{file.file_name}"
    new_file = await file.get_file()
    await new_file.download_to_drive(file_path)
    await update.message.reply_text(f"📂 **File '{file.file_name}' is being hosted...**", parse_mode="Markdown")

    # ✅ Python फ़ाइल रन करना
    try:
        output = subprocess.run(["python3", file_path], capture_output=True, text=True)
        stdout = output.stdout.strip() if output.stdout else "No Output"
        stderr = output.stderr.strip() if output.stderr else "No Errors"

        result_message = f"✅ **Execution Output:**\n```{stdout}```\n❌ **Errors:**\n```{stderr}```"
        await update.message.reply_text(result_message, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ **Error:** `{str(e)}`", parse_mode="Markdown")

# ✅ बॉट स्टार्ट फंक्शन
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("host", host))  # ✅ /host फिक्स किया
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))  # ✅ फ़ाइल होस्टिंग फिक्स
    app.add_handler(CallbackQueryHandler(check_join, pattern="check_join"))

    app.run_polling()

if __name__ == "__main__":
    main()

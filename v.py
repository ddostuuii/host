import os
import subprocess
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

TOKEN = "7204456254:AAG_E_SfVryRcmYcgbRIqk5zE56RPYU1OTU"
CHANNEL_USERNAME = "seedhe_maut"  # अपने चैनल का यूजरनेम डालें (जैसे @seedhe_maut)
CHANNEL_ID = -1002363906868  # चैनल ID

# चैनल जॉइन चेक करने का फंक्शन
async def is_user_joined(update: Update) -> bool:
    if CHANNEL_ID is None:
        return False

    user_id = update.message.from_user.id
    try:
        chat_member = await update.message.bot.get_chat_member(CHANNEL_ID, user_id)
        return chat_member.status in ["member", "administrator", "creator"]
    except:
        return False

# स्टार्ट कमांड
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("🔗 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME}")],
        [InlineKeyboardButton("✅ मैंने जॉइन कर लिया", callback_data="check_join")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if not await is_user_joined(update):
        await update.message.reply_text(
            "🚀 पहले हमारे चैनल से जुड़ें ताकि बॉट का इस्तेमाल कर सकें!",
            reply_markup=reply_markup
        )
        return

    await update.message.reply_text("🎉 बॉट में आपका स्वागत है! अब आप कमांड का उपयोग कर सकते हैं।")

# "✅ मैंने जॉइन कर लिया" बटन का हैंडलर
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

# /host कमांड
async def host(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_joined(update):
        keyboard = [
            [InlineKeyboardButton("🔗 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME}")],
            [InlineKeyboardButton("✅ मैंने जॉइन कर लिया", callback_data="check_join")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "🚀 पहले हमारे चैनल से जुड़ें ताकि बॉट का इस्तेमाल कर सकें!",
            reply_markup=reply_markup
        )
        return

    await update.message.reply_text("📂 Python फ़ाइल भेजें जिसे होस्ट करना है।")

# Python फ़ाइल होस्ट करने का फंक्शन
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_joined(update):
        keyboard = [
            [InlineKeyboardButton("🔗 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME}")],
            [InlineKeyboardButton("✅ मैंने जॉइन कर लिया", callback_data="check_join")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "🚀 पहले हमारे चैनल से जुड़ें ताकि बॉट का इस्तेमाल कर सकें!",
            reply_markup=reply_markup
        )
        return

    file = update.message.document
    if not file.file_name.endswith(".py"):
        await update.message.reply_text("⚠️ कृपया केवल .py फ़ाइल भेजें!")
        return

    file_path = f"./{file.file_name}"
    new_file = await file.get_file()
    await new_file.download_to_drive(file_path)
    await update.message.reply_text(f"📂 फ़ाइल '{file.file_name}' होस्ट की जा रही है...")

    # Python फ़ाइल रन करना
    try:
        output = subprocess.run(["python3", file_path], capture_output=True, text=True)
        await update.message.reply_text(f"✅ Execution Output:\n{output.stdout or 'No Output'}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

# बॉट स्टार्ट फंक्शन
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("host", host))  # ✅ /host कमांड ऐड किया
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))  # ✅ फ़ाइल होस्टिंग सपोर्ट
    app.add_handler(CallbackQueryHandler(check_join, pattern="check_join"))

    app.run_polling()

if __name__ == "__main__":
    main()

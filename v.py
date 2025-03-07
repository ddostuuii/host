from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

TOKEN = "7204456254:AAG_E_SfVryRcmYcgbRIqk5zE56RPYU1OTU"
CHANNEL_USERNAME = "@seedhe_maut"  # अपने चैनल का यूजरनेम डालें (जैसे @seedhe_maut)
CHANNEL_ID = None  # चैनल ID ऑटोमैटिकली निकाली जाएगी

# चैनल की ID निकालने का फंक्शन
async def get_channel_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CHANNEL_ID
    chat = await context.bot.get_chat(CHANNEL_USERNAME)
    CHANNEL_ID = chat.id
    await update.message.reply_text(f"✅ Channel ID: `{CHANNEL_ID}`", parse_mode="Markdown")

# चैनल जॉइन चेक करने का फंक्शन
async def is_user_joined(update: Update) -> bool:
    if CHANNEL_ID is None:
        return False  # अगर चैनल ID नहीं मिली तो False भेजो

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

# बॉट स्टार्ट फंक्शन
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("getid", get_channel_id))  # ✅ यह कमांड चैनल की ID निकालेगा
    app.add_handler(CallbackQueryHandler(check_join, pattern="check_join"))

    app.run_polling()

if __name__ == "__main__":
    main()

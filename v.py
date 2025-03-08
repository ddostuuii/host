import os
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

TOKEN = "8024990900:AAEVjj9q-b3SIEakZPfGOnq03rSNwQWniDU"
CHANNEL_USERNAME = "seedhe_maut"
CHANNEL_ID = -1002363906868  
active_users = set()  # सिर्फ उन्हीं यूज़र्स को फाइल होस्ट करने देना है जो /host भेजें

# ✅ चैनल जॉइन चेक करने का फंक्शन
async def is_user_joined(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        chat_member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return chat_member.status in ["member", "administrator", "creator"]
    except:
        return False

# ✅ Join Message
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

# ✅ /start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    if not await is_user_joined(user_id, context):
        await send_join_message(update)
        return

    await update.message.reply_text("🎉 बॉट में आपका स्वागत है! `/host` कमांड भेजें और फिर `.py` फाइल अपलोड करें।")

# ✅ /host Command
async def host(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    if not await is_user_joined(user_id, context):
        await send_join_message(update)
        return

    active_users.add(user_id)  # /host करने वाले यूजर को एक्टिव लिस्ट में ऐड करो
    await update.message.reply_text("📂 **अब आप `.py` फाइल भेज सकते हैं, बॉट उसे होस्ट करेगा।**", parse_mode="Markdown")

# ✅ Python फ़ाइल होस्ट करने का फंक्शन
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    if not await is_user_joined(user_id, context):
        await send_join_message(update)
        return

    if user_id not in active_users:
        await update.message.reply_text("⚠️ **Please use /host first!**", parse_mode="Markdown")
        return

    file = update.message.document
    if not file.file_name.endswith(".py"):
        await update.message.reply_text("⚠️ **Please send a valid .py file!**", parse_mode="Markdown")
        return

    file_path = f"./{file.file_name}"
    new_file = await file.get_file()
    await new_file.download_to_drive(file_path)
    await update.message.reply_text(f"📂 **File '{file.file_name}' is being hosted...**", parse_mode="Markdown")

    # ✅ Python फ़ाइल रन करना (async mode में)
    asyncio.create_task(run_python_script(update, file_path))

# ✅ Python स्क्रिप्ट को async रन करने का फंक्शन
async def run_python_script(update: Update, file_path: str):
    try:
        process = await asyncio.create_subprocess_exec(
            "python3", file_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()
        stdout = stdout.decode().strip() or "No Output"
        stderr = stderr.decode().strip() or "No Errors"

        result_message = f"✅ **Execution Output:**\n```{stdout}```\n❌ **Errors:**\n```{stderr}```"
        await update.message.reply_text(result_message, parse_mode="Markdown")

    except asyncio.TimeoutError:
        await update.message.reply_text("❌ **Error:** Execution Timed Out!", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ **Error:** `{str(e)}`", parse_mode="Markdown")

# ✅ "✅ मैंने जॉइन कर लिया" बटन का हैंडलर
async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    try:
        chat_member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        if chat_member.status in ["member", "administrator", "creator"]:
            await query.answer("✅ आपने चैनल जॉइन कर लिया है!", show_alert=True)
            await query.message.edit_text("🎉 बॉट में आपका स्वागत है! `/host` कमांड भेजें और फिर `.py` फाइल अपलोड करें।")
        else:
            await query.answer("🚫 पहले चैनल जॉइन करें!", show_alert=True)
    except:
        await query.answer("🚫 पहले चैनल जॉइन करें!", show_alert=True)

# ✅ बॉट स्टार्ट फंक्शन
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("host", host))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))  
    app.add_handler(CallbackQueryHandler(check_join, pattern="check_join"))

    app.run_polling()

if __name__ == "__main__":
    main()

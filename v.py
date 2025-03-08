import os
import asyncio
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ✅ Bot Token & Channel Information
TOKEN = "8024990900:AAEVjj9q-b3SIEakZPfGOnq03rSNwQWniDU"
CHANNEL_USERNAME = "seedhe_maut"
CHANNEL_ID = -1002363906868

# ✅ एडमिन्स की लिस्ट (डायरेक्ट जोड़ें)
def load_admins():
    try:
        with open("admins.txt", "r") as f:
            return {int(line.strip()) for line in f if line.strip().isdigit()}
    except FileNotFoundError:
        return {7017469802, 987654321}  # Default Admins

admins = load_admins()
approved_users = set()  
normal_user_data = {}  
active_users = set()  
user_files = {}  
running_processes = {}  

# ✅ चैनल जॉइन चेक करने का फंक्शन
async def is_user_joined(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        chat_member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return chat_member.status in ["member", "administrator", "creator"]
    except:
        return False

# ✅ स्क्रिप्ट होस्टिंग लिमिट चेक
def can_host_script(user_id: int) -> bool:
    if user_id in admins or user_id in approved_users:
        return True

    if user_id not in normal_user_data:
        normal_user_data[user_id] = {"count": 0, "start_time": 0}

    user_info = normal_user_data[user_id]
    if user_info["count"] >= 2:
        return False

    if time.time() - user_info["start_time"] >= 24 * 3600:
        user_info["count"] = 0  
        user_info["start_time"] = 0  

    if user_info["start_time"] and time.time() - user_info["start_time"] < 20 * 3600:
        return True
    elif user_info["start_time"] and time.time() - user_info["start_time"] < 24 * 3600:
        return False
    else:
        return True

# ✅ /start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if not await is_user_joined(user_id, context):
        await update.message.reply_text("🚫 पहले चैनल जॉइन करें!")
        return
    await update.message.reply_text("🎉 बॉट में आपका स्वागत है! `/host` कमांड भेजें और फिर `.py` फाइल अपलोड करें।")

# ✅ /host Command
async def host(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if not await is_user_joined(user_id, context):
        await update.message.reply_text("🚫 पहले चैनल जॉइन करें!")
        return

    if not can_host_script(user_id):
        await update.message.reply_text("⏳ **आप 4 घंटे बाद फिर से स्क्रिप्ट होस्ट कर सकते हैं।**", parse_mode="Markdown")
        return

    if user_id not in admins and user_id not in approved_users:
        if user_id not in normal_user_data:
            normal_user_data[user_id] = {"count": 0, "start_time": 0}
        normal_user_data[user_id]["count"] += 1
        if normal_user_data[user_id]["count"] == 1:
            normal_user_data[user_id]["start_time"] = time.time()

    active_users.add(user_id)
    await update.message.reply_text("📂 **अब आप `.py` फाइल भेज सकते हैं, बॉट उसे होस्ट करेगा।**", parse_mode="Markdown")

# ✅ Python फ़ाइल होस्ट करने का फंक्शन
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if not await is_user_joined(user_id, context):
        await update.message.reply_text("🚫 पहले चैनल जॉइन करें!")
        return

    if user_id not in active_users:
        await update.message.reply_text("⚠️ **Please use /host first!**", parse_mode="Markdown")
        return

    file = update.message.document
    if not file.file_name.endswith(".py"):
        await update.message.reply_text("⚠️ **Please send a valid .py file!**", parse_mode="Markdown")
        return

    file_path = f"./hosted_scripts/{file.file_name}"
    os.makedirs("hosted_scripts", exist_ok=True)  
    new_file = await file.get_file()
    await new_file.download_to_drive(file_path)

    user_files[user_id] = file_path  
    await update.message.reply_text(f"📂 **File '{file.file_name}' is being hosted...**", parse_mode="Markdown")

    asyncio.create_task(run_python_script(update, file_path, user_id))

# ✅ Python स्क्रिप्ट रन करने का फंक्शन
async def run_python_script(update: Update, file_path: str, user_id: int):
    try:
        process = await asyncio.create_subprocess_exec(
            "python3", file_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        running_processes[user_id] = process  

        stdout_lines = []
        stderr_lines = []

        while True:
            stdout_line = await process.stdout.readline()
            stderr_line = await process.stderr.readline()

            if not stdout_line and not stderr_line:
                break

            if stdout_line:
                stdout_lines.append(stdout_line.decode().strip())

            if stderr_line:
                stderr_lines.append(stderr_line.decode().strip())

        stdout = "\n".join(stdout_lines) or "No Output"
        stderr = "\n".join(stderr_lines) or "No Errors"

        result_message = f"✅ **Execution Output:**\n```{stdout}```\n❌ **Errors:**\n```{stderr}```"
        await update.message.reply_text(result_message, parse_mode="Markdown")

        del running_processes[user_id]

    except Exception as e:
        await update.message.reply_text(f"❌ **Error:** `{str(e)}`", parse_mode="Markdown")

# ✅ /add_admin Command
async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in admins:
        await update.message.reply_text("🚫 **आपको अनुमति नहीं है!**", parse_mode="Markdown")
        return

    if not context.args:
        await update.message.reply_text("⚠️ **Usage:** `/add_admin <user_id>`", parse_mode="Markdown")
        return

    try:
        user_id = int(context.args[0])
        admins.add(user_id)
        with open("admins.txt", "a") as f:
            f.write(f"{user_id}\n")  

        await update.message.reply_text(f"✅ **User {user_id} is now an admin!**", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("⚠️ **Invalid user ID!**", parse_mode="Markdown")

# ✅ बॉट स्टार्ट फंक्शन
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("host", host))
    app.add_handler(CommandHandler("add_admin", add_admin))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    app.run_polling()

if __name__ == "__main__":
    main()

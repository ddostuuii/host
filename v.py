import os
import asyncio
import time
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ✅ बॉट टोकन और चैनल डिटेल्स लोड करना
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "-1002363906868"))
ADMIN = int(os.getenv("ADMIN_ID", "7017469802"))

# ✅ एडमिन और अप्रूव्ड यूज़र फ़ाइल लोड करना
admins_file = "admins.txt"
approved_users_file = "approved_users.txt"

def load_users(filename):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return set(map(int, f.read().splitlines()))
    return set()

admins = load_users(admins_file)
admins.add(ADMIN)
approved_users = load_users(approved_users_file)

# ✅ नॉर्मल यूज़र डेटा (लिमिट ट्रैकिंग)
normal_user_data = {}
active_users = set()
user_files = {}
running_processes = {}

# ✅ एडमिन सेव करने का फंक्शन
def save_users(filename, user_set):
    with open(filename, "w") as f:
        f.write("\n".join(map(str, user_set)))

# ✅ /add_admin Command
async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id not in admins:
        await update.message.reply_text("🚫 **सिर्फ एडमिन नए एडमिन जोड़ सकते हैं!**", parse_mode="Markdown")
        return

    if not context.args:
        await update.message.reply_text("⚠️ **कृपया एक यूज़र आईडी दें!**\nउदाहरण: `/add_admin 123456789`", parse_mode="Markdown")
        return

    try:
        new_admin = int(context.args[0])
        if new_admin in admins:
            await update.message.reply_text("✅ **यह यूज़र पहले से ही एडमिन है!**", parse_mode="Markdown")
        else:
            admins.add(new_admin)
            save_users(admins_file, admins)
            await update.message.reply_text(f"✅ **यूज़र {new_admin} को एडमिन बना दिया गया है!**", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("❌ **अमान्य यूज़र आईडी! कृपया सही संख्या दें।**", parse_mode="Markdown")

# ✅ /stop_host Command
async def stop_host(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    if user_id not in running_processes:
        await update.message.reply_text("⚠️ **आपके लिए कोई भी स्क्रिप्ट चल नहीं रही!**", parse_mode="Markdown")
        return

    process = running_processes[user_id]
    process.terminate()  # ✅ Script stop करें
    del running_processes[user_id]

    if user_id in user_files:
        os.remove(user_files[user_id])  # ✅ Delete script file
        del user_files[user_id]

    await update.message.reply_text("🛑 **आपकी होस्ट की गई स्क्रिप्ट रोक दी गई है!**", parse_mode="Markdown")

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

    now = time.time()

    if user_id not in normal_user_data:
        normal_user_data[user_id] = {"count": 0, "start_time": now}

    user_info = normal_user_data[user_id]

    if user_info["count"] >= 2:
        if now - user_info["start_time"] >= 24 * 3600:
            user_info["count"] = 0  
            user_info["start_time"] = now  
        else:
            return False

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

    active_users.add(user_id)
    await update.message.reply_text("📂 **अब आप `.py` फाइल भेज सकते हैं, बॉट उसे होस्ट करेगा।**", parse_mode="Markdown")

# ✅ 20 घंटे बाद स्क्रिप्ट ऑटो स्टॉप करने का फंक्शन
async def stop_script_after_timeout(user_id: int, file_path: str, context: ContextTypes.DEFAULT_TYPE):
    await asyncio.sleep(20 * 3600)

    if user_id in running_processes:
        process = running_processes[user_id]
        process.terminate()
        del running_processes[user_id]

        if user_id in user_files:
            os.remove(user_files[user_id])
            del user_files[user_id]

        await context.bot.send_message(user_id, f"⏳ **Script '{file_path}' has been stopped after 20 hours.**")

# ✅ Python फ़ाइल होस्ट करने का फंक्शन
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id not in active_users:
        await update.message.reply_text("⚠️ **कृपया पहले /host कमांड भेजें!**", parse_mode="Markdown")
        return

    if not can_host_script(user_id):
        await update.message.reply_text("⏳ **आप 4 घंटे बाद फिर से स्क्रिप्ट होस्ट कर सकते हैं।**", parse_mode="Markdown")
        return

    file = update.message.document
    if not file.file_name.endswith(".py"):
        await update.message.reply_text("⚠️ **Please send a valid .py file!**", parse_mode="Markdown")
        return

    file_path = f"./hosted_scripts/{file.file_name}"
    os.makedirs("hosted_scripts", exist_ok=True)
    
    try:
        new_file = await file.get_file()
        await new_file.download_to_drive(file_path)
    except:
        await update.message.reply_text("❌ **फ़ाइल डाउनलोड करने में समस्या आई!**")
        return

    user_files[user_id] = file_path

    normal_user_data[user_id]["count"] += 1

    await update.message.reply_text(f"📂 **File '{file.file_name}' is being hosted...**", parse_mode="Markdown")

    asyncio.create_task(stop_script_after_timeout(user_id, file_path, context))
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

# ✅ बॉट स्टार्ट फंक्शन
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("stop_host", stop_host))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("host", host))
    app.add_handler(CommandHandler("add_admin", add_admin))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    app.run_polling()

if __name__ == "__main__":
    main()

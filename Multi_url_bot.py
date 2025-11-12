# filename: multi_url_bot_admin.py
# pip install python-telegram-bot==20.7

import os
import sqlite3
import uuid
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# -------------------------------
# BOT TOKEN
# -------------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN") or "8519364326:AAGug-4zuw6-77AzMo3KqWySju-IuXYAALk"

# -------------------------------
# ADMIN LIST (👉 yaha apna Telegram user ID daalo)
# -------------------------------
ADMINS = [7681308594, 8244432792]  # 👈 apna Telegram user ID yaha likh

# -------------------------------
# Database Setup
# -------------------------------
conn = sqlite3.connect("multi_url_bot.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS links (
    short_id TEXT PRIMARY KEY,
    content TEXT,
    clicks INTEGER DEFAULT 0,
    owner_id INTEGER
)
""")
conn.commit()

# -------------------------------
# Helper
# -------------------------------
def is_admin(user_id: int) -> bool:
    return user_id in ADMINS

# -------------------------------
# Functions
# -------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    args = context.args
    user_id = update.message.from_user.id

    # Link click (public allowed)
    if args:
        short_id = args[0]
        cursor.execute("SELECT content, clicks FROM links WHERE short_id = ?", (short_id,))
        row = cursor.fetchone()

        if not row:
            await update.message.reply_text("❌ Invalid or expired link.")
            return

        content, clicks = row
        cursor.execute("UPDATE links SET clicks = clicks + 1 WHERE short_id = ?", (short_id,))
        conn.commit()

        await update.message.reply_text(f"📩 Here are your links:\n\n{content}")
        return

    # Check admin
    if not is_admin(user_id):
        await update.message.reply_text("🚫 You are not authorized to use this bot.")
        return

    await update.message.reply_text(
        "👋 Welcome Admin!\n\nSend me your text and URLs like this:\n\n"
        "Example:\nGoogle\nhttps://google.com\n\nYouTube\nhttps://youtube.com"
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text with multiple lines"""
    user_id = update.message.from_user.id
    if not is_admin(user_id):
        await update.message.reply_text("🚫 You are not authorized to create links.")
        return

    text = update.message.text.strip()
    short_id = str(uuid.uuid4())[:8]

    cursor.execute(
        "INSERT INTO links (short_id, content, owner_id) VALUES (?, ?, ?)",
        (short_id, text, user_id),
    )
    conn.commit()

    short_url = f"https://t.me/{(await context.bot.get_me()).username}?start={short_id}"

    await update.message.reply_text(
        f"✅ Short link created:\n{short_url}\n\n"
        "📊 Use /stats to check your links."
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user stats"""
    user_id = update.message.from_user.id
    if not is_admin(user_id):
        await update.message.reply_text("🚫 You are not authorized to view stats.")
        return

    cursor.execute("SELECT short_id, clicks FROM links WHERE owner_id = ?", (user_id,))
    data = cursor.fetchall()

    if not data:
        await update.message.reply_text("ℹ️ You haven’t created any links yet.")
        return

    msg = "📈 Your Links:\n\n"
    for short_id, clicks in data:
        msg += f"🔗 `{short_id}` — {clicks} clicks\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

# -------------------------------
# Main
# -------------------------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("🤖 Admin-only Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

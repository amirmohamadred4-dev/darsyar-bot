from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from .config import BOT_TOKEN
from .db import init_db


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام 👋\n"
        "به مشاور درسی یازدهم خوش اومدی! 📚\n\n"
        "برای شروع روی /register بزن."
    )


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📝 ثبت‌نام در نسخه‌ی بعدی فعال می‌شود."
    )


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN تنظیم نشده است.")

    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("register", register))

    print("🤖 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()

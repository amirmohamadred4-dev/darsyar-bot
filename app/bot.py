from telegram import Update
from telegram.ext import Application, CommandHandler

from .config import BOT_TOKEN
from .db import init_db
from .seed import seed_database
from .handlers.user import get_user_handlers


async def start(update: Update, context):
    await update.message.reply_text(
        "سلام 👋\n"
        "به مشاور درسی یازدهم خوش اومدی! 📚\n\n"
        "برای شروع روی /register بزن."
    )


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN تنظیم نشده است.")

    init_db()
    seed_database()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    for handler in get_user_handlers():
        app.add_handler(handler)

    print("🤖 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()

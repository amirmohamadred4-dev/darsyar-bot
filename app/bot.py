from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from .config import BOT_TOKEN
from .db import init_db, session, User
from .handlers.user import get_user_handlers


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id

    db = session()
    try:
        user = (
            db.query(User)
            .filter(User.telegram_id == telegram_id)
            .first()
        )
    finally:
        db.close()

    if user:
        await update.effective_message.reply_text(
            f"سلام {user.name} 👋\n\n"
            "📚 به مشاور درسی یازدهم خوش اومدی!\n"
            "از منوی زیر انتخاب کن:",
            reply_markup=None,
        )

        # نمایش منوی اصلی
        from .handlers.user import main_menu

        await update.effective_message.reply_text(
            "📚 منوی اصلی:",
            reply_markup=main_menu(),
        )
        return

    await update.effective_message.reply_text(
        "سلام 👋\n"
        "به مشاور درسی یازدهم خوش اومدی! 📚\n\n"
        "برای شروع ثبت‌نام کن:",
        reply_markup=None,
    )

    from .handlers.user import start_register
    await start_register(update, context)


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN تنظیم نشده است.")

    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    for handler in get_user_handlers():
        app.add_handler(handler)

    print("🤖 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from .config import BOT_TOKEN
from .db import init_db, session, User
from .seed import seed_database
from .handlers.user import get_user_handlers, main_menu, start_register


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id

    db = session()

    try:
        user = (
            db.query(User)
            .filter(User.telegram_id == telegram_id)
            .first()
        )

        if user:
            name = user.name
            grade = user.grade
            field = user.field
        else:
            name = None
            grade = None
            field = None

    finally:
        db.close()

    # کاربر قبلاً ثبت‌نام کرده
    if name:
        context.user_data.clear()

        await update.effective_message.reply_text(
            f"سلام {name} 👋\n\n"
            "📚 خوش اومدی!\n\n"
            f"🎓 پایه: {grade}\n"
            f"📖 رشته: {field}\n\n"
            "از منوی زیر استفاده کن:",
            reply_markup=main_menu(),
        )
        return

    # کاربر جدید
    await start_register(update, context)


def main():

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN تنظیم نشده است."
        )

    # ساخت جداول
    init_db()

    # وارد کردن دبیرها و برنامه‌ها
    seed_database()

    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    for handler in get_user_handlers():
        app.add_handler(handler)

    print("🤖 Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()

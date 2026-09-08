from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from ..config import FIELDS, GRADE
from ..db import session, User


def main_menu():
    keyboard = [
        [
            InlineKeyboardButton("🏠 صفحه اصلی", callback_data="home"),
            InlineKeyboardButton("📅 برنامه امروز", callback_data="today"),
        ],
        [
            InlineKeyboardButton("📆 برنامه هفتگی", callback_data="weekly"),
        ],
        [
            InlineKeyboardButton("👨‍🏫 دبیرهای من", callback_data="teachers"),
            InlineKeyboardButton("📊 عملکرد من", callback_data="performance"),
        ],
        [
            InlineKeyboardButton("🔔 تنظیمات یادآوری", callback_data="reminders"),
        ],
        [
            InlineKeyboardButton("⚙️ تنظیمات", callback_data="settings"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "📚 منوی اصلی\n\n"
        "از گزینه‌های زیر استفاده کن:",
        reply_markup=main_menu(),
    )


async def start_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["registering"] = True

    await update.effective_message.reply_text(
        "📝 ثبت‌نام\n\n"
        "لطفاً نامت رو وارد کن:"
    )


async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("registering"):
        return

    name = update.message.text.strip()

    if len(name) < 2:
        await update.message.reply_text(
            "❌ نام واردشده کوتاهه.\n"
            "لطفاً نامت رو دوباره وارد کن:"
        )
        return

    context.user_data["name"] = name

    keyboard = [
        [InlineKeyboardButton(GRADE, callback_data="grade:11")]
    ]

    await update.message.reply_text(
        "🎓 پایه تحصیلی:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "home":
        await query.edit_message_text(
            "📚 منوی اصلی\n\n"
            "از گزینه‌های زیر استفاده کن:",
            reply_markup=main_menu(),
        )

    elif data == "grade:11":
        keyboard = [
            [
                InlineKeyboardButton(
                    field,
                    callback_data=f"field:{field}"
                )
            ]
            for field in FIELDS
        ]

        await query.edit_message_text(
            "📚 رشته‌ات رو انتخاب کن:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif data.startswith("field:"):
        field = data.split(":", 1)[1]

        name = context.user_data.get("name")

        if not name:
            await query.edit_message_text(
                "❌ اطلاعات ثبت‌نام پیدا نشد.\n"
                "دوباره /register رو بزن."
            )
            return

        db = session()

        try:
            telegram_id = update.effective_user.id

            user = (
                db.query(User)
                .filter(User.telegram_id == telegram_id)
                .first()
            )

            if user:
                user.name = name
                user.grade = GRADE
                user.field = field
            else:
                user = User(
                    telegram_id=telegram_id,
                    name=name,
                    grade=GRADE,
                    field=field,
                )
                db.add(user)

            db.commit()

        finally:
            db.close()

        context.user_data["registering"] = False

        await query.edit_message_text(
            f"🎉 ثبت‌نام با موفقیت انجام شد!\n\n"
            f"👤 نام: {name}\n"
            f"🎓 پایه: {GRADE}\n"
            f"📚 رشته: {field}\n\n"
            "حالا می‌تونیم دبیرهای هر درس رو برات انتخاب کنیم.",
            reply_markup=main_menu(),
        )

    elif data == "today":
        await query.edit_message_text(
            "📅 برنامه امروز\n\n"
            "این بخش رو در مرحله بعد فعال می‌کنیم."
        )

    elif data == "weekly":
        await query.edit_message_text(
            "📆 برنامه هفتگی\n\n"
            "این بخش رو در مرحله بعد فعال می‌کنیم."
        )

    elif data == "teachers":
        await query.edit_message_text(
            "👨‍🏫 دبیرهای من\n\n"
            "این بخش رو در مرحله بعد فعال می‌کنیم."
        )

    elif data == "performance":
        await query.edit_message_text(
            "📊 عملکرد من\n\n"
            "هنوز اطلاعات عملکردی ثبت نشده."
        )

    elif data == "reminders":
        await query.edit_message_text(
            "🔔 تنظیمات یادآوری\n\n"
            "این بخش رو در مرحله بعد فعال می‌کنیم."
        )

    elif data == "settings":
        await query.edit_message_text(
            "⚙️ تنظیمات\n\n"
            "این بخش رو در مرحله بعد فعال می‌کنیم."
        )


def get_user_handlers():
    return [
        CommandHandler("menu", show_menu),
        CommandHandler("register", start_register),

        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receive_name,
        ),

        CallbackQueryHandler(button_handler),
    ]

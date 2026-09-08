from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from ..config import FIELDS


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
    keyboard = [
        [InlineKeyboardButton(field, callback_data=f"field:{field}")]
        for field in FIELDS
    ]

    await update.effective_message.reply_text(
        "🎓 رشته‌ات رو انتخاب کن:",
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

    elif data.startswith("field:"):
        field = data.split(":", 1)[1]

        await query.edit_message_text(
            f"✅ رشته انتخاب شد: {field}\n\n"
            "حالا انتخاب دبیرها رو در مرحله بعد اضافه می‌کنیم."
        )

    elif data == "today":
        await query.edit_message_text(
            "📅 برنامه امروز\n\n"
            "هنوز برنامه امروز به منو متصل نشده."
        )

    elif data == "weekly":
        await query.edit_message_text(
            "📆 برنامه هفتگی\n\n"
            "این بخش در مرحله بعد تکمیل می‌شود."
        )

    elif data == "teachers":
        await query.edit_message_text(
            "👨‍🏫 دبیرهای من\n\n"
            "این بخش در مرحله بعد تکمیل می‌شود."
        )

    elif data == "performance":
        await query.edit_message_text(
            "📊 عملکرد من\n\n"
            "هنوز داده‌ای برای نمایش وجود ندارد."
        )

    elif data == "reminders":
        await query.edit_message_text(
            "🔔 تنظیمات یادآوری\n\n"
            "این بخش در مرحله بعد فعال می‌شود."
        )

    elif data == "settings":
        await query.edit_message_text(
            "⚙️ تنظیمات\n\n"
            "این بخش در مرحله بعد فعال می‌شود."
        )


def get_user_handlers():
    from telegram.ext import CommandHandler, CallbackQueryHandler

    return [
        CommandHandler("menu", show_menu),
        CommandHandler("register", start_register),
        CallbackQueryHandler(button_handler),
    ]

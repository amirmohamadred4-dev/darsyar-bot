from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from .config import ADMIN_ID
from .db import session, User


def admin_menu():
    keyboard = [
        [
            InlineKeyboardButton("📊 آمار ربات", callback_data="admin:stats"),
            InlineKeyboardButton("👥 کاربران", callback_data="admin:users"),
        ],
        [
            InlineKeyboardButton("👨‍🏫 دبیرها", callback_data="admin:teachers"),
            InlineKeyboardButton("📅 برنامه کلاس‌ها", callback_data="admin:classes"),
        ],
        [
            InlineKeyboardButton("📢 پیام همگانی", callback_data="admin:broadcast"),
        ],
        [
            InlineKeyboardButton("📈 گزارش‌ها", callback_data="admin:reports"),
            InlineKeyboardButton("🔔 یادآوری‌ها", callback_data="admin:reminders"),
        ],
        [
            InlineKeyboardButton("🚨 وضعیت سیستم", callback_data="admin:system"),
        ],
        [
            InlineKeyboardButton("🚪 خروج", callback_data="admin:exit"),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        await update.effective_message.reply_text(
            "⛔ دسترسی غیرمجاز."
        )
        return

    await update.effective_message.reply_text(
        "👑 پنل مدیریت\n\n"
        "به بخش مدیریت ربات خوش اومدی.\n"
        "یکی از گزینه‌های زیر رو انتخاب کن:",
        reply_markup=admin_menu(),
    )


async def admin_button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if update.effective_user.id != ADMIN_ID:
        await query.answer(
            "⛔ دسترسی غیرمجاز",
            show_alert=True,
        )
        return

    await query.answer()

    data = query.data

    if data == "admin:stats":

        db = session()

        try:
            total_users = db.query(User).count()

            experimental = (
                db.query(User)
                .filter(User.field == "تجربی")
                .count()
            )

            mathematics = (
                db.query(User)
                .filter(User.field == "ریاضی")
                .count()
            )

            humanities = (
                db.query(User)
                .filter(User.field == "انسانی")
                .count()
            )

        finally:
            db.close()

        await query.edit_message_text(
            "📊 آمار ربات\n\n"
            f"👥 کل کاربران: {total_users}\n\n"
            f"🧪 تجربی: {experimental}\n"
            f"📐 ریاضی: {mathematics}\n"
            f"📚 انسانی: {humanities}",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 پنل مدیریت",
                        callback_data="admin:back"
                    )
                ]
            ]),
        )

    elif data == "admin:users":

        db = session()

        try:
            total_users = db.query(User).count()
        finally:
            db.close()

        await query.edit_message_text(
            "👥 مدیریت کاربران\n\n"
            f"تعداد کاربران ثبت‌نام‌شده: {total_users}\n\n"
            "در مرحله بعد جستجو و مشاهده اطلاعات کاربران "
            "را هم به این بخش اضافه می‌کنیم.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 پنل مدیریت",
                        callback_data="admin:back"
                    )
                ]
            ]),
        )

    elif data == "admin:teachers":

        await query.edit_message_text(
            "👨‍🏫 مدیریت دبیرها\n\n"
            "از این بخش می‌تونی دبیرهای ربات رو مدیریت کنی.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 پنل مدیریت",
                        callback_data="admin:back"
                    )
                ]
            ]),
        )

    elif data == "admin:classes":

        await query.edit_message_text(
            "📅 مدیریت برنامه کلاس‌ها\n\n"
            "برنامه کلاس‌ها از دیتابیس مدیریت می‌شود.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 پنل مدیریت",
                        callback_data="admin:back"
                    )
                ]
            ]),
        )

    elif data == "admin:broadcast":

        await query.edit_message_text(
            "📢 پیام همگانی\n\n"
            "در مرحله بعد ارسال پیام همگانی به کاربران "
            "را اضافه می‌کنیم.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 پنل مدیریت",
                        callback_data="admin:back"
                    )
                ]
            ]),
        )

    elif data == "admin:reports":

        await query.edit_message_text(
            "📈 گزارش‌ها\n\n"
            "گزارش‌های آماری ربات از دیتابیس قابل محاسبه هستند.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 پنل مدیریت",
                        callback_data="admin:back"
                    )
                ]
            ]),
        )

    elif data == "admin:reminders":

        await query.edit_message_text(
            "🔔 مدیریت یادآوری‌ها\n\n"
            "وضعیت تنظیمات یادآوری کاربران در این بخش مدیریت می‌شود.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 پنل مدیریت",
                        callback_data="admin:back"
                    )
                ]
            ]),
        )

    elif data == "admin:system":

        await query.edit_message_text(
            "🚨 وضعیت سیستم\n\n"
            "🟢 Bot: Online\n"
            "🟢 Database: Connected",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 پنل مدیریت",
                        callback_data="admin:back"
                    )
                ]
            ]),
        )

    elif data == "admin:back":

        await query.edit_message_text(
            "👑 پنل مدیریت\n\n"
            "یکی از گزینه‌ها رو انتخاب کن:",
            reply_markup=admin_menu(),
        )

    elif data == "admin:exit":

        await query.edit_message_text(
            "🚪 از پنل مدیریت خارج شدی."
  )

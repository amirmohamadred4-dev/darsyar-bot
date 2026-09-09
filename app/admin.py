import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from .config import ADMIN_ID
from .db import session, User, Teacher, Class


# =========================================================
# 🔐 تنظیمات امنیتی
# =========================================================

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")


# =========================================================
# 🧰 بررسی دسترسی ادمین
# =========================================================

def is_admin(update: Update) -> bool:
    return (
        update.effective_user is not None
        and update.effective_user.id == ADMIN_ID
    )


# =========================================================
# 🔐 ورود به پنل
# =========================================================

async def admin_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not is_admin(update):
        await update.effective_message.reply_text(
            "⛔️ شما اجازه ورود به پنل مدیریت را ندارید."
        )
        return

    if not ADMIN_PASSWORD:
        await update.effective_message.reply_text(
            "⚠️ رمز ادمین در تنظیمات Railway ثبت نشده است."
        )
        return

    context.user_data["admin_waiting_password"] = True
    context.user_data["admin_logged_in"] = False

    await update.effective_message.reply_text(
        "🔐 <b>ورود به پنل مدیریت</b>\n\n"
        "رمز ورود ادمین را ارسال کن:",
        parse_mode="HTML",
    )


# =========================================================
# 🛠 منوی اصلی ادمین
# =========================================================

def admin_menu():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📊 آمار کلی",
                callback_data="admin:stats"
            ),
            InlineKeyboardButton(
                "👥 کاربران",
                callback_data="admin:users"
            ),
        ],
        [
            InlineKeyboardButton(
                "👨‍🏫 دبیرها",
                callback_data="admin:teachers"
            ),
            InlineKeyboardButton(
                "📚 کلاس‌ها",
                callback_data="admin:classes"
            ),
        ],
        [
            InlineKeyboardButton(
                "🔄 بروزرسانی",
                callback_data="admin:panel"
            ),
            InlineKeyboardButton(
                "🚪 خروج",
                callback_data="admin:exit"
            ),
        ],
    ])


async def show_admin_panel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = (
        "🔐 <b>پنل مدیریت</b>\n\n"
        "👑 سلام مدیر!\n\n"
        "از منوی زیر بخش موردنظر را انتخاب کن:"
    )

    if update.callback_query:

        await update.callback_query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=admin_menu(),
        )

    else:

        await update.effective_message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=admin_menu(),
        )


# =========================================================
# 📊 آمار کلی
# =========================================================

async def admin_stats(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    db = session()

    try:

        total_users = db.query(User).count()

        riazi = (
            db.query(User)
            .filter(User.field == "ریاضی")
            .count()
        )

        tajrobi = (
            db.query(User)
            .filter(User.field == "تجربی")
            .count()
        )

        ensani = (
            db.query(User)
            .filter(User.field == "انسانی")
            .count()
        )

        total_teachers = db.query(Teacher).count()
        total_classes = db.query(Class).count()

    finally:
        db.close()

    text = (
        "📊 <b>آمار کلی ربات</b>\n\n"
        f"👥 کل کاربران: <b>{total_users}</b>\n\n"
        "🎓 تفکیک رشته:\n"
        f"➗ ریاضی: <b>{riazi}</b>\n"
        f"🧬 تجربی: <b>{tajrobi}</b>\n"
        f"📖 انسانی: <b>{ensani}</b>\n\n"
        f"👨‍🏫 تعداد دبیرها: <b>{total_teachers}</b>\n"
        f"📚 تعداد کلاس‌ها: <b>{total_classes}</b>"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔙 برگشت",
                callback_data="admin:panel"
            )
        ]
    ])

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard,
    )


# =========================================================
# 👥 کاربران
# =========================================================

async def admin_users(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    db = session()

    try:

        users = (
            db.query(User)
            .order_by(User.id.desc())
            .limit(20)
            .all()
        )

        user_data = [
            {
                "name": user.name,
                "grade": user.grade,
                "field": user.field,
                "telegram_id": user.telegram_id,
            }
            for user in users
        ]

    finally:
        db.close()

    if not user_data:

        text = "👥 هنوز هیچ کاربری ثبت‌نام نکرده است."

    else:

        text = "👥 <b>آخرین کاربران</b>\n\n"

        for i, user in enumerate(user_data, 1):

            text += (
                f"{i}. <b>{user['name']}</b>\n"
                f"   🎓 پایه: {user['grade']}\n"
                f"   📖 رشته: {user['field']}\n"
                f"   🆔 ID: <code>{user['telegram_id']}</code>\n\n"
            )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔙 برگشت",
                callback_data="admin:panel"
            )
        ]
    ])

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard,
    )


# =========================================================
# 👨‍🏫 دبیرها
# =========================================================

async def admin_teachers(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    db = session()

    try:

        teachers = (
            db.query(Teacher)
            .order_by(
                Teacher.field,
                Teacher.subject,
                Teacher.name
            )
            .all()
        )

        teacher_data = [
            {
                "name": teacher.name,
                "subject": teacher.subject,
                "field": teacher.field,
            }
            for teacher in teachers
        ]

    finally:
        db.close()

    if not teacher_data:

        text = "👨‍🏫 هیچ دبیری در سیستم ثبت نشده است."

    else:

        text = "👨‍🏫 <b>دبیرهای ثبت‌شده</b>\n"

        current_field = None

        for teacher in teacher_data:

            if teacher["field"] != current_field:

                current_field = teacher["field"]

                text += (
                    f"\n🎓 <b>{current_field}</b>\n"
                )

            text += (
                f"• {teacher['subject']} — "
                f"{teacher['name']}\n"
            )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔙 برگشت",
                callback_data="admin:panel"
            )
        ]
    ])

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard,
    )


# =========================================================
# 📚 کلاس‌ها
# =========================================================

async def admin_classes(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    days = [
        "شنبه",
        "یکشنبه",
        "دوشنبه",
        "سه‌شنبه",
        "چهارشنبه",
        "پنجشنبه",
        "جمعه",
    ]

    db = session()

    try:

        classes = (
            db.query(Class)
            .order_by(
                Class.field,
                Class.day_of_week,
                Class.start_time
            )
            .all()
        )

        class_data = []

        for cls in classes:

            teacher = (
                db.query(Teacher)
                .filter(Teacher.id == cls.teacher_id)
                .first()
            )

            teacher_name = (
                teacher.name
                if teacher
                else "نامشخص"
            )

            day_name = (
                days[cls.day_of_week]
                if 0 <= cls.day_of_week < len(days)
                else "نامشخص"
            )

            class_data.append({
                "field": cls.field,
                "subject": cls.subject,
                "teacher": teacher_name,
                "day": day_name,
                "start": cls.start_time.strftime("%H:%M"),
                "end": cls.end_time.strftime("%H:%M"),
                "title": cls.title or "",
            })

    finally:
        db.close()

    if not class_data:

        text = "📚 هیچ کلاسی در سیستم ثبت نشده است."

    else:

        text = "📚 <b>برنامه کلاس‌ها</b>\n"

        current_field = None

        for cls in class_data:

            if cls["field"] != current_field:

                current_field = cls["field"]

                text += (
                    f"\n🎓 <b>{current_field}</b>\n"
                )

            text += (
                f"• 📅 {cls['day']}\n"
                f"  ⏰ {cls['start']} تا {cls['end']}\n"
                f"  📖 {cls['subject']}\n"
                f"  👨‍🏫 {cls['teacher']}\n"
            )

            if cls["title"]:

                text += (
                    f"  📝 {cls['title']}\n"
                )

            text += "\n"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔙 برگشت",
                callback_data="admin:panel"
            )
        ]
    ])

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard,
    )


# =========================================================
# 🚪 خروج
# =========================================================

async def admin_exit(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    context.user_data.pop(
        "admin_logged_in",
        None
    )

    context.user_data.pop(
        "admin_waiting_password",
        None
    )

    await query.edit_message_text(
        "🚪 از پنل مدیریت خارج شدی.\n\n"
        "برای ورود دوباره از /admin استفاده کن."
    )


# =========================================================
# 🎛 دکمه‌های ادمین
# =========================================================

async def admin_button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not is_admin(update):

        await query.answer(
            "⛔️ دسترسی ندارید.",
            show_alert=True
        )

        return

    if not context.user_data.get(
        "admin_logged_in"
    ):

        await query.answer(
            "⛔️ ابتدا وارد پنل شوید.",
            show_alert=True
        )

        return

    data = query.data

    if data == "admin:panel":

        await query.answer()

        await show_admin_panel(
            update,
            context
        )

    elif data == "admin:stats":

        await admin_stats(
            update,
            context
        )

    elif data == "admin:users":

        await admin_users(
            update,
            context
        )

    elif data == "admin:teachers":

        await admin_teachers(
            update,
            context
        )

    elif data == "admin:classes":

        await admin_classes(
            update,
            context
        )

    elif data == "admin:exit":

        await admin_exit(
            update,
            context
        )


# =========================================================
# 📦 Handlerها
# =========================================================

def get_admin_handlers():

    return [
        CommandHandler(
            "admin",
            admin_entry
        ),

        CallbackQueryHandler(
            admin_button_handler,
            pattern=r"^admin:"
        ),
        ]

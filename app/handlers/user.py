from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from ..config import FIELDS, GRADE
from ..db import session, User, Teacher, UserTeacher


def main_menu():
    keyboard = [
        [
            InlineKeyboardButton("🏠 صفحه اصلی", callback_data="home"),
            InlineKeyboardButton("📅 برنامه امروز", callback_data="today"),
        ],
        [InlineKeyboardButton("📆 برنامه هفتگی", callback_data="weekly")],
        [
            InlineKeyboardButton("👨‍🏫 دبیرهای من", callback_data="teachers"),
            InlineKeyboardButton("📊 عملکرد من", callback_data="performance"),
        ],
        [InlineKeyboardButton("🔔 تنظیمات یادآوری", callback_data="reminders")],
        [InlineKeyboardButton("⚙️ تنظیمات", callback_data="settings")],
    ]
    return InlineKeyboardMarkup(keyboard)


async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "📚 منوی اصلی\n\nاز گزینه‌های زیر استفاده کن:",
        reply_markup=main_menu(),
    )


async def start_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["registering"] = True

    await update.effective_message.reply_text(
        "📝 ثبت‌نام\n\nلطفاً نامت رو وارد کن:"
    )


async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("registering"):
        return

    name = update.message.text.strip()

    if len(name) < 2:
        await update.message.reply_text("❌ نام معتبر نیست. دوباره وارد کن:")
        return

    context.user_data["name"] = name

    keyboard = [
        [InlineKeyboardButton(GRADE, callback_data="grade:11")]
    ]

    await update.message.reply_text(
        "🎓 پایه تحصیلی:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def show_teachers_for_subject(
    query,
    context,
    subject,
):
    field = context.user_data["field"]

    db = session()

    try:
        teachers = (
            db.query(Teacher)
            .filter(
                Teacher.field == field,
                Teacher.subject == subject,
            )
            .order_by(Teacher.name)
            .all()
        )
    finally:
        db.close()

    if not teachers:
        await query.edit_message_text(
            f"⚠️ برای درس «{subject}» هنوز دبیری ثبت نشده."
        )
        return

    keyboard = [
        [
            InlineKeyboardButton(
                teacher.name,
                callback_data=f"teacher:{teacher.id}:{subject}",
            )
        ]
        for teacher in teachers
    ]

    await query.edit_message_text(
        f"👨‍🏫 دبیر درس «{subject}» رو انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def start_teacher_selection(query, context):
    field = context.user_data["field"]

    db = session()

    try:
        subjects = (
            db.query(Teacher.subject)
            .filter(Teacher.field == field)
            .distinct()
            .all()
        )
    finally:
        db.close()

    subjects = sorted({x[0] for x in subjects})

    if not subjects:
        await query.edit_message_text(
            "⚠️ هنوز دبیرهای این رشته وارد دیتابیس نشده‌اند."
        )
        return

    context.user_data["subjects"] = subjects
    context.user_data["subject_index"] = 0
    context.user_data["selected_teachers"] = {}

    await show_teachers_for_subject(
        query,
        context,
        subjects[0],
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "home":
        await query.edit_message_text(
            "📚 منوی اصلی",
            reply_markup=main_menu(),
        )

    elif data == "grade:11":
        keyboard = [
            [InlineKeyboardButton(field, callback_data=f"field:{field}")]
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
                "❌ ثبت‌نام منقضی شده. دوباره /register رو بزن."
            )
            return

        db = session()

        try:
            user = (
                db.query(User)
                .filter(User.telegram_id == update.effective_user.id)
                .first()
            )

            if user:
                user.name = name
                user.grade = GRADE
                user.field = field
            else:
                user = User(
                    telegram_id=update.effective_user.id,
                    name=name,
                    grade=GRADE,
                    field=field,
                )
                db.add(user)

            db.commit()
        finally:
            db.close()

        context.user_data["field"] = field

        await query.edit_message_text(
            f"✅ رشته «{field}» انتخاب شد.\n\n"
            "حالا دبیر هر درس رو یکی‌یکی انتخاب می‌کنیم."
        )

        await start_teacher_selection(query, context)

    elif data.startswith("teacher:"):
        _, teacher_id, subject = data.split(":", 2)
        teacher_id = int(teacher_id)

        field = context.user_data["field"]

        db = session()

        try:
            user = (
                db.query(User)
                .filter(User.telegram_id == update.effective_user.id)
                .first()
            )

            if not user:
                await query.edit_message_text(
                    "❌ کاربر پیدا نشد. دوباره /register رو بزن."
                )
                return

            old = (
                db.query(UserTeacher)
                .filter(
                    UserTeacher.user_id == user.id,
                    UserTeacher.subject == subject,
                )
                .first()
            )

            if old:
                old.teacher_id = teacher_id
            else:
                db.add(
                    UserTeacher(
                        user_id=user.id,
                        teacher_id=teacher_id,
                        subject=subject,
                    )
                )

            db.commit()

            teacher = db.query(Teacher).filter(
                Teacher.id == teacher_id
            ).first()

            teacher_name = teacher.name if teacher else "دبیر"

        finally:
            db.close()

        context.user_data["selected_teachers"][subject] = teacher_id

        index = context.user_data["subject_index"] + 1
        subjects = context.user_data["subjects"]

        if index < len(subjects):
            context.user_data["subject_index"] = index

            await show_teachers_for_subject(
                query,
                context,
                subjects[index],
            )
        else:
            await query.edit_message_text(
                "🎉 انتخاب دبیرها کامل شد!\n\n"
                "همه دبیرهای انتخابی در دیتابیس ذخیره شدند.",
                reply_markup=main_menu(),
            )

    elif data == "today":
        await query.edit_message_text("📅 برنامه امروز به‌زودی فعال می‌شود.")

    elif data == "weekly":
        await query.edit_message_text("📆 برنامه هفتگی به‌زودی فعال می‌شود.")

    elif data == "teachers":
        await query.edit_message_text("👨‍🏫 مدیریت دبیرها به‌زودی فعال می‌شود.")

    elif data == "performance":
        await query.edit_message_text("📊 عملکرد به‌زودی فعال می‌شود.")

    elif data == "reminders":
        await query.edit_message_text("🔔 تنظیمات یادآوری به‌زودی فعال می‌شود.")

    elif data == "settings":
        await query.edit_message_text("⚙️ تنظیمات به‌زودی فعال می‌شود.")


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

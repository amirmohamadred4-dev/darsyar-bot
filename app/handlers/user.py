from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from ..config import FIELDS, GRADE, DAYS, TIMEZONE
from ..db import session, User, Teacher, UserTeacher, Class, ClassRecord, UserSettings


# =========================
# منوی اصلی
# =========================

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


# =========================
# ابزارهای کمکی
# =========================

def get_user(telegram_id):
    db = session()
    try:
        return (
            db.query(User)
            .filter(User.telegram_id == telegram_id)
            .first()
        )
    finally:
        db.close()


def get_or_create_settings(db, user_id):
    settings = (
        db.query(UserSettings)
        .filter(UserSettings.user_id == user_id)
        .first()
    )

    if settings is None:
        settings = UserSettings(user_id=user_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)

    return settings


def today_persian_day():
    """
    Python:
    Monday=0 ... Sunday=6

    برنامه:
    شنبه=0 ... جمعه=6
    """

    weekday = datetime.now(TIMEZONE).weekday()

    mapping = {
        5: 0,  # شنبه
        6: 1,  # یکشنبه
        0: 2,  # دوشنبه
        1: 3,  # سه‌شنبه
        2: 4,  # چهارشنبه
        3: 5,  # پنجشنبه
        4: 6,  # جمعه
    }

    return mapping[weekday]


def format_class(class_item, teacher):
    start = class_item.start_time.strftime("%H:%M")
    end = class_item.end_time.strftime("%H:%M")

    return (
        f"🕐 {start} تا {end}\n"
        f"📚 {class_item.subject}\n"
        f"👨‍🏫 {teacher.name}"
    )


# =========================
# صفحه اصلی
# =========================

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = get_user(update.effective_user.id)

    if not user:
        await update.effective_message.reply_text(
            "👋 سلام!\n\n"
            "برای استفاده از ربات ابتدا ثبت‌نام کن.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "📝 ثبت‌نام",
                        callback_data="register"
                    )
                ]
            ]),
        )
        return

    await update.effective_message.reply_text(
        f"📚 سلام {user.name}!\n\n"
        f"🎓 پایه: {user.grade}\n"
        f"📖 رشته: {user.field}\n\n"
        "از منوی زیر استفاده کن:",
        reply_markup=main_menu(),
    )


# =========================
# ثبت نام
# =========================

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
            "❌ نام معتبر نیست.\n"
            "لطفاً دوباره وارد کن:"
        )
        return

    context.user_data["name"] = name

    await update.message.reply_text(
        "🎓 پایه تحصیلی:",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    GRADE,
                    callback_data="grade:11"
                )
            ]
        ]),
    )


# =========================
# انتخاب رشته
# =========================

async def show_fields(query):

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


# =========================
# انتخاب دبیر
# =========================

async def show_teachers_for_subject(query, context, subject):

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
            f"❌ برای درس «{subject}» دبیری پیدا نشد."
        )
        return

    keyboard = []

    for teacher in teachers:
        keyboard.append([
            InlineKeyboardButton(
                teacher.name,
                callback_data=f"teacher:{teacher.id}:{subject}"
            )
        ])

    await query.edit_message_text(
        f"👨‍🏫 دبیر «{subject}» رو انتخاب کن:",
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
            "❌ برای این رشته هنوز دبیر ثبت نشده."
        )
        return

    context.user_data["subjects"] = subjects
    context.user_data["subject_index"] = 0

    await show_teachers_for_subject(
        query,
        context,
        subjects[0]
    )


# =========================
# برنامه امروز
# =========================

async def show_today(query, update):

    user = get_user(update.effective_user.id)

    if not user:
        await query.edit_message_text(
            "❌ ابتدا ثبت‌نام کن.",
            reply_markup=main_menu(),
        )
        return

    day_number = today_persian_day()
    day_name = DAYS[day_number]

    db = session()

    try:

        selected = (
            db.query(UserTeacher)
            .filter(UserTeacher.user_id == user.id)
            .all()
        )

        teacher_ids = [x.teacher_id for x in selected]

        if not teacher_ids:
            await query.edit_message_text(
                "👨‍🏫 هنوز هیچ دبیری انتخاب نکردی.",
                reply_markup=main_menu(),
            )
            return

        classes = (
            db.query(Class, Teacher)
            .join(
                Teacher,
                Class.teacher_id == Teacher.id
            )
            .filter(
                Class.field == user.field,
                Class.day_of_week == day_number,
                Class.teacher_id.in_(teacher_ids),
            )
            .order_by(Class.start_time)
            .all()
        )

    finally:
        db.close()

    text = (
        f"📅 برنامه امروز\n"
        f"📌 {day_name}\n"
        f"🎓 {user.field}\n\n"
    )

    if not classes:
        text += "🎉 امروز کلاسی برای دبیرهای انتخابی تو نداری."

    else:
        for class_item, teacher in classes:
            text += format_class(
                class_item,
                teacher
            )
            text += "\n\n"

    await query.edit_message_text(
        text,
        reply_markup=main_menu(),
    )


# =========================
# برنامه هفتگی
# =========================

async def show_weekly(query, update):

    user = get_user(update.effective_user.id)

    if not user:
        await query.edit_message_text(
            "❌ ابتدا ثبت‌نام کن.",
            reply_markup=main_menu(),
        )
        return

    db = session()

    try:

        selected = (
            db.query(UserTeacher)
            .filter(UserTeacher.user_id == user.id)
            .all()
        )

        teacher_ids = [x.teacher_id for x in selected]

        if not teacher_ids:
            await query.edit_message_text(
                "👨‍🏫 هنوز دبیر انتخاب نکردی.",
                reply_markup=main_menu(),
            )
            return

        classes = (
            db.query(Class, Teacher)
            .join(
                Teacher,
                Class.teacher_id == Teacher.id
            )
            .filter(
                Class.field == user.field,
                Class.teacher_id.in_(teacher_ids),
            )
            .order_by(
                Class.day_of_week,
                Class.start_time
            )
            .all()
        )

    finally:
        db.close()

    text = (
        f"📆 برنامه هفتگی\n"
        f"🎓 رشته: {user.field}\n"
    )

    current_day = None

    for class_item, teacher in classes:

        if class_item.day_of_week != current_day:

            current_day = class_item.day_of_week

            text += (
                f"\n\n📌 {DAYS[current_day]}\n"
                "━━━━━━━━━━━━\n"
            )

        start = class_item.start_time.strftime("%H:%M")
        end = class_item.end_time.strftime("%H:%M")

        text += (
            f"🕐 {start} تا {end}\n"
            f"📚 {class_item.subject}\n"
            f"👨‍🏫 {teacher.name}\n\n"
        )

    await query.edit_message_text(
        text,
        reply_markup=main_menu(),
    )


# =========================
# دبیرهای من
# =========================

async def show_my_teachers(query, update):

    user = get_user(update.effective_user.id)

    if not user:
        await query.edit_message_text(
            "❌ ابتدا ثبت‌نام کن.",
            reply_markup=main_menu(),
        )
        return

    db = session()

    try:

        selected = (
            db.query(UserTeacher, Teacher)
            .join(
                Teacher,
                UserTeacher.teacher_id == Teacher.id
            )
            .filter(UserTeacher.user_id == user.id)
            .order_by(UserTeacher.subject)
            .all()
        )

    finally:
        db.close()

    if not selected:
        await query.edit_message_text(
            "👨‍🏫 هنوز دبیر انتخاب نکردی.",
            reply_markup=main_menu(),
        )
        return

    text = "👨‍🏫 دبیرهای من\n\n"

    keyboard = []

    for user_teacher, teacher in selected:

        text += (
            f"📚 {user_teacher.subject}\n"
            f"👨‍🏫 {teacher.name}\n\n"
        )

        keyboard.append([
            InlineKeyboardButton(
                f"🔄 تغییر {user_teacher.subject}",
                callback_data=f"change_teacher:{user_teacher.subject}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "🔙 منوی اصلی",
            callback_data="home"
        )
    ])

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def change_teacher(query, update, subject):

    user = get_user(update.effective_user.id)

    if not user:
        return

    db = session()

    try:
        teachers = (
            db.query(Teacher)
            .filter(
                Teacher.field == user.field,
                Teacher.subject == subject,
            )
            .order_by(Teacher.name)
            .all()
        )
    finally:
        db.close()

    keyboard = [
        [
            InlineKeyboardButton(
                teacher.name,
                callback_data=f"change:{teacher.id}:{subject}"
            )
        ]
        for teacher in teachers
    ]

    keyboard.append([
        InlineKeyboardButton(
            "🔙 برگشت",
            callback_data="teachers"
        )
    ])

    await query.edit_message_text(
        f"🔄 تغییر دبیر «{subject}»\n\n"
        "دبیر جدید رو انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================
# عملکرد
# =========================

async def show_performance(query, update):

    user = get_user(update.effective_user.id)

    if not user:
        await query.edit_message_text(
            "❌ ابتدا ثبت‌نام کن.",
            reply_markup=main_menu(),
        )
        return

    db = session()

    try:

        records = (
            db.query(ClassRecord)
            .filter(ClassRecord.user_id == user.id)
            .all()
        )

    finally:
        db.close()

    total = len(records)
    seen = sum(1 for r in records if r.status == "seen")
    unseen = sum(1 for r in records if r.status == "unseen")
    pending = sum(1 for r in records if r.status == "pending")

    if total:
        percent = round((seen / total) * 100)
    else:
        percent = 0

    text = (
        "📊 عملکرد من\n\n"
        f"📚 کل کلاس‌ها: {total}\n"
        f"✅ دیده‌شده: {seen}\n"
        f"❌ دیده‌نشده: {unseen}\n"
        f"⏳ هنوز مشخص نشده: {pending}\n\n"
        f"📈 میزان پیگیری: {percent}%\n\n"
    )

    if total == 0:
        text += "هنوز اطلاعاتی برای محاسبه عملکرد ثبت نشده."

    elif percent >= 80:
        text += "🔥 عالی پیش رفتی! همین روند رو ادامه بده."

    elif percent >= 50:
        text += "💪 خوبه! با کمی نظم بیشتر می‌تونی بهترش کنی."

    else:
        text += "🌱 قدم‌به‌قدم جلو برو؛ مهم اینه که ادامه بدی."

    await query.edit_message_text(
        text,
        reply_markup=main_menu(),
    )


# =========================
# تنظیمات یادآوری
# =========================

async def show_reminders(query, update):

    user = get_user(update.effective_user.id)

    if not user:
        return

    db = session()

    try:
        settings = get_or_create_settings(db, user.id)

        enabled = settings.reminders_enabled
        minutes = settings.reminder_minutes
        start_enabled = settings.start_reminder_enabled
        nightly = settings.nightly_report_enabled

    finally:
        db.close()

    status = "🟢 روشن" if enabled else "🔴 خاموش"
    start_status = "🟢 روشن" if start_enabled else "🔴 خاموش"
    nightly_status = "🟢 روشن" if nightly else "🔴 خاموش"

    text = (
        "🔔 تنظیمات یادآوری\n\n"
        f"یادآوری قبل از کلاس: {status}\n"
        f"⏰ زمان: {minutes} دقیقه قبل\n\n"
        f"🚀 یادآوری شروع کلاس: {start_status}\n\n"
        f"🌙 گزارش شبانه: {nightly_status}\n"
        "🕚 زمان گزارش: ۲۳:۴۵"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "🔄 روشن/خاموش",
                callback_data="toggle_reminders"
            )
        ],
        [
            InlineKeyboardButton(
                "⏰ ۱۵ دقیقه",
                callback_data="reminder:15"
            ),
            InlineKeyboardButton(
                "⏰ ۳۰ دقیقه",
                callback_data="reminder:30"
            ),
            InlineKeyboardButton(
                "⏰ ۶۰ دقیقه",
                callback_data="reminder:60"
            ),
        ],
        [
            InlineKeyboardButton(
                "🚀 روشن/خاموش شروع کلاس",
                callback_data="toggle_start"
            )
        ],
        [
            InlineKeyboardButton(
                "🌙 روشن/خاموش گزارش شبانه",
                callback_data="toggle_nightly"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 منوی اصلی",
                callback_data="home"
            )
        ],
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================
# تنظیمات کاربر
# =========================

async def show_settings(query, update):

    user = get_user(update.effective_user.id)

    if not user:
        return

    text = (
        "⚙️ تنظیمات\n\n"
        f"👤 نام: {user.name}\n"
        f"🎓 پایه: {user.grade}\n"
        f"📚 رشته: {user.field}\n\n"
        "از گزینه‌های زیر استفاده کن:"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "✏️ تغییر نام",
                callback_data="change_name"
            )
        ],
        [
            InlineKeyboardButton(
                "📚 تغییر رشته",
                callback_data="change_field"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 منوی اصلی",
                callback_data="home"
            )
        ],
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================
# هندلر اصلی دکمه‌ها
# =========================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data

    # ثبت نام
    if data == "register":
        await start_register(update, context)
        return

    # خانه
    if data == "home":

        user = get_user(update.effective_user.id)

        if user:
            await query.edit_message_text(
                f"📚 منوی اصلی\n\n"
                f"سلام {user.name} 👋\n"
                f"🎓 {user.grade} | 📖 {user.field}\n\n"
                "یکی از گزینه‌ها رو انتخاب کن:",
                reply_markup=main_menu(),
            )
        else:
            await query.edit_message_text(
                "👋 برای شروع ثبت‌نام کن.",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "📝 ثبت‌نام",
                            callback_data="register"
                        )
                    ]
                ]),
            )

        return

    # پایه
    if data == "grade:11":
        await show_fields(query)
        return

    # رشته
    if data.startswith("field:"):

        field = data.split(":", 1)[1]
        name = context.user_data.get("name")

        if not name:
            await query.edit_message_text(
                "❌ اطلاعات ثبت‌نام پیدا نشد.\n"
                "دوباره ثبت‌نام کن."
            )
            return

        db = session()

        try:

            user = (
                db.query(User)
                .filter(
                    User.telegram_id == update.effective_user.id
                )
                .first()
            )

            if user:
                user.name = name
                user.grade = GRADE
                user.field = field

                # انتخاب‌های قبلی پاک می‌شوند
                db.query(UserTeacher).filter(
                    UserTeacher.user_id == user.id
                ).delete()

            else:

                user = User(
                    telegram_id=update.effective_user.id,
                    name=name,
                    grade=GRADE,
                    field=field,
                )

                db.add(user)
                db.flush()

            get_or_create_settings(db, user.id)

            db.commit()

        finally:
            db.close()

        context.user_data["field"] = field

        await query.edit_message_text(
            f"✅ رشته «{field}» انتخاب شد.\n\n"
            "حالا دبیر هر درس رو انتخاب می‌کنیم."
        )

        await start_teacher_selection(
            query,
            context
        )

        return

    # انتخاب دبیر هنگام ثبت نام
    if data.startswith("teacher:"):

        _, teacher_id, subject = data.split(":", 2)
        teacher_id = int(teacher_id)

        db = session()

        try:

            user = (
                db.query(User)
                .filter(
                    User.telegram_id == update.effective_user.id
                )
                .first()
            )

            if not user:
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

        finally:
            db.close()

        index = context.user_data["subject_index"] + 1
        subjects = context.user_data["subjects"]

        if index < len(subjects):

            context.user_data["subject_index"] = index

            await show_teachers_for_subject(
                query,
                context,
                subjects[index]
            )

        else:

            context.user_data["registering"] = False

            await query.edit_message_text(
                "🎉 ثبت‌نام کامل شد!\n\n"
                "دبیرهای انتخابی ذخیره شدند.",
                reply_markup=main_menu(),
            )

        return

    # برنامه امروز
    if data == "today":
        await show_today(query, update)
        return

    # برنامه هفتگی
    if data == "weekly":
        await show_weekly(query, update)
        return

    # دبیرهای من
    if data == "teachers":
        await show_my_teachers(query, update)
        return

    # تغییر دبیر یک درس
    if data.startswith("change_teacher:"):

        subject = data.split(":", 1)[1]

        await change_teacher(
            query,
            update,
            subject
        )

        return

    # ثبت دبیر جدید
    if data.startswith("change:"):

        _, teacher_id, subject = data.split(":", 2)

        teacher_id = int(teacher_id)

        db = session()

        try:

            user = (
                db.query(User)
                .filter(
                    User.telegram_id == update.effective_user.id
                )
                .first()
            )

            if user:

                selected = (
                    db.query(UserTeacher)
                    .filter(
                        UserTeacher.user_id == user.id,
                        UserTeacher.subject == subject,
                    )
                    .first()
                )

                if selected:
                    selected.teacher_id = teacher_id

                else:
                    db.add(
                        UserTeacher(
                            user_id=user.id,
                            teacher_id=teacher_id,
                            subject=subject,
                        )
                    )

                db.commit()

        finally:
            db.close()

        await show_my_teachers(
            query,
            update
        )

        return

    # عملکرد
    if data == "performance":
        await show_performance(query, update)
        return

    # تنظیمات یادآوری
    if data == "reminders":
        await show_reminders(query, update)
        return

    # روشن/خاموش یادآوری
    if data == "toggle_reminders":

        user = get_user(update.effective_user.id)

        db = session()

        try:
            settings = get_or_create_settings(db, user.id)
            settings.reminders_enabled = not settings.reminders_enabled
            db.commit()
        finally:
            db.close()

        await show_reminders(query, update)
        return

    # زمان یادآوری
    if data.startswith("reminder:"):

        minutes = int(data.split(":", 1)[1])

        user = get_user(update.effective_user.id)

        db = session()

        try:
            settings = get_or_create_settings(db, user.id)
            settings.reminder_minutes = minutes
            settings.reminders_enabled = True
            db.commit()
        finally:
            db.close()

        await show_reminders(query, update)
        return

    # یادآوری شروع کلاس
    if data == "toggle_start":

        user = get_user(update.effective_user.id)

        db = session()

        try:
            settings = get_or_create_settings(db, user.id)
            settings.start_reminder_enabled = (
                not settings.start_reminder_enabled
            )
            db.commit()
        finally:
            db.close()

        await show_reminders(query, update)
        return

    # گزارش شبانه
    if data == "toggle_nightly":

        user = get_user(update.effective_user.id)

        db = session()

        try:
            settings = get_or_create_settings(db, user.id)
            settings.nightly_report_enabled = (
                not settings.nightly_report_enabled
            )
            db.commit()
        finally:
            db.close()

        await show_reminders(query, update)
        return

    # تنظیمات
    if data == "settings":
        await show_settings(query, update)
        return

    # تغییر رشته
    if data == "change_field":

        keyboard = [
            [
                InlineKeyboardButton(
                    field,
                    callback_data=f"newfield:{field}"
                )
            ]
            for field in FIELDS
        ]

        keyboard.append([
            InlineKeyboardButton(
                "🔙 برگشت",
                callback_data="settings"
            )
        ])

        await query.edit_message_text(
            "📚 رشته جدیدت رو انتخاب کن:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

        return

    # تغییر رشته نهایی
    if data.startswith("newfield:"):

        field = data.split(":", 1)[1]

        user = get_user(update.effective_user.id)

        db = session()

        try:

            user.field = field

            db.query(UserTeacher).filter(
                UserTeacher.user_id == user.id
            ).delete()

            db.commit()

        finally:
            db.close()

        context.user_data["field"] = field
        context.user_data["subjects"] = []
        context.user_data["subject_index"] = 0

        await query.edit_message_text(
            f"✅ رشته به «{field}» تغییر کرد.\n\n"
            "حالا دبیرهای رشته جدیدت رو انتخاب کن."
        )

        await start_teacher_selection(
            query,
            context
        )

        return

    # تغییر نام
    if data == "change_name":

        context.user_data["changing_name"] = True

        await query.edit_message_text(
            "✏️ نام جدیدت رو ارسال کن:"
        )

        return


# =========================
# دریافت نام جدید
# =========================

async def receive_new_name(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.user_data.get("changing_name"):
        return

    name = update.message.text.strip()

    if len(name) < 2:
        await update.message.reply_text(
            "❌ نام معتبر نیست. دوباره ارسال کن:"
        )
        return

    user = get_user(update.effective_user.id)

    if not user:
        return

    db = session()

    try:
        user.name = name
        db.commit()
    finally:
        db.close()

    context.user_data["changing_name"] = False

    await update.message.reply_text(
        f"✅ نامت به «{name}» تغییر کرد.",
        reply_markup=main_menu(),
    )


# =========================
# ثبت Handler ها
# =========================

def get_user_handlers():

    return [

        CommandHandler(
            "menu",
            show_menu
        ),

        CommandHandler(
            "register",
            start_register
        ),

        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND
            & ~filters.UpdateType.EDITED_MESSAGE,
            receive_new_name
        ),

        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receive_name
        ),

        CallbackQueryHandler(
            button_handler
        ),
    ]

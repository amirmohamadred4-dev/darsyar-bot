import os
from zoneinfo import ZoneInfo

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

DATABASE_URL = "sqlite:///studybot.db"

TIMEZONE = ZoneInfo(
    os.getenv("TIMEZONE", "Asia/Tehran")
)

FIELDS = (
    "ریاضی",
    "تجربی",
    "انسانی",
)

GRADE = "یازدهم"

DAYS = [
    "شنبه",
    "یکشنبه",
    "دوشنبه",
    "سه‌شنبه",
    "چهارشنبه",
    "پنجشنبه",
    "جمعه",
]

DAY_TO_NUM = {
    day: index
    for index, day in enumerate(DAYS)
}

PY_TO_FA_DAY = {
    5: "شنبه",
    6: "یکشنبه",
    0: "دوشنبه",
    1: "سه‌شنبه",
    2: "چهارشنبه",
    3: "پنجشنبه",
    4: "جمعه",
}

RECORD_UNSEEN = "unseen"
RECORD_SEEN = "seen"
RECORD_PENDING = "pending"

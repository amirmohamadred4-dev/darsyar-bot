import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

ADMIN_ID = int(os.getenv("ADMIN_ID", "7390580427"))

TIMEZONE = os.getenv("TIMEZONE", "Asia/Tehran")

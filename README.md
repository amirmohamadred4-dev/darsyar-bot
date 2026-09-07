# مشاور درسی یازدهم — ربات تلگرام

ربات فارسی مشاور درسی بر اساس رشته و دبیرهای انتخابی. دیتابیس PostgreSQL برای Railway پیشنهاد می‌شود؛ SQLite فقط برای تست محلی قابل استفاده است.

## متغیرهای محیطی
- `BOT_TOKEN`
- `ADMIN_ID`
- `DATABASE_URL`
- `TIMEZONE` (پیش‌فرض: `Asia/Tehran`)

## اجرا
```bash
pip install -r requirements.txt
python -m app
```

## Railway
1. Repository را به Railway وصل کنید.
2. Variables بالا را اضافه کنید.
3. یک PostgreSQL به پروژه اضافه کنید و `DATABASE_URL` آن را به سرویس ربات بدهید.
4. Deploy را اجرا کنید.

> برنامه دبیرها در `app/seed.py` قرار دارد و با اجرای برنامه به‌صورت idempotent وارد/به‌روزرسانی می‌شود. برای تغییر برنامه، seed را اصلاح کنید و Deploy کنید؛ منطق ربات نیاز به تغییر ندارد.

## دستورات ادمین
- `/admin` پنل
- `/addteacher رشته|درس|نام`
- `/delteacher ID`
- `/editteacher ID|نام جدید|درس جدید|رشته`
- `/addclass teacher_id|روز|شروع|پایان|عنوان`
- `/delclass ID`
- `/editclass ID|روز|شروع|پایان|عنوان`
- `/user telegram_id`
- `/broadcast متن`

روزها: `شنبه، یکشنبه، دوشنبه، سه‌شنبه، چهارشنبه، پنجشنبه، جمعه`

فرمت ساعت: `HH:MM`

## نکته
Scheduler هر ۳۰ ثانیه دیتابیس را بررسی می‌کند؛ بنابراین بعد از Restart، وضعیت‌های ثبت‌شده در DB باقی می‌مانند و پیام‌های ارسال‌شده دوباره ارسال نمی‌شوند.


import requests
import json
import time
import schedule
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# ==== تنظیمات ====
import os
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]

DATA_FILE = "data.json"

# ==== تابع دریافت اطلاعات از سایت ====
def fetch_data():
    url = "https://ledc.ir/خاموشیهای-برنامه-ریزی-شده"
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", class_="table-striped table-bordered rtl")

        result = {}
        rows = table.find_all("tr")

        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 5:
                code = cols[0].text.strip()
                zone = cols[1].text.strip()
                time_str = cols[2].text.strip()
                area = cols[3].text.strip()
                address = cols[4].text.strip()

                if code:
                    result[code] = {
                        "time": time_str,
                        "zone": zone,
                        "area": area,
                        "address": address
                    }

        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print("✅ اطلاعات به‌روزرسانی شد.")

    except Exception as e:
        print(f"⚠️ خطا در دریافت اطلاعات: {e}")

# ==== تبدیل عدد انگلیسی به فارسی ====
def to_persian_digits(text):
    eng_to_fa = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
    return text.translate(eng_to_fa)

# ==== پاسخ به پیام‌های کاربران ====
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = to_persian_digits(update.message.text.strip())
    normalized_query = query.replace("-", " ").replace("‌", "").strip()

    try:
        with open("data.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        found = False
        msg = ""

        for code, entry in data.items():
            normalized_address = entry["address"].replace("-", " ").replace("‌", "")
            normalized_zone = entry.get("zone", "").replace("-", " ").replace("‌", "")
            normalized_area = entry.get("area", "").replace("-", " ").replace("‌", "")

            if (
                normalized_query == code or
                normalized_query in normalized_address or
                normalized_query in normalized_zone or
                normalized_query in normalized_area
            ):
                msg = (
                    f"📍 اطلاعات خاموشی برای کد {code}:

"
                    f"🗺 منطقه شهرداری:
{entry['zone']}

"
                    f"⚡️ برق شما ساعت {entry['time']} قطع میشه😓

"
                    f"📌 آدرس:
{entry['address']}

"
                    f"👨‍💻 طراحی ربات توسط [mamadmk](https://t.me/MamadMk)"
                )
                found = True
                break

        if found:
            await update.message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=True)
        else:
            if update.message.chat.type == "private":
                await update.message.reply_text("❌ موردی با این مشخصات پیدا نشد.")
            else:
                pass

    except Exception as e:
        await update.message.reply_text("⚠️ خطا در دسترسی به اطلاعات.")

# ==== اجرای ربات ====
if __name__ == "__main__":
    from telegram.ext import ApplicationBuilder, MessageHandler, filters

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    fetch_data()  # بار اول
    schedule.every(3).hours.do(fetch_data)

    import threading, asyncio

    async def run_schedule():
        while True:
            schedule.run_pending()
            await asyncio.sleep(60)

    threading.Thread(target=lambda: asyncio.run(run_schedule()), daemon=True).start()

    print("🤖 ربات فعال شد.")
    app.run_polling()

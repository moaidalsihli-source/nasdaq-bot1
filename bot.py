import requests
import yfinance as yf
import pandas as pd
import time
import os
import pytz
from datetime import datetime, time as dtime

# ==============================
# إعدادات تيليجرام
# ==============================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text
    }
    requests.post(url, data=payload)

# ==============================
# وقت الجلسة (السوق الأمريكي)
# ==============================

EST = pytz.timezone("US/Eastern")

def is_trading_session():
    now = datetime.now(EST).time()
    market_open = dtime(9, 30)
    market_close = dtime(16, 0)
    return market_open <= now <= market_close

# ==============================
# جلب أسهم NASDAQ
# ==============================

def get_nasdaq_tickers():
    url = "ftp://ftp.nasdaqtrader.com/SymbolDirectory/nasdaqlisted.txt"
    df = pd.read_csv(url, sep="|")
    df = df[df["Test Issue"] == "N"]
    return df["Symbol"].tolist()

# ==============================
# المتغيرات العامة
# ==============================

alerted = {}
daily_count = 0
today_date = datetime.now().date()

# ==============================
# الفحص
# ==============================

def check_stocks():
    global daily_count, today_date

    # تصفير يوم جديد
    if datetime.now().date() != today_date:
        daily_count = 0
        today_date = datetime.now().date()
        alerted.clear()

    tickers = get_nasdaq_tickers()
    levels = [5, 10, 20, 50, 70, 100]

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(period="1d", interval="1m")

            if len(data) < 5:
                continue

            price = data["Close"].iloc[-1]
            open_price = data["Open"].iloc[0]

            # فلتر السعر
            if not (0.06 <= price <= 10):
                continue

            change_percent = ((price - open_price) / open_price) * 100
            abs_change = abs(change_percent)

            current_level = None
            for lvl in levels:
                if abs_change >= lvl:
                    current_level = lvl

            if current_level is None:
                continue

            # منع تكرار نفس المستوى
            if ticker in alerted and alerted[ticker] >= current_level:
                continue

            # فلتر السيولة
            first_min_volume = data["Volume"].iloc[0]
            current_volume = data["Volume"].iloc[-1]

            if current_volume <= first_min_volume:
                continue

            alerted[ticker] = current_level
            daily_count += 1

            direction = "🟢 صعود" if change_percent > 0 else "🔴 هبوط"

            message = (
                f"\n🔸 الرمز -> {ticker}\n"
                f"🚨 تنبيه رقم {daily_count} اليوم\n"
                f"⚡️ مستوى {current_level}%+\n"
                f"{direction}\n"
                f"💰 السعر -> {round(price,2)}$ ({round(change_percent,2)}%)\n"
                f"📊 فوليوم الآن -> {current_volume}\n"
                f"🔥 أول دقيقة -> {first_min_volume}"
            )

            send_message(message)

            return  # يرسل سهم واحد فقط

        except:
            continue

# ==============================
# التشغيل المستمر
# ==============================

while True:
    if is_trading_session():
        check_stocks()
        time.sleep(20)
    else:
    
        time.sleep(60)

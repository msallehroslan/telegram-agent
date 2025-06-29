import requests
import os
from openai import OpenAI
import matplotlib.pyplot as plt
from datetime import datetime
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from io import BytesIO

# --- Configuration ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# ThingSpeak channels
POLY_URL = "https://api.thingspeak.com/channels/2749134/feeds.json?api_key=ELRZSYIQKSNMXSA4&results=10"
LSTM_URL = "https://api.thingspeak.com/channels/2796258/feeds.json?api_key=G3MHZ8U7VD4W1GH3&results=10"
CURRENT_URL = "https://api.thingspeak.com/channels/2692605/fields/1/last.json?api_key=60SQCX95B7XKZN2E"

# --- Functions ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("\U0001F44B Welcome to TempCast Bot!\nType `status`, `trend`, `chart`, or ask me anything \U0001F916")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        poly = requests.get(POLY_URL).json()["feeds"][-1]
        lstm = requests.get(LSTM_URL).json()["feeds"][-1]
        current = requests.get(CURRENT_URL).json().get("field1", "N/A")

        poly_temp = poly.get("field1", "N/A")
        poly_anom = "\u26A0\uFE0F Yes - Check system!" if poly.get("field2", "0") == "1" else "\u2705 No"

        lstm_temp = lstm.get("field1", "N/A")
        lstm_anom = "\u26A0\uFE0F Yes - Check system!" if lstm.get("field2", "0") == "1" else "\u2705 No"

        message = f"""\U0001F321\uFE0F *Temperature Status*

🌍 *Current*: {current} °C

📈 *Polynomial*
• Predicted: {poly_temp} °C
• Anomaly: {poly_anom}

🔁 *LSTM*
• Predicted: {lstm_temp} °C
• Anomaly: {lstm_anom}
"""
        await update.message.reply_markdown(message)
    except:
        await update.message.reply_text("❌ Failed to fetch data from ThingSpeak.")

async def trend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        poly_data = requests.get(POLY_URL).json()["feeds"]
        lstm_data = requests.get(LSTM_URL).json()["feeds"]

        poly_trend = float(poly_data[-1]["field1"]) - float(poly_data[0]["field1"])
        lstm_trend = float(lstm_data[-1]["field1"]) - float(lstm_data[0]["field1"])

        trend_msg = """\U0001F4CA *Temperature Trend (Last 10)*

\U0001F4C8 *Polynomial*: {:+.2f} °C ({})
🔁 *LSTM*: {:+.2f} °C ({})
""".format(
            poly_trend, "Rising" if poly_trend > 0 else "Falling" if poly_trend < 0 else "Stable",
            lstm_trend, "Rising" if lstm_trend > 0 else "Falling" if lstm_trend < 0 else "Stable"
        )
        await update.message.reply_markdown(trend_msg)
    except:
        await update.message.reply_text("⚠️ Could not analyze trend.")

async def chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        poly_data = requests.get(POLY_URL).json()["feeds"]
        lstm_data = requests.get(LSTM_URL).json()["feeds"]
        current = requests.get(CURRENT_URL).json().get("field1", None)

        times = [datetime.strptime(d["created_at"], "%Y-%m-%dT%H:%M:%SZ") for d in poly_data]
        poly_vals = [float(d["field1"]) for d in poly_data]
        lstm_vals = [float(d["field1"]) for d in lstm_data]

        plt.figure(figsize=(10,5))
        plt.plot(times, poly_vals, label='Polynomial')
        plt.plot(times, lstm_vals, label='LSTM')

        if current is not None:
            plt.axhline(float(current), color='gray', linestyle='--', label=f'Current: {current}°C')

        plt.legend()
        plt.title("Temperature Prediction vs Current (Last 10)")
        plt.xlabel("Time")
        plt.ylabel("Temp (°C)")
        plt.grid(True)

        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        await update.message.reply_photo(photo=InputFile(buf, filename="trend.png"))
        plt.close()
    except:
        await update.message.reply_text("❌ Failed to generate chart.")

# (Other functions remain unchanged)

# --- Bot Setup ---
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("trend", trend))
    app.add_handler(CommandHandler("chart", chart))
    app.add_handler(CommandHandler("explain", explain))
    app.add_handler(CommandHandler("forecast", forecast_menu))
    app.add_handler(CallbackQueryHandler(forecast_callback, pattern="^forecast_"))

    app.add_handler(MessageHandler(filters.Regex("(?i)status|prediction|temp"), status))
    app.add_handler(MessageHandler(filters.Regex("(?i)explain"), explain))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chatgpt_reply))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()

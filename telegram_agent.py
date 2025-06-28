import requests
import os
from openai import OpenAI
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# --- Configuration ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")  # Set in GitHub/Render env
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# ThingSpeak channels
POLY_URL = "https://api.thingspeak.com/channels/2749134/feeds/last.json?api_key=ELRZSYIQKSNMXSA4"
LSTM_URL = "https://api.thingspeak.com/channels/2796258/feeds/last.json?api_key=G3MHZ8U7VD4W1GH3"

# --- Functions ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome to TempCast Bot!\nType `status` or ask me anything 🤖")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        poly = requests.get(POLY_URL).json()
        lstm = requests.get(LSTM_URL).json()

        poly_temp = poly.get("field1", "N/A")
        poly_anom = "⚠️ Yes" if poly.get("field2", "0") == "1" else "✅ No"

        lstm_temp = lstm.get("field1", "N/A")
        lstm_anom = "⚠️ Yes" if lstm.get("field2", "0") == "1" else "✅ No"

        message = f"""🌡️ *Temperature Predictions*

📈 *Polynomial*
• Predicted: {poly_temp} °C
• Anomaly: {poly_anom}

🔁 *LSTM*
• Predicted: {lstm_temp} °C
• Anomaly: {lstm_anom}
"""
        await update.message.reply_markdown(message)
    except Exception as e:
        await update.message.reply_text("❌ Failed to fetch data from ThingSpeak.")

async def chatgpt_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_input}]
        )
        reply = response.choices[0].message.content
        await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text("⚠️ ChatGPT failed to respond.")

# --- Bot Setup ---
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("(?i)status|prediction|temp"), status))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chatgpt_reply))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()

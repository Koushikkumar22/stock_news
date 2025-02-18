import logging
import sqlite3
import requests
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from news_fetcher import get_stock_news
import os

# Replace with your actual bot token
TOKEN = "8056446844:AAHwhKlo8-ZI4j8ESuAmAgpx4uSyyEErneM"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Render will set this variable for you

# Set up logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# Database setup
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, stock_symbol TEXT)")
conn.commit()

# Create a Flask app
app = Flask(__name__)

# Create the bot application
application = Application.builder().token(TOKEN).build()

# Webhook endpoint to receive updates from Telegram
@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(), application.bot)
    application.process_update(update)
    return 'OK'

# Function to send news updates
async def send_news(context: CallbackContext):
    logging.info("Checking for stock news...")
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    for user_id, stock_symbol in users:
        logging.info(f"Fetching news for {stock_symbol}")
        news = get_stock_news(stock_symbol)
        if news:
            for article in news:
                logging.info(f"Sending news for {stock_symbol}")
                await context.bot.send_message(chat_id=user_id, text=article)
        else:
            logging.info(f"No news found for {stock_symbol}")

# Start command
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Welcome! Use /subscribe <stock_symbol> to get news updates.")

# Subscribe command
async def subscribe(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    stock_symbol = " ".join(context.args).upper()

    if not stock_symbol:
        await update.message.reply_text("Usage: /subscribe <stock_symbol>")
        return

    cursor.execute("INSERT OR REPLACE INTO users (user_id, stock_symbol) VALUES (?, ?)", (user_id, stock_symbol))
    conn.commit()

    await update.message.reply_text(f"Subscribed to news updates for {stock_symbol}")

# Unsubscribe command
async def unsubscribe(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    cursor.execute("DELETE FROM users WHERE user_id=?", (user_id,))
    conn.commit()

    await update.message.reply_text("Unsubscribed from stock news updates.")

# Add handlers to your bot
def setup_bot():
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))

# Set the webhook URL for your bot
application.bot.set_webhook(url=WEBHOOK_URL + "/webhook")

# Run the Flask app
if __name__ == "__main__":
    setup_bot()  # Ensure bot handlers are set up before running the Flask app
    app.run(host="0.0.0.0", port=5000)


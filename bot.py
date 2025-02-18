import logging
import sqlite3
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from news_fetcher import get_stock_news

# Replace with your actual bot token
TOKEN = "8056446844:AAHwhKlo8-ZI4j8ESuAmAgpx4uSyyEErneM"

# Set up logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# Database setup
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, stock_symbol TEXT)")
conn.commit()

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

# Main function
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("subscribe", subscribe))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe))

    # Schedule job to run every **1 minute**
    job_queue = app.job_queue
    job_queue.run_repeating(send_news, interval=60, first=10)  # Runs every 60 seconds

    app.run_polling()

if __name__ == "__main__":
    main()


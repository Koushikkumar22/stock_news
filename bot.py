import logging
import sqlite3
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from apscheduler.schedulers.background import BackgroundScheduler
from news_fetcher import get_stock_news

# Hardcoded bot token (for this example)
TOKEN = "8056446844:AAHwhKlo8-ZI4j8ESuAmAgpx4uSyyEErneM"

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Ensure database exists and is initialized
def init_db():
    conn = sqlite3.connect("users.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, stock_symbol TEXT)"
    )
    conn.commit()
    conn.close()

init_db()

# Function to send news updates (synchronous version for job queue)
def send_news(context: CallbackContext):
    logging.info("Checking for stock news...")
    # Create a new connection for thread safety
    conn = sqlite3.connect("users.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    for user_id, stock_symbol in users:
        logging.info(f"Fetching news for {stock_symbol}")
        news = get_stock_news(stock_symbol)
        if news:
            for article in news:
                logging.info(f"Sending news for {stock_symbol}")
                context.bot.send_message(chat_id=user_id, text=article)
        else:
            logging.info(f"No news found for {stock_symbol}")
    conn.close()

# Start command handler
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Welcome! Use /subscribe <stock_symbol> to get news updates.")

# Subscribe command handler
async def subscribe(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    stock_symbol = " ".join(context.args).upper()
    if not stock_symbol:
        await update.message.reply_text("Usage: /subscribe <stock_symbol>")
        return

    conn = sqlite3.connect("users.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users (user_id, stock_symbol) VALUES (?, ?)", (user_id, stock_symbol))
    conn.commit()
    conn.close()

    await update.message.reply_text(f"Subscribed to news updates for {stock_symbol}")

# Unsubscribe command handler
async def unsubscribe(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    conn = sqlite3.connect("users.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

    await update.message.reply_text("Unsubscribed from stock news updates.")

# Main function
def main():
    # Create the Application (bot instance)
    app = Application.builder().token(TOKEN).build()

    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("subscribe", subscribe))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe))

    # Schedule job to run every 1 minute (60 seconds), starting after 10 seconds
    job_queue = app.job_queue
    job_queue.run_repeating(send_news, interval=60, first=10)

    logging.info("Bot is running using long polling...")
    app.run_polling()

if __name__ == "__main__":
    main()


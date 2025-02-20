import logging
import sqlite3
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from news_fetcher import get_stock_news

# Hardcoded bot token
TOKEN = "8056446844:AAHwhKlo8-ZI4j8ESuAmAgpx4uSyyEErneM"

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Ensure database exists and is initialized
def init_db():
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, stock_symbol TEXT)"
        )
        conn.commit()

init_db()

# Synchronous function to send news updates
def send_news(context: CallbackContext):
    logging.info("Checking for stock news...")
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()

    for user_id, stock_symbol in users:
        logging.info(f"Fetching news for {stock_symbol}")
        news = get_stock_news(stock_symbol)
        if news:
            for article in news:
                logging.info(f"Sending news for {stock_symbol}")
                try:
                    context.bot.send_message(chat_id=user_id, text=article)
                except Exception as e:
                    logging.error(f"Error sending message to {user_id}: {e}")
        else:
            logging.info(f"No news found for {stock_symbol}")

# Start command handler (remains async)
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Welcome! Use /subscribe <stock_symbol> to get news updates.")

# Subscribe command handler (remains async)
async def subscribe(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    stock_symbol = " ".join(context.args).upper()
    if not stock_symbol:
        await update.message.reply_text("Usage: /subscribe <stock_symbol>")
        return

    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO users (user_id, stock_symbol) VALUES (?, ?)", (user_id, stock_symbol))
        conn.commit()

    await update.message.reply_text(f"Subscribed to news updates for {stock_symbol}")

# Unsubscribe command handler (remains async)
async def unsubscribe(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE user_id=?", (user_id,))
        conn.commit()

    await update.message.reply_text("Unsubscribed from stock news updates.")

# Main function to start the bot
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("subscribe", subscribe))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe))

    # Use APScheduler for job scheduling
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_news, IntervalTrigger(minutes=1), id="send_stock_news")
    scheduler.start()

    logging.info("Bot is running using long polling...")
    app.run_polling()

if __name__ == "__main__":
    main()



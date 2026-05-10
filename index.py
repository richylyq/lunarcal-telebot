import os, csv
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from lunar_python import Solar
from dotenv import load_dotenv


# load the .env file
load_dotenv()

# Config
TOKEN = os.getenv("TOKEN")
USER_ID = os.getenv("USER_ID")
CSV_FILE = 'events.csv'
EVENTS = {}

def load_events():
    """Reads events from the CSV file and returns a dictionary."""
    try:
        with open(CSV_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            data = {row['date']: row['name'] for row in reader}
    except FileNotFoundError:
        print(f"Error: {CSV_FILE} not found!")

    return data

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reponds to /start"""
    await update.message.reply_text("Lunar Bot is active! I will remind you of upcoming Lunar events!")

async def list_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responds to /list"""
    today = datetime.now()
    solar = Solar.fromYmd(today.year, today.month, today.day)
    lunar = solar.getLunar()    
    # month_day = (lunar.getMonth(), lunar.getDay())
    lunar_str = f"{lunar.getMonthInChinese()}月{lunar.getDayInChinese()}日"

    EVENTS = load_events()
    response = f"Today is {lunar_str} \n\n📅 **Upcoming Lunar Events:**\n\n"
    for date, name in EVENTS.items():
        month, day = date.split('-')
        response += f"• *{month}月 {day}日:* {name}\n"
    
    # parse_mode='Markdown' allows bold/italic text   
    await update.message.reply_text(text=response, parse_mode='Markdown')
    

async def check_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responds to /check"""
    
    # 2. Define the lead times we care about
    ## Key = days from now, Value = label for the message
    LEAD_TIMES = {
        31: "About 1 months time",
        7: "In 1 week",
        1: "Tomorrow",
        0: "TODAY"
    }

    today = datetime.now()
    found_event = False

    for days_ahead, label in LEAD_TIMES.items():
        # Look at the date (today + 0, 1, or 7 days)
        target_date = today + timedelta(days=days_ahead)

        # Convert that specific date to Lunar
        solar = Solar.fromYmd(target_date.year, target_date.month, target_date.day)
        lunar = solar.getLunar()    

        month_day = (lunar.getMonth(), lunar.getDay())

        if month_day in EVENTS:
            event_name = EVENTS[month_day]
            lunar_str = f"{lunar.getMonthInChinese()}月{lunar.getDayInChinese()}日"

            message = (
                f"🔔 *Lunar Calendar Reminder*\n\n"
                f"⏰ *When:* {label} ({target_date.strftime('%d %b')})\n"
                f"🎲 *Event:* {event_name}\n"
                f"🗓️ *Lunar Date:* {lunar_str}"
            )

            await update.message.reply_text(chat_id=USER_ID, text=message, parse_mode='Markdown')
            found_event = True

    if not found_event:
        print(f"Checked {today.strftime('%d-%m-%Y')}: No upcoming events.")
        await update.message.reply_text(f"Checked {today.strftime('%d-%m-%Y')}: No upcoming events.")

if __name__ == "__main__":
    if not TOKEN:
        print("ERROR: TOKEN not found in environment!")
    else:
        app = ApplicationBuilder().token(TOKEN).build()

        # add commands
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("list", list_calendar))
        app.add_handler(CommandHandler("check", check_calendar))

        print("Bot is polling...")
        app.run_polling()
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import supabase

# Function to check birthdays and send wishes
async def wish_birthdays(update:Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    todayMD = datetime.now().strftime("%m-%d")
    response = supabase.rpc("get_birthdays_today", {"today_md": todayMD}).execute()
    for record in response.data:
        print(record['username'])
        await context.bot.send_message(chat_id=record["chat_id"], text=f"Happy Birthday, {record['username']}! 🎉")

from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import supabase

# Function to check birthdays and send wishes
async def wish_birthdays(update:Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    today = datetime.now()
    response = supabase.table("your_table_name") \
                        .select("*") \
                        .eq("birthday.month", today.month) \
                        .eq("birthday.day", today.day) \
                        .execute()
    for record in response.data:
        print(record['username'])
        await context.bot.send_message(chat_id=record["chat_id"], text=f"Blessed Birthday, {record['username']}! 🎉")

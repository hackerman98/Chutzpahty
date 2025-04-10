import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, ContextTypes,CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from datetime import datetime
from supabase import create_client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TELEGRAM_KEY = os.getenv("TELEGRAM_KEY")


# Connect to Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Command to start the bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await log_chat_id(update,context)
    await update.message.reply_text("Welcome! Use /setbirthday <DD-MM-YYYY> to set your birthday.")

# Command to log chat id
async def log_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    chat_title = update.effective_chat.title  # Get chat title or default to "Private Chat"

    # Log the chat ID
    print(f"Chat ID: {chat_id}, Title: {chat_title}")

    if chat_title:
        # Insert or update the chat ID in Supabase
        try:
            response = supabase.table("chats").upsert({
                "chat_id": chat_id,
                "chat_title": chat_title
            }).execute()

            if not response.error:
                await update.message.reply_text(f"Chat ID {chat_id} has been logged successfully!")
            else:
                await update.message.reply_text(f"Failed to log chat ID: {response.data}")
        except Exception as e:
            await update.message.reply_text(f"An error occurred: {e}")

# Command to fetch chat IDs from Supabase and display as a selectable list
async def select_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        # Fetch chat IDs and titles from Supabase
        response = supabase.table("chats").select("chat_id, chat_title").execute()

        if response.data:
            chats = response.data

            # Create InlineKeyboardMarkup with chat options
            keyboard = [
                [InlineKeyboardButton(chat["chat_title"], callback_data=str(chat["chat_id"]))]
                for chat in chats
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Send the list of chats to the user
            await update.message.reply_text("Select a chat:", reply_markup=reply_markup)
        else:
            await update.message.reply_text("No chats found in the database.")
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {e}")

# Callback handler to process the selected chat
async def handle_chat_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    # Retrieve the selected chat_id
    selected_chat_id = query.data
    
    context.user_data["selected_chat_id"] = selected_chat_id
    await query.edit_message_text(f"You selected chat ID: {selected_chat_id}")
    
# Command to set birthday
async def set_birthday(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        user_id = update.message.from_user.id
        name = update.message.from_user.first_name
        username = update.message.from_user.username
        birthday = context.args[0]
    
        chat_id = context.user_data.get("selected_chat_id")

        if not chat_id:
            await update.message.reply_text("Please select a chat first using /selectchat.")
            return
        
        
        datetime.strptime(birthday, '%d-%m-%Y')  # Validate date format

        # Insert or update birthday in Supabase
        response = supabase.table("birthdays").upsert({
            "user_id": user_id,
            "name": name,
            "username": username,
            "birthday": birthday,
            "chat_id": chat_id
        }).execute()
        if response.status_code == 200:
            await update.message.reply_text(f"Birthday set for {name} in chat ID {chat_id}.")
        else:
            await update.message.reply_text("Failed to set birthday. Please try again.")
        await update.message.reply_text(f"Your birthday has been set to {birthday}.")
    except (IndexError, ValueError):
        await update.message.reply_text("Please use the format: /setbirthday <DD-MM-YYYY>")

# Function to check birthdays and send wishes
async def check_birthdays(update:Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    todayMD = datetime.now().strftime("%m-%d")
    response = supabase.rpc("get_birthdays_today", {"today_md": todayMD}).execute()
    for record in response.data:
        print(record['username'])
        await context.bot.send_message(chat_id=record["chat_id"], text=f"Happy Birthday, {record['username']}! 🎉")


async def command_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Start", callback_data="start")],
        [InlineKeyboardButton("Set Birthday", callback_data="setbirthday")],
        [InlineKeyboardButton("Check Birthdays", callback_data="checkbirthdays")],
        [InlineKeyboardButton("Select Chat", callback_data="selectchat")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select a command:", reply_markup=reply_markup)

# Callback handler to execute the selected command
async def handle_menu_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    # Execute the corresponding command based on the callback data
    command = query.data
    if command == "start":
        await start(update, context)
    elif command == "setbirthday":
        await update.callback_query.message.reply_text("Use /setbirthday YYYY-MM-DD to set your birthday.")
    elif command == "checkbirthdays":
        await check_birthdays(update, context)
    elif command == "selectchat":
        await select_chat(update, context)

# Main function to run the bot
def main():
    # Create the application with JobQueue enabled
    application = Application.builder().token(TELEGRAM_KEY).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("setbirthday", set_birthday))
    application.add_handler(CommandHandler("checkbirthday", check_birthdays))
    application.add_handler(CommandHandler("selectChat", select_chat))
    application.add_handler(CommandHandler("menu", command_menu))  
    application.add_handler(CallbackQueryHandler(handle_menu_selection))

    # Schedule daily birthday checks
    response = supabase.table("chats").select("chat_id").execute()

    if not response.data:
        print(f"Error fetching chat IDs")
    else:
        job_queue = application.job_queue  # Access the JobQueue

        # Schedule a daily job for each chat_id
        job_queue.run_daily(
            check_birthdays,
            time=datetime.strptime("08:00", "%H:%M").time()
        )

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
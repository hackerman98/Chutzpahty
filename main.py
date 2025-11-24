from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, ChatMemberHandler, ContextTypes,CallbackQueryHandler, MessageHandler, ConversationHandler, filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Bot
from datetime import datetime, time
from register import conv_handler
from sendPoll import send_poll_conv_handler
from birthday import wish_birthdays
from config import supabase, TELEGRAM_KEY
from pytz import timezone
from launchForm import launch, web_app_data

sgtz = timezone('Asia/Singapore')
job_time = sgtz.localize(datetime.combine(datetime.today(), time(13, 30)))

# Command to start the bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await log_chat_id(update,context)
    await update.message.reply_text("Initiliazed Chat! I am Chutzpahty, your friendly bot! I was created to handle Administrative tasks so don't mind me!")

# Command to log chat id
async def log_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    chat_title = update.effective_chat.title  # Get chat title or default to "Private Chat"
    # Log the chat ID
    print(f"Chat ID: {chat_id}, Title: {chat_title}")
    
    response = supabase.table("chats").select("*").eq("chat_id", chat_id).execute()
    if response.data:  # If chat_id exists
        # Update the name for the existing chat_id
        update_response = supabase.table("chats").update({"chat_title": chat_title}).eq("chat_id", chat_id).execute()
        
        if update_response.data:{
            print(f"Chat ID {chat_id} updated successfully!") 
        }
        
    elif chat_title:
        # Insert or update the chat ID in Supabase
        try:
            response = supabase.table("chats").upsert({
                "chat_id": chat_id,
                "chat_title": chat_title
            },on_conflict=["chat_id"]).execute()

            if not response.error:
                await update.message.reply_text(f"Chat ID {chat_id} has been logged successfully!")
            else:
                await update.message.reply_text(f"Failed to log chat ID: {response.data}")
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

async def update_chats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    bot = Bot(TELEGRAM_KEY)
    try:
        # Fetch all chat IDs from Supabase
        response = supabase.table("chats").select("chat_id").execute()
        if not response.data:
            print("No chats found in the database.")
            return

        # Iterate through each chat_id and update the chat_title
        for chat in response.data:
            chat_id = chat["chat_id"]
            try:
                # Get chat details from Telegram
                chat_details = await bot.get_chat(chat_id)
                chat_title = chat_details.title

                # Update the chat_title in Supabase
                supabase.table("chats").update({"chat_title": chat_title}).eq("chat_id", chat_id).execute()
                print(f"Updated chat_title for chat_id {chat_id}: {chat_title}")
            except Exception as e:
                print(f"Failed to fetch or update chat_id {chat_id}: {e}")
                
        await update.message.reply_text("Chats have been updated successfully!")

    except Exception as e:
        print(f"Error fetching chats from Supabase: {e}")
        
async def new_member_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    print("new_member_handler triggered")
    chat_title = update.message.chat.title
    print(chat_title)
    bot_id = context.bot.id
    for member in update.message.new_chat_members:
        
        if member.id == bot_id:
            continue
        try:
            await context.bot.send_message(
                chat_id= update.message.chat.id,
                text=(
                    f"Hi {member.full_name}! Welcome to {chat_title}!"
                )
            )
            launch
        
        except Exception as e:
            # Handle cases where the bot cannot message the user (e.g., privacy settings)
            print(f"Error sending message: {e}")

# Main function to run the bot
def main():
    # Create the application with JobQueue enabled
    application = Application.builder().token(TELEGRAM_KEY).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("wishbirthdays", wish_birthdays))
    application.add_handler(CommandHandler("updatechat", update_chats))
    application.add_handler(CommandHandler("logchatid", log_chat_id))
    application.add_handler(ChatMemberHandler(new_member_handler, ChatMemberHandler.CHAT_MEMBER))
    #application.add_handler(conv_handler)
    application.add_handler(send_poll_conv_handler)

    application.add_handler(CommandHandler("register", launch))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))  

    # ✅ Now you can safely use job_queue
    job_queue = application.job_queue
    job_time = datetime.strptime("08:00", "%H:%M")

    job_queue.run_daily(update_chats, time=job_time.time())
    job_queue.run_daily(wish_birthdays, time=job_time.time())
      
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
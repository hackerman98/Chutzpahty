
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler
from config import supabase

# Define states for the conversation
ASK_FIRST_NAME, ASK_LAST_NAME, ASK_YEAR, ASK_UNI_COURSE,ASK_UNIVERSITY, ASK_GROUP, GROUP_SELECTED, ASK_BDAYMESSAGE = range(8)


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
                    f"Hi {member.full_name}! Welcome to {chat_title}! "
                    "Help us get to know you better by registering! Just open a chat with me and /register to start!"
                )
            )
        
        except Exception as e:
            # Handle cases where the bot cannot message the user (e.g., privacy settings)
            print(f"Error sending message: {e}")
            
async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the registration process."""
    if update.effective_chat.type in ["group", "supergroup"]:
        await update.message.reply_text("Sorry m8... don't think you want to share all your secrets with me 😏 Drop me a private message!")
        return ConversationHandler.END
    
    await update.message.reply_text("Hi there! New member who this...")
    await update.message.reply_text("What is your first name?")
    return ASK_FIRST_NAME

async def ask_last_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Save the user's first name
    context.user_data["first_name"] = update.message.text
    await update.message.reply_text("What is your last name?")
    return ASK_LAST_NAME

async def ask_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["last_name"] = update.message.text
    response = supabase.table("chats").select("chat_title").execute()
    
    keyboard = [
        [InlineKeyboardButton(chat_title["chat_title"], callback_data=chat_title["chat_title"])] for chat_title in response.data
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("Please select the group you belong to:", reply_markup=reply_markup)
    
    return ASK_GROUP

async def handle_group_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the user's group selection."""
    query = update.callback_query
    await query.answer()

    # Save the selected group in user data
    selected_group = query.data
    context.user_data["chat_title"] = selected_group
    
    response = supabase.table("chats").select("chat_id").eq("chat_title", selected_group).execute()
    context.user_data["chat_id"] = response.data[0]["chat_id"]

    # Acknowledge the selection
    await query.edit_message_text(f"I see you are from {selected_group}! I heard the leader is pretty cool!")

    # Proceed to the next step
    await update.callback_query.message.reply_text("What is your birthday? (e.g., DD-MM-YYYY)")
    return GROUP_SELECTED

async def ask_year(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Save the user's birthday
    context.user_data["birthday"] = update.message.text
    await update.message.reply_text("What year are you in?")
    return ASK_YEAR

async def ask_uni_course(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Save the user's year
    context.user_data["year"] = update.message.text
    
    if (context.user_data["year"] == "1" or context.user_data["year"] == "2"):
        await update.message.reply_text("Sheesh you are young, there is much to come!")
        
    await update.message.reply_text("What is your university and course? (E.g., NUS, Mechanical Engineering)")
    return ASK_UNI_COURSE

async def ask_bdaymessage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["uni_course"] = update.message.text
    await update.message.reply_text("Oooo, what a nice course! I hope you enjoy it!")
    await update.message.reply_text("Lastly, if it was your birthday...What birthday message would you like to receive?")
    return ASK_BDAYMESSAGE
    
async def save_user_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Save the user's year
    context.user_data["birthday_message"] = update.message.text

    user_data = {
            "user_id": update.message.from_user.id,
            "username": update.message.from_user.username,
            "first_name": context.user_data["first_name"],
            "last_name": context.user_data["last_name"],
            "birthday": context.user_data["birthday"],
            "year": context.user_data["year"],
            "chat_id": context.user_data["chat_id"],
            "chat_title": context.user_data["chat_title"],
            "uni_course": context.user_data["uni_course"],
        }
    
    bdaymessage_data = {
            "user_id": update.message.from_user.id,
            "username": update.message.from_user.username,
            "first_name": update.message.from_user.full_name,
            "chat_id": context.user_data["chat_id"],
            "birthday_message": context.user_data["birthday_message"],
        }
    try:
        initialcheck = supabase.table("vg_user").select("*").eq("user_id", update.message.from_user.id).execute()
        
        if initialcheck.data:
            await update.message.reply_text("You are already registered!")
        else:
            response = supabase.table("vg_user").upsert(user_data, on_conflict=["user_id"]).execute()
        
        bdayresponse = supabase.table("birthdays").upsert(bdaymessage_data).execute()
        if bdayresponse.data and response.data:
            await update.message.reply_text("Thank you! Your details have been saved.")
        
        else:
            await update.message.reply_text("There was an error saving your details. Please try again 😔")
            
    except Exception as e:
        await update.message.reply_text("❗ There was an error somewhere somehow 🙃. Please tell somebody so they can fix it...❗")
        print(f"Error saving user data: {e}")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Okay, the process has been canceled.")
    return ConversationHandler.END

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Notify the user that the process is restarting
    await update.message.reply_text("Let's start again!")
    
    # Start from the first question
    await update.message.reply_text("What is your first name?")
    return ASK_FIRST_NAME

conv_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.TEXT & filters.Regex("^/register$"), register)],
    states={
        ASK_FIRST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_last_name)],
        ASK_LAST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_group)],
        ASK_GROUP: [CallbackQueryHandler(handle_group_selection)],
        GROUP_SELECTED: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_year)],
        ASK_YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_uni_course)],
        ASK_UNI_COURSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_bdaymessage)],
        ASK_BDAYMESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_user_data)],
    },
    fallbacks=[
        MessageHandler(filters.COMMAND & filters.Regex("^/cancel$"), cancel),
        MessageHandler(filters.COMMAND & filters.Regex("^/restart$"), restart),
    ],
    
)


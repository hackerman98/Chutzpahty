from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler, CallbackContext
from config import supabase


ASK_QUESTION, ASK_OPTIONS, ASK_CHAT = range(3)

async def prompt_for_poll(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Creating a new poll!")
    await update.message.reply_text("What is the poll question?")
    return ASK_QUESTION

async def ask_options(update: Update, context: CallbackContext) -> None:
   
    context.user_data['poll_question'] = update.message.text
    await update.message.reply_text("Now provide options for the poll, separated by paragraphs.")
    
    return ASK_OPTIONS
   
        
async def ask_chat(update: Update, context: CallbackContext) -> None:
    user_input = update.message.text
    print(f"User input for options: {user_input}")
    options = [option.strip() for option in user_input.split('\n') if option.strip()]
    print(f"Parsed options: {options}")
    if len(options) < 2:
        await update.message.reply_text("Options should be at least 2. Please try again!")
        return ASK_OPTIONS

    context.user_data['poll_options'] = options   
    
    response = supabase.table("chats").select("chat_title").execute()
    keyboard = [
        [InlineKeyboardButton(chat_title["chat_title"], callback_data=chat_title["chat_title"])] for chat_title in response.data
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("Which chat do you want to send the poll to?", reply_markup=reply_markup)
    return ASK_CHAT

async def send_poll(update: Update, context: CallbackContext) -> None:
    print("send_poll triggered")
    query = update.callback_query
    await query.answer()

    # Save the selected group in user data
    selected_group = query.data
    print(f"Selected group: {selected_group}")
    
    context.user_data["chat_title"] = selected_group
    response = supabase.table("chats").select("chat_id").eq("chat_title", selected_group).execute()
    context.user_data["chat_id"] = response.data[0]["chat_id"]
    
    print(f"Chat ID: {context.user_data['chat_id']}")
    
    chat_id = context.user_data["chat_id"]
    question = context.user_data["poll_question"]
    options = context.user_data['poll_options']
    
    await query.edit_message_text(f"Poll created! Sending to {selected_group}...")
    
    # Send the poll
    await context.bot.send_poll(
        chat_id=chat_id,
        question=question,
        options=options,
        is_anonymous=False
    )
    
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Okay, the process has been canceled.")
    return ConversationHandler.END

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Notify the user that the process is restarting
    await update.message.reply_text("Let's start again!")
    
    # Start from the first question
    await update.message.reply_text("What is the poll question?")
    return ASK_QUESTION
    
send_poll_conv_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.TEXT & filters.Regex("^/poll$"), prompt_for_poll)],
    states={
        ASK_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_options)],
        ASK_OPTIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_chat)],
        ASK_CHAT: [CallbackQueryHandler(send_poll)],
        },
    fallbacks=[
        MessageHandler(filters.COMMAND & filters.Regex("^/cancel$"), cancel),
        MessageHandler(filters.COMMAND & filters.Regex("^/restart$"), restart),
    ],
    
)

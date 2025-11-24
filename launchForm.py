import supabase
from telegram import KeyboardButton, ReplyKeyboardMarkup, Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import  ContextTypes

from telegram.constants import ChatType

async def launch(update: Update, context):
    # Check if private chat
    # if update.effective_chat.type != ChatType.PRIVATE:
    #     bot_username = context.bot.username
    #     keyboard = [[
    #         InlineKeyboardButton("📝 Register Here", url=f"https://t.me/{bot_username}?start=register")
    #     ]]
    #     reply_markup = InlineKeyboardMarkup(keyboard)
    #     await update.message.reply_text(
    #         "⚠️ Registration must be done in private chat.\nClick below to start:",
    #         reply_markup=reply_markup
    #     )
    #     return
    
    # Private chat - show web app button


    
    # keyboard = [[
    #     KeyboardButton("📝 Launch Form", web_app=WebAppInfo(url="https://hackerman98.github.io/Chutzpahty/"))
    # ]]
    reply_markup = ReplyKeyboardMarkup.from_button(KeyboardButton("📝 Launch Form", web_app=WebAppInfo(url="https://hackerman98.github.io/Chutzpahty/")),)
    await update.message.reply_text("Click the button to open the form:", reply_markup=reply_markup)


    
# Handle data sent back from the form
async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get the data sent from your HTML form
    print("=" * 50)
    print("✅ WEB APP DATA HANDLER TRIGGERED!")
    print("=" * 50)
    
    data = update.message.web_app_data.data
    
    # Parse the JSON data
    import json
    form_data = json.loads(data)
    
    # Send confirmation to user
    # await update.message.reply_text(
    #     f"✅ Form received!\n\n"
    #     f"Name: {form_data['name']}\n"
    #     f"Birthday: {form_data['birthday']}\n" 
    #     f"Course: {form_data['course']}\n" 
    #     f"Year: {form_data['year']}\n" 
    #     f"University: {form_data['university']}\n"
    #     f"Group: {form_data['group']}\n"
    #     f"Fun Fact: {form_data['funfact']}"
    # )




    user_data = {
        "user_id": context.user_data.get("user_id"),
        "username": context.user_data.get("username"),
        "name": form_data['name'],
        "birthday": form_data['birthday'],
        "course": form_data['course'],
        "year": form_data['year'],
        "university": form_data['university'],
        "funfact": form_data['fun_fact'],
        "chat_id": update.effective_chat.id
    }

    try:
        initialcheck = supabase.table("user").select("*").eq("user_id", user_data["user_id"]).execute()
        
        if initialcheck.data:
            await update.message.reply_text("You have already registered! Updating details...")
            
            #update existing user
            response = supabase.table("user").update(user_data).eq("user_id", user_data["user_id"]).execute()    

        else:
            response = supabase.table("user").upsert(user_data, on_conflict=["user_id"]).execute()
    
        if response.data:
            await update.message.reply_text("Thank you for registering! Welcome to the chat group!")
        
        else:
            await update.message.reply_text("There was an error saving your details. Please try again 😔")
            
    except Exception as e:
        await update.message.reply_text("❗ There was an error somewhere somehow 🙃. Please tell somebody so they can fix it...❗")
        print(f"Error saving user data: {e}")

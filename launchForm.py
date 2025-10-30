import supabase
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import  ContextTypes

async def launch(update: Update, context: ContextTypes.DEFAULT_TYPE):

    print("launch command triggered")

    # Create a button that opens your Mini App
    keyboard = [
        [InlineKeyboardButton(
            "📝 Launch Form", 
            web_app=WebAppInfo(url="https://hackerman98.github.io/Chutzpahty/")
        )]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Click the button below to fill out the form for us to get to know you better:",
        reply_markup=reply_markup
    )

# Handle data sent back from the form
async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get the data sent from your HTML form
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
        "user_id": form_data['user_id'],
        "username": form_data['username'],
        "name": form_data['name'],
        "birthday": form_data['birthday'],
        "course": form_data['course'],
        "year": form_data['year'],
        "university": form_data['university'],
        "group": form_data['group'],
        "funfact": form_data['funfact'],
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
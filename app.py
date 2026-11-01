import os
import time
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.request import HTTPXRequest

# Aapka Telegram Bot Token
BOT_TOKEN = "9121435413:AAGOyU8sCeJZohrJb45GhaO8tdpFxggSA48"

# Aapka Render API URL
API_BASE_URL = "https://guest-gen-li9q.onrender.com/v3/generate"

# User states track karne ke liye
user_data_store = {}

REGION_LIST = ["ID", "BR", "IND", "VN", "TH", "ME", "PK", "BD", "TW", "CIS", "SAC"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    row = []
    for reg in REGION_LIST:
        row.append(InlineKeyboardButton(reg, callback_data=f"reg_{reg}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 **Free Fire Account Generator Bot**\n\n"
        "Sabse pehle apna **Region / Server** select karein:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    chat_id = query.message.chat_id
    
    if data.startswith("reg_"):
        region = data.split("_")[1]
        user_data_store[chat_id] = {"region": region}
        
        await query.edit_message_text(
            f"✅ Server Selected: **{region}**\n\n"
            "Ab apne accounts ke liye **Custom Name Prefix** bhejiye (Jaise: `Toxic`):",
            parse_mode="Markdown"
        )
        user_data_store[chat_id]["step"] = "waiting_name"

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    text = update.message.text.strip()
    
    if chat_id not in user_data_store:
        await update.message.reply_text("Pehle /start command ka use karein!")
        return
    
    step = user_data_store[chat_id].get("step")
    
    if step == "waiting_name":
        user_data_store[chat_id]["name"] = text
        user_data_store[chat_id]["step"] = "waiting_password"
        await update.message.reply_text("🔐 Ab **Password Prefix** bhejiye (Jaise: `Pass123`):")
        
    elif step == "waiting_password":
        user_data_store[chat_id]["password"] = text
        user_data_store[chat_id]["step"] = "waiting_count"
        await update.message.reply_text("🔢 Ab kitne accounts generate karne hain wo **Amount** likhein (Jaise: `1000`, `10000`, ya `50000`):")
        
    elif step == "waiting_count":
        try:
            target_count = int(text)
            if target_count < 1 or target_count > 100000:
                await update.message.reply_text("⚠️ Kripya 1 se 100,000 ke beech ki sankhya dalein.")
                return
        except ValueError:
            await update.message.reply_text("⚠️ Kripya valid number enter karein!")
            return
            
        data = user_data_store[chat_id]
        region = data["region"]
        name = data["name"]
        password = data["password"]
        
        msg = await update.message.reply_text(f"🚀 Generating 0 / {target_count} accounts... Fast speed mode on!")
        
        all_accounts = []
        batch_size = 500  # Ek baar me bade batches mangenge taaki speed fast ho
        
        try:
            while len(all_accounts) < target_count:
                remaining = target_count - len(all_accounts)
                current_count = min(batch_size, remaining)
                
                url = f"{API_BASE_URL}?count={current_count}&name={name}&password={password}&region={region}&debug=0"
                
                # Fast Request loop
                fetched = False
                for attempt in range(3):
                    try:
                        response = requests.get(url, timeout=120)
                        res_json = response.json()
                        
                        if res_json.get("success"):
                            batch_accs = res_json.get("accounts", [])
                            if batch_accs:
                                all_accounts.extend(batch_accs)
                                fetched = True
                                break
                    except Exception:
                        time.sleep(0.5)
                
                if not fetched:
                    time.sleep(1)
                
                try:
                    await msg.edit_text(f"🚀 Generating {len(all_accounts)} / {target_count} accounts... Please wait!")
                except Exception:
                    pass
                
                time.sleep(0.1)
            
            if len(all_accounts) > 0:
                await msg.edit_text(f"✅ Generated {len(all_accounts)} accounts! Creating file...")
                
                # Detailed file formatting
                file_content = "========================================\n"
                file_content += "     TOXIC FF LEAKS - ACCOUNT LIST      \n"
                file_content += "========================================\n\n"
                
                for idx, acc in enumerate(all_accounts, 1):
                    uid_val = acc.get('uid', 'N/A')
                    acc_id_val = acc.get('account_id', 'N/A')
                    acc_pass = acc.get('password', 'N/A')
                    acc_name = acc.get('name', 'N/A')
                    acc_reg = acc.get('region', 'N/A')
                    rarity = acc.get('rarity', 'NORMAL')
                    score = acc.get('rarity_score', 0)
                    device = acc.get('device_model', 'N/A')
                    device_id = acc.get('device_id', 'N/A')
                    created = acc.get('created_at', 'N/A')
                    
                    file_content += f"[{idx}] Account Details:\n"
                    file_content += f"----------------------------------------\n"
                    file_content += f"UID        : {uid_val}\n"
                    file_content += f"Account ID : {acc_id_val}\n"
                    file_content += f"Password   : {acc_pass}\n"
                    file_content += f"Name       : {acc_name}\n"
                    file_content += f"Region     : {acc_reg}\n"
                    file_content += f"Rarity     : {rarity} (Score: {score})\n"
                    file_content += f"Device     : {device}\n"
                    file_content += f"Device ID  : {device_id}\n"
                    file_content += f"Created At : {created}\n"
                    file_content += f"----------------------------------------\n\n"
                
                file_path = f"accounts_{chat_id}.txt"
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(file_content)
                
                # Send file to user
                with open(file_path, "rb") as f:
                    await context.bot.send_document(
                        chat_id=chat_id,
                        document=f,
                        filename="accounts.txt",
                        caption=f"🎉 **Generation Complete!**\n📊 Total Accounts: {len(all_accounts)}[span_1](start_span)[span_1](end_span)\n🌍 Region: {region}"
                    )
                
                os.remove(file_path)
                await msg.delete()
            else:
                await msg.edit_text("❌ Account generation fail ho gaya. Dubara try karein.")
                
        except Exception as e:
            await msg.edit_text(f"❌ Error: {str(e)}")
            
        if chat_id in user_data_store:
            del user_data_store[chat_id]

def main():
    request_config = HTTPXRequest(
        connect_timeout=60.0,
        read_timeout=60.0,
        write_timeout=60.0,
        pool_timeout=60.0
    )
    
    app = Application.builder().token(BOT_TOKEN).request(request_config).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    print("🤖 High-speed Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

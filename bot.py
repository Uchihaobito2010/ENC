import os
import time
import base64
import marshal
import random
import zlib
import requests
import telebot
from telebot import types
import ssl
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Bot Token
BOT_TOKEN = "8465522008:AAF-oFTrmuAOQ_eReyNyTcTfOsXN6OYJ1pk"
ADMIN_IDS = [8033743774]  # Add admin user IDs here

# Configure bot with retry settings
bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None, threaded=True)

user_selections = {}

zlb = lambda data: zlib.compress(data)
b64 = lambda data: base64.b64encode(data)
b32 = lambda data: base64.b32encode(data)
b16 = lambda data: base64.b16encode(data)
mar = lambda data: marshal.dumps(compile(data, 'module', 'exec'))

@bot.message_handler(commands=['start'])
def start(message):
    try:
        send_main_menu(message.chat.id)
    except Exception as e:
        print(f"Error in start command: {e}")
        bot.send_message(message.chat.id, "⚠️ Bot is starting up, please try again in a moment...")

def send_main_menu(chat_id):
    buttons = [
        types.InlineKeyboardButton("🔹 Base64", callback_data='base64'),
        types.InlineKeyboardButton("🔹 Marshal", callback_data='marshal'),
        types.InlineKeyboardButton("🔹 Zlib", callback_data='zlib'),
        types.InlineKeyboardButton("🔹 Advanced", callback_data='advanced'),
        types.InlineKeyboardButton("🔹 B16", callback_data='base16'),
        types.InlineKeyboardButton("🔹 B32", callback_data='base32'),
        types.InlineKeyboardButton("🔹 MZlib", callback_data='marshal_zlib'),
        types.InlineKeyboardButton("🔹 Complex", callback_data='complex'),
        types.InlineKeyboardButton("ℹ️ Bot Info", callback_data='bot_info')
    ]
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(*buttons)
    try:
        bot.send_message(chat_id, "🔒 Choose an encryption method:", reply_markup=markup)
    except Exception as e:
        print(f"Error sending main menu: {e}")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    
    try:
        if call.data == "bot_info":
            send_bot_info(call.message)
        elif call.data == "back":
            bot.edit_message_text("🔒 Choose an encryption method:", chat_id=chat_id, message_id=call.message.message_id)
            send_main_menu(chat_id)  
        else:
            user_selections[chat_id] = call.data
            bot.send_message(chat_id, f"📂 Send a file for {call.data} encryption.")
    except Exception as e:
        print(f"Error handling callback: {e}")
        bot.answer_callback_query(call.id, "❌ Error processing request. Please try again.")

def send_bot_info(message):
    info_text = """
🤖 <b>Bot Name:</b> Secure File Encryptor

<blockquote>💻 <b>Code Language :</b> Python
🛠 <b>Created By :</b> Bot Developer
</blockquote>

<b>This bot encrypts Python scripts using various encoding methods, making them harder to reverse-engineer.</b>
"""
    markup = types.InlineKeyboardMarkup()
    back_button = types.InlineKeyboardButton("⬅️ Back", callback_data="back")
    markup.add(back_button)
    try:
        bot.edit_message_text(info_text, chat_id=message.chat.id, message_id=message.message_id, parse_mode="HTML", reply_markup=markup)
    except Exception as e:
        print(f"Error sending bot info: {e}")

@bot.message_handler(content_types=['document'])
def receive_file(message):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if chat_id not in user_selections:
            bot.send_message(chat_id, "❌ Please select an encryption method first!")
            return

        encryption_type = user_selections[chat_id]

        # Send reaction
        try:
            send_reaction(chat_id, message.message_id, "👨🏻‍💻")
        except:
            pass  # Skip if reaction fails

        # Download file
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        file_id = str(random.randint(1000, 9999))
        file_name = f"{encryption_type}-{file_id}.py"

        with open(file_name, 'wb') as f:
            f.write(downloaded_file)

        # Show loading animation
        loading_msg = bot.send_message(chat_id, "⚙️ Processing your file...\n[0%] █▒▒▒▒▒▒▒▒▒")
        for i in range(1, 101, random.randint(7, 14)):
            time.sleep(0.02)
            try:
                bot.edit_message_text(chat_id=chat_id, message_id=loading_msg.message_id, text=f"⚙️ Processing your file...\n[{i}%] {'█' * (i // 10)}{'▒' * (10 - (i // 10))}")
            except:
                break

        # Encrypt file
        encrypted_code = encrypt_file(encryption_type, file_name)

        with open(file_name, 'w') as f:
            f.write(encrypted_code)

        # Delete loading message
        try:
            bot.delete_message(chat_id, loading_msg.message_id)
        except:
            pass

        # Send encrypted file
        with open(file_name, 'rb') as file:
            bot.send_document(chat_id, file)

        os.remove(file_name)  

    except Exception as e:
        print(f"Error receiving file: {e}")
        try:
            bot.send_message(chat_id, f"❌ Error: {str(e)[:200]}")
        except:
            pass

def send_reaction(chat_id, message_id, emoji):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/setMessageReaction"
        data = {
            "chat_id": chat_id,
            "message_id": message_id,
            "reaction": [{"type": "emoji", "emoji": emoji}]
        }
        requests.post(url, json=data, timeout=5, verify=False)
    except:
        pass  # Skip if reaction fails

def encrypt_file(method, file_name):
    try:
        original_code = open(file_name, "r", encoding='utf-8').read().encode('utf-8')
    except:
        original_code = open(file_name, "r", encoding='latin-1').read().encode('utf-8')
    
    header = "\n\n"
    footer = "\n\n
    try:
        if method == "base64":
            encoded = b64(original_code)[::-1]
            return f"{header}_ = lambda __ : __import__('base64').b64decode(__[::-1]);exec((_)({encoded})) {footer}"

        elif method == "marshal":
            encoded = marshal.dumps(compile(original_code.decode(), 'module', 'exec'))
            return f"{header}import marshal\nexec(marshal.loads({encoded})) {footer}"

        elif method == "zlib":
            encoded = b64(zlb(original_code))[::-1]
            return f"{header}_ = lambda __ : __import__('zlib').decompress(__import__('base64').b64decode(__[::-1]));exec((_)({encoded})) {footer}"

        elif method == "base16":
            encoded = b16(zlb(original_code))[::-1]
            return f"{header}_ = lambda __ : __import__('zlib').decompress(__import__('base64').b16decode(__[::-1]));exec((_)({encoded})) {footer}"

        elif method == "base32":
            encoded = b32(zlb(original_code))[::-1]
            return f"{header}_ = lambda __ : __import__('zlib').decompress(__import__('base64').b32decode(__[::-1]));exec((_)({encoded})) {footer}"

        elif method == "marshal_zlib":
            encoded = b64(zlb(mar(original_code)))[::-1]
            return f"{header}import marshal, zlib, base64\nexec(marshal.loads(zlib.decompress(base64.b64decode({encoded})))) {footer}"

        elif method == "advanced":
            var1, var2, var3 = random.sample(['x', 'y', 'z', 'p', 'q', 'r'], 3)
            encoded = b64(zlb(mar(original_code)))[::-1]
            return f"""{header}
import base64, zlib, marshal
{var1} = lambda {var2}: marshal.loads(zlib.decompress(base64.b64decode({var2})))
{var3} = "{encoded}"
exec({var1}({var3})) {footer}"""

        elif method == "complex":
            encoded = b64(zlb(mar(original_code)))[::-1]
            return f"""{header}import base64, zlib, marshal, hashlib
exec(marshal.loads(zlib.decompress(base64.b64decode({encoded})))) {footer}"""

        return "# Error Invalid Encryption Method"
    except Exception as e:
        return f"# Error during encryption: {str(e)[:100]}"

if __name__ == "__main__":
    print("🤖 Bot is starting...")
    
    # Add retry logic for connection issues
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            print(f"Attempting to start bot (attempt {retry_count + 1}/{max_retries})...")
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            retry_count += 1
            print(f"Connection error (attempt {retry_count}): {str(e)[:100]}")
            if retry_count < max_retries:
                print("Waiting 10 seconds before retry...")
                time.sleep(10)
            else:
                print(f"Failed to start bot after {max_retries} attempts")
                break

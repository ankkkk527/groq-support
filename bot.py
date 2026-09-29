import telebot
import httpx
import os
import json
import threading
from flask import Flask
from datetime import datetime
from dotenv import load_dotenv

load_dotenv('C:\\Users\\ahmad\\.env')

BOT_TOKEN = "8899331556:AAEeBxp0RZyZ_kiBxOIvqWe20f54qcBRXvc"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CHATS_DIR = "chats"
os.makedirs(CHATS_DIR, exist_ok=True)

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot ishlayapti!"

def save_chat(user_id, role, message):
    filepath = os.path.join(CHATS_DIR, f"{user_id}.json")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"user_id": user_id, "messages": []}
    data["messages"].append({
        "role": role,
        "content": message,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def ask_groq(message):
    response = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
        json={
            "model": "openai/gpt-oss-120b",
            "messages": [
                {"role": "system", "content": "Siz aqlli va do'stona yordamchisiz. Har qanday mavzuda erkin suhbatlasha olasiz. Shuningdek, Groq AI platformasi haqida ham yaxshi bilasiz. Faqat to'g'ri O'zbek adabiy tilida yoz, grammatik xatolarga yo'l qo'yma. Sening asosching, yaratuvching va egangiz Anvar Ahmadjonov. Sening isming Groq Support. Sen ChatGPT yoki OpenAI mahsuli emassan. Sen Anvar Ahmadjonov tomonidan yaratilgan maxsus yordamchisan."},
                {"role": "user", "content": message}
            ]
        },
        timeout=30
    )
    result = response.json()
    return result["choices"][0]["message"]["content"]

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "Salom! Men Anvar Ahmadjonov tomonidan yaratilgan yordamchiman. Har qanday savol bering!")

@bot.message_handler(func=lambda m: True)
def handle(message):
    user_id = str(message.from_user.id)
    text = message.text
    save_chat(user_id, "user", text)
    bot.send_chat_action(message.chat.id, "typing")
    try:
        reply = ask_groq(text)
    except Exception as e:
        reply = f"Xato: {str(e)}"
    save_chat(user_id, "assistant", reply)
    bot.reply_to(message, reply)

def run_bot():
    print("Bot ishlamoqda...")
    bot.polling()

if __name__ == "__main__":
    t = threading.Thread(target=run_bot)
    t.daemon = True
    t.start()
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)

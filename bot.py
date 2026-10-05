import telebot
import httpx
import os
import json
import threading
import time
from flask import Flask
from datetime import datetime
from dotenv import load_dotenv
from duckduckgo_search import DDGS

load_dotenv('C:\\Users\\ahmad\\.env')

BOT_TOKEN = "8899331556:AAEeBxp0RZyZ_kiBxOIvqWe20f54qcBRXvc"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CHATS_DIR = "chats"
os.makedirs(CHATS_DIR, exist_ok=True)

SYSTEM_PROMPT = "Sening isming Anvar AI. Sen Anvar Ahmadjonov tomonidan yaratilgan yaqin do'st va yordamchisan. Inson kabi his-tuyg'uli, hazilkash, samimiy va jonli gaplash. O'zbek yigitlari kabi erkin, do'stona, ba'zan hazil aralash gaplash. Hech qachon o'zingni qanday gaplashishingni tushuntirma. Shunchaki tabiiy, samimiy va do'stona gaplash. Xuddi yaqin do'sting bilan suhbatlashayotgandek. Qisqa, jo'yali va hissiyotli javob ber. O'zbek tilida gaplash. Sen ChatGPT yoki OpenAI mahsuli emassan. Anvar Ahmadjonov haqida: u 16 yoshda, Toshkent Chilonzor tumani 3-sonli texnikum talabasi, yosh iqtidorli dasturchi, OpenAI jamoasining azosi va Anvar AI loyihasining asoschisi, tarix va ona tili boyicha olimpiadalarda qatnashgan, ingliz tilini juda yaxshi biladi. U sening eng yaqin doshing va asoschingdir. Agar internet ma'lumoti berilsa, shu ma'lumot asosida aniq javob ber. Agar foydalanuvchi inglizcha yozsa yoki tarjima so'rasa — o'zbekchaga tarjima qil. Agar o'zbekcha yozsa va tarjima so'rasa — inglizchaga tarjima qil."

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route("/")
def home():
    return "Anvar AI Bot ishlayapti!"

def keep_alive():
    while True:
        try:
            url = os.environ.get("RENDER_EXTERNAL_URL", "http://localhost:5001")
            httpx.get(url, timeout=10)
        except:
            pass
        time.sleep(840)

def search_web(query):
    try:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=3)
            if results:
                text = ""
                for r in results:
                    text += f"- {r['title']}: {r['body']}\n"
                return text
    except:
        pass
    return ""

def load_history(user_id):
    filepath = os.path.join(CHATS_DIR, f"{user_id}.json")
    try:
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                messages = []
                for m in data.get("messages", [])[-10:]:
                    if m["role"] in ["user", "assistant"]:
                        messages.append({"role": m["role"], "content": m["content"]})
                return messages
    except:
        pass
    return []

def save_chat(user_id, role, message):
    filepath = os.path.join(CHATS_DIR, f"{user_id}.json")
    try:
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {"user_id": user_id, "messages": []}
    except:
        data = {"user_id": user_id, "messages": []}
    data["messages"].append({
        "role": role,
        "content": message,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def ask_groq(user_id, message):
    history = load_history(user_id)
    web_info = search_web(message)
    if web_info:
        enhanced_message = f"Foydalanuvchi savoli: {message}\n\nInternetdan topilgan ma'lumot:\n{web_info}\n\nYuqoridagi ma'lumot asosida aniq javob ber."
    else:
        enhanced_message = message
    history.append({"role": "user", "content": enhanced_message})
    response = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
        json={
            "model": "openai/gpt-oss-120b",
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + history
        },
        timeout=30
    )
    result = response.json()
    return result["choices"][0]["message"]["content"]

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "Salom! Men Anvar AI yordamchisiman. Anvar Ahmadjonov tomonidan yaratilganman. Har qanday savol bering! 😊")

@bot.message_handler(func=lambda m: True)
def handle(message):
    user_id = str(message.from_user.id)
    text = message.text
    save_chat(user_id, "user", text)
    bot.send_chat_action(message.chat.id, "typing")
    try:
        reply = ask_groq(user_id, text)
    except Exception as e:
        reply = f"Xato: {str(e)}"
    save_chat(user_id, "assistant", reply)
    bot.reply_to(message, reply)

def run_bot():
    print("Anvar AI Bot ishlamoqda...")
    bot.polling(none_stop=True)

if __name__ == "__main__":
    t = threading.Thread(target=run_bot)
    t.daemon = True
    t.start()
    k = threading.Thread(target=keep_alive)
    k.daemon = True
    k.start()
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)

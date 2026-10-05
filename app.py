from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import os
import json
import httpx
from datetime import datetime
from duckduckgo_search import DDGS

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CHATS_DIR = os.path.join(basedir, "chats")
os.makedirs(CHATS_DIR, exist_ok=True)

SYSTEM_PROMPT = "Sening isming Anvar AI. Sen Anvar Ahmadjonov tomonidan yaratilgan yaqin do'st va yordamchisan. Inson kabi his-tuyg'uli, hazilkash, samimiy va jonli gaplash. O'zbek yigitlari kabi erkin, do'stona, ba'zan hazil aralash gaplash. Hech qachon o'zingni qanday gaplashishingni tushuntirma. Shunchaki tabiiy, samimiy va do'stona gaplash. Xuddi yaqin do'sting bilan suhbatlashayotgandek. Qisqa, jo'yali va hissiyotli javob ber. O'zbek tilida gaplash. Sen ChatGPT yoki OpenAI mahsuli emassan. Anvar Ahmadjonov haqida: u 16 yoshda, Toshkent Chilonzor tumani 3-sonli texnikum talabasi, yosh iqtidorli dasturchi, OpenAI jamoasining azosi va Anvar AI loyihasining asoschisi, tarix va ona tili boyicha olimpiadalarda qatnashgan, ingliz tilini juda yaxshi biladi. U sening eng yaqin doshing va asoschingdir. Agar internet ma'lumoti berilsa, shu ma'lumot asosida aniq javob ber."

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

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        user_id = data.get("user_id", "guest")
        message = data.get("message", "")
        save_chat(user_id, "user", message)
        history = load_history(user_id)

        web_info = search_web(message)
        if web_info:
            enhanced_message = f"Foydalanuvchi savoli: {message}\n\nInternetdan topilgan ma'lumot:\n{web_info}\n\nYuqoridagi ma'lumot asosida aniq javob ber."
        else:
            enhanced_message = message

        history_with_search = history[:-1] + [{"role": "user", "content": enhanced_message}] if history else [{"role": "user", "content": enhanced_message}]

        response = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + history_with_search
            },
            timeout=30
        )
        result = response.json()
        reply = result["choices"][0]["message"]["content"]
        save_chat(user_id, "assistant", reply)
        return jsonify({"reply": reply})
    except Exception as e:
        print(f"Xato: {e}")
        return jsonify({"reply": f"Xato: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

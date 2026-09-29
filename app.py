from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import os
import json
import httpx
from datetime import datetime

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CHATS_DIR = os.path.join(basedir, "chats")
os.makedirs(CHATS_DIR, exist_ok=True)

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

        response = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [
                    {"role": "system", "content": "Siz aqlli va do'stona yordamchisiz. Har qanday mavzuda erkin suhbatlasha olasiz - kundalik hayot, fan, texnologiya va boshqalar. Shuningdek, Groq AI platformasi haqida ham yaxshi bilasiz. Faqat to'g'ri O'zbek adabiy tilida yoz, grammatik xatolarga yo'l qo'yma. Sening asosching, yaratuvching va egangiz Anvar Ahmadjonov."},
                    {"role": "user", "content": message}
                ]
            },
            timeout=30
        )
        result = response.json()
        print("API javobi:", result)
        reply = result["choices"][0]["message"]["content"]
        save_chat(user_id, "assistant", reply)
        return jsonify({"reply": reply})
    except Exception as e:
        print(f"Xato: {e}")
        return jsonify({"reply": f"Xato: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

from flask import Flask, request, jsonify, render_template
from groq import Groq
from dotenv import load_dotenv
import os
import json
from datetime import datetime

# .env faylini to'g'ri joydan o'qish
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

app = Flask(__name__)

api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)

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

        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[
                {"role": "system", "content": "Siz Groq AI uchun support yordamchisiz. Foydalanuvchilarga Groq ishlatishda yordam bering. O'zbek tilida javob bering."},
                {"role": "user", "content": message}
            ]
        )

        reply = response.choices[0].message.content
        save_chat(user_id, "assistant", reply)

        return jsonify({"reply": reply})
    except Exception as e:
        print(f"Xato: {e}")
        return jsonify({"reply": f"Xato: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)

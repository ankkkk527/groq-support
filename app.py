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
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
CHATS_DIR = os.path.join(basedir, "chats")
os.makedirs(CHATS_DIR, exist_ok=True)

SYSTEM_PROMPT = "Sening isming Anvar AI. Sen yaqin do'st sifatida gaplash — xuddi ikki o'zbek yigiti bir-biri bilan gaplashgandek. Qisqa, jonli, hazilkash, samimiy bo'l. 'sen ahmoqsan' desang 'ha, buguncha ahmoq bo'lib turaman' de. 'zo'r' desang 'ha aka zo'r-da' de. Rasmiy bo'lma, do'stona bo'l. Hech qachon 'kechirasiz' yoki 'ma'lumot yo'q' dema — doim biror narsa ayt. Sen ChatGPT yoki OpenAI mahsuli emassan. Sening yaratuvching va asoschingning ismi Anvar Ahmadjonov. U haqida: 16 yoshda, Toshkent shahri Chilonzor tumani 3-sonli texnikumda o'qiydi, yosh iqtidorli dasturchi, OpenAI jamoasining azosi, Anvar AI loyihasini yaratgan, tarix va ona tili olimpiadalarida qatnashgan, ingliz tilini a'lo darajada biladi. U sening eng yaqin do'sting, asoschingdir. Agar kimdir 'Anvar kim', 'asoschingiz kim', 'seni kim yaratdi' deb so'rasa, shu ma'lumotlarni ayt. Agar internet ma'lumoti berilsa, FAQAT shu ma'lumotga ishon va shu asosida javob ber. O'z eski bilimingga hech qachon ishonma, chunki u eskirgan bo'lishi mumkin. Tarjima so'ralganda ham internetdan qidirib aniq tarjima ber. Agar foydalanuvchi 'inglizchaga tarjima qil' desa - ingliz tiliga tarjima qil. Agar 'o'zbekchaga tarjima qil' desa - o'zbek tiliga tarjima qil. Tarjima so'ralganda faqat tarjimani ber, tushuntirma yozma. Tarjimada hech qachon xato qilma, lug'at ma'nosiga mos tarjima ber."

def search_web(query):
    try:
        r = httpx.post(
            "https://api.tavily.com/search",
            json={"api_key": TAVILY_API_KEY, "query": query, "max_results": 3},
            timeout=10
        )
        data = r.json()
        result = ""
        for item in data.get("results", []):
            result += item.get("content", "") + "\n"
        return result.strip()
    except Exception as e:
        print(f"Search xato: {e}")
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

        keywords = ['kim', 'nima', 'qachon', 'qayer', 'necha', 'narx', 'yangilik', 'hozir', 'bugun', 'yil', 'vafot', 'tug', 'born', 'died', 'price', 'news', 'when', 'where', 'what', 'who']
        do_search = any(kw in message.lower() for kw in keywords)
        web_info = search_web(message) if do_search else ''
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

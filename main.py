import os
import json
import datetime
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load API key from the ai-agent .env
load_dotenv(os.path.join(os.path.dirname(__file__), ".venv", "ai-agent", ".env"))

app = Flask(__name__)

llm = ChatOpenAI(
    temperature=0.7,
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o-mini"
)

SYSTEM_PROMPT = (
    "You are Nova, a friendly and highly capable AI assistant built by NovaStack Labs. "
    "You help users with coding, automation, workflows, and general questions. "
    "Be concise, helpful, and slightly enthusiastic."
)

# In-memory stats (resets on server restart)
stats = {"messages": 0, "tasks": 0, "workflows": 12, "errors": 0}
activity_log = []

@app.route("/")
def landing():
    return render_template("landing.html")

@app.route("/agent")
def agent():
    return render_template("agent.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok"}), 200

@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_msg = data.get("message", "").strip()
        history  = data.get("history", [])

        if not user_msg:
            return jsonify({"error": "Empty message"}), 400

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for h in history[-10:]:          # keep last 10 turns for context
            messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": user_msg})

        response = llm.invoke(messages)
        reply = response.content

        stats["messages"] += 1
        stats["tasks"] += 1
        activity_log.insert(0, {
            "time": datetime.datetime.now().strftime("%H:%M:%S"),
            "text": user_msg[:60] + ("…" if len(user_msg) > 60 else "")
        })
        if len(activity_log) > 20:
            activity_log.pop()

        return jsonify({"reply": reply})
    except ValueError as e:
        stats["errors"] += 1
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        stats["errors"] += 1
        return jsonify({"error": f"Agent error: {str(e)}"}), 500

@app.route("/api/stats")
def get_stats():
    return jsonify({**stats, "activity": activity_log[:10]})

if __name__ == "__main__":
    print("Starting NovaStack Labs on http://localhost:5000/")
    app.run(debug=True, host="0.0.0.0", port=5000)

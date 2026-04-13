import os
import json
import base64
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Always load env vars from this project folder, regardless of current shell cwd.
# override=True prevents stale variables from previous runs from taking precedence.
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"), override=True)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-secret-in-env")

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

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/tech")
def tech():
    return render_template("tech.html")


def _is_admin_authenticated():
    return session.get("is_admin") is True


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "GET":
        if _is_admin_authenticated():
            return redirect(url_for("admin"))
        return render_template("admin_login.html", error=None)

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    expected_username = os.getenv("ADMIN_USERNAME", "admin")
    expected_password = os.getenv("ADMIN_PASSWORD", "change-me-now")

    if username == expected_username and password == expected_password:
        session["is_admin"] = True
        return redirect(url_for("admin"))

    return render_template("admin_login.html", error="Invalid admin credentials.")


@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    session.pop("is_admin", None)
    return redirect(url_for("admin_login"))


@app.route("/admin")
def admin():
    if not _is_admin_authenticated():
        return redirect(url_for("admin_login"))
    return render_template("admin.html")

@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok"}), 200

@app.route("/api/oauth-check")
def oauth_check():
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    refresh_token = os.getenv("GOOGLE_REFRESH_TOKEN")
    mail_sender = os.getenv("MAIL_SENDER")

    missing = []
    if not client_id:
        missing.append("GOOGLE_CLIENT_ID")
    if not client_secret:
        missing.append("GOOGLE_CLIENT_SECRET")
    if not refresh_token:
        missing.append("GOOGLE_REFRESH_TOKEN")
    if not mail_sender:
        missing.append("MAIL_SENDER")

    if missing:
        return jsonify({"ok": False, "missing": missing}), 400

    try:
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            client_id=client_id,
            client_secret=client_secret,
            token_uri="https://oauth2.googleapis.com/token",
        )
        service = build("gmail", "v1", credentials=creds)
        profile = service.users().getProfile(userId="me").execute()
        return jsonify({
            "ok": True,
            "message": "OAuth configuration is valid.",
            "gmail_account": profile.get("emailAddress"),
        }), 200
    except HttpError as e:
        return jsonify({"ok": False, "error": f"Gmail API error: {e.reason}"}), 500
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/contact", methods=["POST"])
def send_contact():
    try:
        data = request.get_json()
        first_name   = data.get("first_name", "").strip()
        last_name    = data.get("last_name", "").strip()
        sender_email = data.get("email", "").strip()
        subject      = data.get("subject", "general")
        message      = data.get("message", "").strip()

        if not first_name or not sender_email or not message:
            return jsonify({"error": "Name, email, and message are required."}), 400

        # ── Gmail API via OAuth2 ──
        # Requires GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN,
        # MAIL_SENDER, and MAIL_RECEIVER in your .env / Railway env vars.
        client_id     = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        refresh_token = os.getenv("GOOGLE_REFRESH_TOKEN")
        mail_sender   = os.getenv("MAIL_SENDER")
        mail_receiver = os.getenv("MAIL_RECEIVER", mail_sender)

        if client_id and client_secret and refresh_token and mail_sender:
            full_name = f"{first_name} {last_name}".strip()
            body = (
                f"From: {full_name} <{sender_email}>\n"
                f"Topic: {subject}\n"
                f"{'─' * 40}\n\n"
                f"{message}"
            )
            creds = Credentials(
                token=None,
                refresh_token=refresh_token,
                client_id=client_id,
                client_secret=client_secret,
                token_uri="https://oauth2.googleapis.com/token",
            )
            service = build("gmail", "v1", credentials=creds)

            msg = MIMEMultipart()
            msg["From"]    = mail_sender
            msg["To"]      = mail_receiver
            msg["Subject"] = f"[Konticode Contact] {subject} – {full_name}"
            msg["Reply-To"] = sender_email
            msg.attach(MIMEText(body, "plain"))

            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            service.users().messages().send(userId="me", body={"raw": raw}).execute()

        # Always log to activity feed
        activity_log.insert(0, {
            "time": datetime.datetime.now().strftime("%H:%M:%S"),
            "text": f"Contact form: {first_name} <{sender_email}>"
        })
        if len(activity_log) > 20:
            activity_log.pop()

        return jsonify({"ok": True}), 200

    except HttpError as e:
        return jsonify({"error": f"Gmail API error: {e.reason}"}), 500
    except Exception as e:
        return jsonify({"error": f"Could not send message: {str(e)}"}), 500

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
    port = int(os.getenv("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)

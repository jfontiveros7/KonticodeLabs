from flask import Flask, render_template, jsonify

app = Flask(__name__)

# ---------------------------
# Home Route
# ---------------------------
@app.route("/")
def home():
    return render_template(
        "home.html",
        title="AI Agent",
        app_name="NovaStack AI Agent",
        version="1.0.0"
    )

# ---------------------------
# Health Check (Render uses this)
# ---------------------------
@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok"}), 200

# ---------------------------
# Example: Agent Page
# ---------------------------
@app.route("/agent")
def agent():
    return render_template(
        "agent.html",
        title="AI Agent Console"
    )

# ---------------------------
# Run Local Dev Server
# ---------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

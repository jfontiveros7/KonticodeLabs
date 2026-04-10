from flask import Flask, render_template, jsonify

app = Flask(__name__)

@app.route("/")
def landing():
    return render_template("landing.html")

@app.route("/agent")
def agent():
    return render_template("agent.html")

@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

import os
import json
import base64
import datetime
import importlib
from contextlib import contextmanager
from urllib.parse import urlparse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, jsonify, request, redirect, url_for, session, Response
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from openai import APIConnectionError, AuthenticationError, RateLimitError
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
try:
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest
except ModuleNotFoundError:
    BetaAnalyticsDataClient = None
    DateRange = None
    Dimension = None
    Metric = None
    RunReportRequest = None

# Always load env vars from this project folder, regardless of current shell cwd.
# override=True prevents stale variables from previous runs from taking precedence.
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"), override=True)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-secret-in-env")
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.jinja_env.auto_reload = True

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def _get_llm():
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        raise ValueError("OPENAI_API_KEY is missing in .env")

    return ChatOpenAI(
        temperature=0.7,
        api_key=api_key,
        model=OPENAI_MODEL,
    )


def _get_mail_config(receiver_env_var=None):
    client_id = (os.getenv("GOOGLE_CLIENT_ID") or "").strip()
    client_secret = (os.getenv("GOOGLE_CLIENT_SECRET") or "").strip()
    refresh_token = (os.getenv("GOOGLE_REFRESH_TOKEN") or "").strip()
    mail_sender = (os.getenv("MAIL_SENDER") or "").strip()

    requested_receiver = (os.getenv(receiver_env_var) or "").strip() if receiver_env_var else ""
    mail_receiver = requested_receiver or (os.getenv("MAIL_RECEIVER") or "").strip() or mail_sender

    missing_mail_env = []
    if not client_id:
        missing_mail_env.append("GOOGLE_CLIENT_ID")
    if not client_secret:
        missing_mail_env.append("GOOGLE_CLIENT_SECRET")
    if not refresh_token:
        missing_mail_env.append("GOOGLE_REFRESH_TOKEN")
    if not mail_sender:
        missing_mail_env.append("MAIL_SENDER")

    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "mail_sender": mail_sender,
        "mail_receiver": mail_receiver,
        "missing": missing_mail_env,
    }


def _build_gmail_service(mail_config):
    creds = Credentials(
        token=None,
        refresh_token=mail_config["refresh_token"],
        client_id=mail_config["client_id"],
        client_secret=mail_config["client_secret"],
        token_uri="https://oauth2.googleapis.com/token",
    )
    return build("gmail", "v1", credentials=creds)


def _send_gmail_message(service, sender, receiver, subject, body, reply_to=None):
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = subject
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.attach(MIMEText(body, "plain", "utf-8"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()


def _log_activity(text):
    activity_log.insert(0, {
        "time": datetime.datetime.now().strftime("%H:%M:%S"),
        "text": text,
    })
    if len(activity_log) > 20:
        activity_log.pop()


def _parse_request_data():
    data = request.get_json(silent=True)
    if isinstance(data, dict):
        return data
    if request.form:
        return request.form.to_dict()
    return {}


def _load_stripe():
    try:
        return importlib.import_module("stripe")
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Stripe support requires the 'stripe' package. Install dependencies from requirements.txt."
        ) from exc


def _get_public_base_url():
    configured = (os.getenv("PUBLIC_BASE_URL") or "").strip().rstrip("/")
    if configured:
        return configured
    return request.url_root.rstrip("/")


def _get_stripe_config():
    return {
        "secret_key": (os.getenv("STRIPE_SECRET_KEY") or "").strip(),
        "webhook_secret": (os.getenv("STRIPE_WEBHOOK_SECRET") or "").strip(),
        "prices": {
            "donation_5": (os.getenv("STRIPE_PRICE_DONATION_5") or "").strip(),
            "donation_20": (os.getenv("STRIPE_PRICE_DONATION_20") or "").strip(),
            "donation_50": (os.getenv("STRIPE_PRICE_DONATION_50") or "").strip(),
            "monthly_support": (os.getenv("STRIPE_PRICE_MONTHLY_SUPPORT") or "").strip(),
        },
    }


def _get_stripe_price_id(plan_key):
    stripe_config = _get_stripe_config()
    price_id = stripe_config["prices"].get(plan_key, "")
    if not price_id:
        raise ValueError(f"Stripe price is not configured for plan '{plan_key}'.")
    return price_id


@contextmanager
def _stripe_network_env():
    proxy_keys = [
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
        "GIT_HTTP_PROXY",
        "GIT_HTTPS_PROXY",
    ]
    original_values = {key: os.environ.get(key) for key in proxy_keys}

    try:
        for key in proxy_keys:
            os.environ.pop(key, None)
        yield
    finally:
        for key, value in original_values.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

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

@app.route("/support")
def support():
    return redirect(url_for("static", filename="index.html"))

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/tech")
def tech():
    return render_template("tech.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/features")
def features():
    return render_template("features.html")

@app.route("/demo")
def demo():
    return render_template("demo.html")


@app.route("/support/success")
def support_success():
    session_id = request.args.get("session_id", "").strip()
    return render_template("donation_success.html", session_id=session_id)


@app.route("/support/cancel")
def support_cancel():
    return redirect(url_for("support"))


def _get_budget_tracker_url():
    """Return a validated external Budget Tracker base URL or None."""
    url = (os.getenv("BUDGET_TRACKER_URL") or "").strip().rstrip("/")
    if not url:
        return None

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None

    return url

@app.route("/budget-tracker")
def budget_tracker():
    external_url = _get_budget_tracker_url()
    if external_url:
        return redirect(external_url)
    return render_template("budget_tracker.html", budget_tracker_url=external_url)


@app.route("/budget-tracker/<path:subpath>")
def budget_tracker_subpath(subpath):
    external_url = _get_budget_tracker_url()
    if external_url:
        return redirect(f"{external_url}/{subpath}")
    return redirect(url_for("budget_tracker"))

@app.route("/affiliate-tools")
def affiliate_tools():
    return render_template("affiliatehub.html")

@app.route("/affiliatehub")
def affiliate_hub_legacy():
    return redirect(url_for("affiliate_tools"))

@app.route("/affiliatehub.html")
def affiliate_hub_html_legacy():
    return redirect(url_for("affiliate_tools"))


@app.route("/robots.txt")
def robots_txt():
    lines = [
        "User-agent: *",
        "Allow: /",
        "Sitemap: " + request.url_root.rstrip("/") + "/sitemap.xml",
    ]
    return Response("\n".join(lines) + "\n", mimetype="text/plain")


@app.route("/sitemap.xml")
def sitemap_xml():
    pages = [
        "landing",
        "about",
        "features",
        "demo",
        "budget_tracker",
        "tech",
        "contact",
        "agent",
        "dashboard",
        "affiliate_tools",
        "support",
    ]
    urls = [request.url_root.rstrip("/") + url_for(endpoint) for endpoint in pages]
    lastmod = datetime.date.today().isoformat()

    body = [
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
        "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">",
    ]
    for loc in urls:
        body.append("  <url>")
        body.append(f"    <loc>{loc}</loc>")
        body.append(f"    <lastmod>{lastmod}</lastmod>")
        body.append("  </url>")
    body.append("</urlset>")
    return Response("\n".join(body) + "\n", mimetype="application/xml")


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

    expected_username = (
        os.getenv("ADMIN_USERNAME")
        or os.getenv("ADMIN_USER")
        or "admin"
    ).strip()
    expected_password = (
        os.getenv("ADMIN_PASSWORD")
        or os.getenv("ADMIN_PASS")
        or "change-me-now"
    ).strip()

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
        body = body.replace("â”€", "-")
        service = _build_gmail_service(mail_config)
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
        data = request.get_json(silent=True) or {}
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
        mail_config = _get_mail_config()

        if mail_config["missing"]:
            return jsonify({
                "error": "Email service is not configured.",
                "missing": mail_config["missing"],
            }), 503

        full_name = f"{first_name} {last_name}".strip()
        body = (
            f"From: {full_name} <{sender_email}>\n"
            f"Topic: {subject}\n"
            f"{'─' * 40}\n\n"
            f"{message}"
        )
        service = _build_gmail_service(mail_config)

        msg = MIMEMultipart()
        msg["From"]    = mail_config["mail_sender"]
        msg["To"]      = mail_config["mail_receiver"]
        msg["Subject"] = f"[Konticode Contact] {subject} – {full_name}"
        msg["Reply-To"] = sender_email
        msg.replace_header("Subject", f"[Konticode Contact] {subject} - {full_name}")
        msg.attach(MIMEText(body, "plain", "utf-8"))

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw}).execute()

        # Always log to activity feed
        _log_activity(f"Contact form: {first_name} <{sender_email}>")

        return jsonify({"ok": True}), 200

    except HttpError as e:
        return jsonify({"error": f"Gmail API error: {e.reason}"}), 500
    except Exception as e:
        return jsonify({"error": f"Could not send message: {str(e)}"}), 500

@app.route("/api/feedback", methods=["POST"])
def send_feedback():
    try:
        data = request.get_json(silent=True) or {}
        topic = data.get("topic", "general").strip() or "general"
        sender_email = data.get("email", "").strip()
        message = data.get("message", "").strip()
        follow_up = bool(data.get("followUp"))
        page = data.get("page", "").strip()
        submitted_at = data.get("submittedAt", "").strip()
        source = data.get("source", "Konticode").strip() or "Konticode"

        if not sender_email or not message:
            return jsonify({"error": "Email and message are required."}), 400

        mail_config = _get_mail_config("FEEDBACK_RECEIVER")

        if mail_config["missing"]:
            return jsonify({
                "error": "Email service is not configured.",
                "missing": mail_config["missing"],
            }), 503

        body = (
            f"Source: {source}\n"
            f"Topic: {topic}\n"
            f"From: {sender_email}\n"
            f"Follow up: {'Yes' if follow_up else 'No'}\n"
            f"Page: {page or 'Not provided'}\n"
            f"Submitted at: {submitted_at or datetime.datetime.utcnow().isoformat()}\n"
            f"{'-' * 40}\n\n"
            f"{message}"
        )

        service = _build_gmail_service(mail_config)

        msg = MIMEMultipart()
        msg["From"] = mail_config["mail_sender"]
        msg["To"] = mail_config["mail_receiver"]
        msg["Subject"] = f"[{source} Feedback] {topic}"
        msg["Reply-To"] = sender_email
        msg.attach(MIMEText(body, "plain", "utf-8"))

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw}).execute()

        _log_activity(f"Feedback: {topic} <{sender_email}>")

        return jsonify({"ok": True}), 200

    except HttpError as e:
        return jsonify({"error": f"Gmail API error: {e.reason}"}), 500
    except Exception as e:
        return jsonify({"error": f"Could not send feedback: {str(e)}"}), 500


@app.route("/api/create-checkout-session", methods=["POST"])
def create_checkout_session():
    try:
        data = _parse_request_data()
        plan = (data.get("plan") or "").strip()
        if not plan:
            return jsonify({"error": "A donation plan is required."}), 400

        stripe_config = _get_stripe_config()
        if not stripe_config["secret_key"]:
            return jsonify({"error": "STRIPE_SECRET_KEY is not configured."}), 503

        price_id = _get_stripe_price_id(plan)
        base_url = _get_public_base_url()
        stripe = _load_stripe()
        stripe.api_key = stripe_config["secret_key"]

        mode = "subscription" if plan == "monthly_support" else "payment"
        session_kwargs = {
            "line_items": [{"price": price_id, "quantity": 1}],
            "mode": mode,
            "success_url": f"{base_url}{url_for('support_success')}?session_id={{CHECKOUT_SESSION_ID}}",
            "cancel_url": f"{base_url}{url_for('support_cancel')}",
            "allow_promotion_codes": True,
            "metadata": {
                "source": "konticode_support_page",
                "plan": plan,
            },
        }
        if mode == "payment":
            session_kwargs["customer_creation"] = "always"

        with _stripe_network_env():
            checkout_session = stripe.checkout.Session.create(**session_kwargs)
        return jsonify({"url": checkout_session.url}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        return jsonify({"error": f"Could not create checkout session: {str(e)}"}), 500


@app.route("/api/create-portal-session", methods=["POST"])
def create_portal_session():
    try:
        data = _parse_request_data()
        session_id = (data.get("session_id") or "").strip()
        if not session_id:
            return jsonify({"error": "session_id is required."}), 400

        stripe_config = _get_stripe_config()
        if not stripe_config["secret_key"]:
            return jsonify({"error": "STRIPE_SECRET_KEY is not configured."}), 503

        stripe = _load_stripe()
        stripe.api_key = stripe_config["secret_key"]

        with _stripe_network_env():
            checkout_session = stripe.checkout.Session.retrieve(session_id)
        customer_id = checkout_session.get("customer")
        if not customer_id:
            return jsonify({"error": "This checkout session has no Stripe customer to manage."}), 400

        with _stripe_network_env():
            portal_session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=f"{_get_public_base_url()}{url_for('support_success')}?session_id={session_id}",
            )
        return redirect(portal_session.url, code=303)
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        return jsonify({"error": f"Could not create billing portal session: {str(e)}"}), 500


@app.route("/api/stripe-webhook", methods=["POST"])
def stripe_webhook():
    stripe_config = _get_stripe_config()
    if not stripe_config["secret_key"]:
        return jsonify({"error": "STRIPE_SECRET_KEY is not configured."}), 503

    try:
        stripe = _load_stripe()
        stripe.api_key = stripe_config["secret_key"]

        payload = request.data
        signature = request.headers.get("Stripe-Signature", "")
        webhook_secret = stripe_config["webhook_secret"]

        if webhook_secret:
            event = stripe.Webhook.construct_event(payload, signature, webhook_secret)
        else:
            event = request.get_json(silent=True) or {}

        event_type = event.get("type", "unknown")
        app.logger.info("Stripe webhook received: %s", event_type)

        if event_type == "checkout.session.completed":
            event_object = event.get("data", {}).get("object", {})
            _log_activity(
                "Stripe checkout completed: "
                + (event_object.get("id") or "unknown_session")
            )
        elif event_type == "customer.subscription.updated":
            event_object = event.get("data", {}).get("object", {})
            _log_activity(
                "Stripe subscription updated: "
                + (event_object.get("id") or "unknown_subscription")
            )

        return jsonify({"received": True}), 200
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        return jsonify({"error": f"Stripe webhook error: {str(e)}"}), 400

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

        llm = _get_llm()
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
    except AuthenticationError:
        stats["errors"] += 1
        return jsonify({"error": "OpenAI authentication failed. Check OPENAI_API_KEY in .env."}), 500
    except APIConnectionError:
        stats["errors"] += 1
        return jsonify({"error": "Could not reach OpenAI. Check your internet connection or firewall in VS Code."}), 500
    except RateLimitError:
        stats["errors"] += 1
        return jsonify({"error": "OpenAI rate limit reached. Try again in a moment."}), 429
    except ValueError as e:
        stats["errors"] += 1
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        stats["errors"] += 1
        return jsonify({"error": f"Agent error: {str(e)}"}), 500


@app.route("/api/chat-test")
def chat_test():
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()

    if not api_key:
        return jsonify({
            "ok": False,
            "stage": "config",
            "error": "OPENAI_API_KEY is missing in .env",
        }), 400

    try:
        llm = _get_llm()
        response = llm.invoke([
            {"role": "system", "content": "Reply with the single word OK."},
            {"role": "user", "content": "ping"},
        ])
        return jsonify({
            "ok": True,
            "stage": "openai",
            "model": OPENAI_MODEL,
            "reply": str(response.content).strip(),
        }), 200
    except AuthenticationError:
        return jsonify({
            "ok": False,
            "stage": "auth",
            "model": OPENAI_MODEL,
            "error": "OpenAI authentication failed. Check OPENAI_API_KEY.",
        }), 401
    except APIConnectionError as e:
        return jsonify({
            "ok": False,
            "stage": "network",
            "model": OPENAI_MODEL,
            "error": "Could not reach OpenAI from this environment.",
            "details": str(e),
        }), 503
    except RateLimitError:
        return jsonify({
            "ok": False,
            "stage": "rate_limit",
            "model": OPENAI_MODEL,
            "error": "OpenAI rate limit reached.",
        }), 429
    except Exception as e:
        return jsonify({
            "ok": False,
            "stage": "unknown",
            "model": OPENAI_MODEL,
            "error": str(e),
            "error_type": type(e).__name__,
        }), 500

@app.route("/api/stats")
def get_stats():
    return jsonify({**stats, "activity": activity_log[:10]})


@app.after_request
def add_no_cache_headers(response):
    content_type = (response.headers.get("Content-Type") or "").lower()
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if "text/html" in content_type:
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


def _build_ga4_client_and_property():
    if BetaAnalyticsDataClient is None:
        return None, None

    property_id = (os.getenv("GA4_PROPERTY_ID") or "").strip()
    if not property_id:
        return None, None

    scopes = ["https://www.googleapis.com/auth/analytics.readonly"]
    creds = None

    service_account_json = (os.getenv("GA4_SERVICE_ACCOUNT_JSON") or "").strip()
    service_account_file = (os.getenv("GA4_SERVICE_ACCOUNT_FILE") or "").strip()

    if service_account_json:
        info = json.loads(service_account_json)
        creds = service_account.Credentials.from_service_account_info(info, scopes=scopes)
    elif service_account_file and os.path.exists(service_account_file):
        creds = service_account.Credentials.from_service_account_file(service_account_file, scopes=scopes)
    else:
        return None, None

    client = BetaAnalyticsDataClient(credentials=creds)
    return client, f"properties/{property_id}"


@app.route("/api/admin/analytics")
def admin_analytics():
    if not _is_admin_authenticated():
        return jsonify({"error": "Unauthorized"}), 401

    # Fallback payload keeps UI functional when GA4 API is not configured.
    fallback_payload = {
        "source": "fallback",
        "kpis": {
            "visitors_today": 0,
            "contact_leads": 0,
            "sessions": 0,
            "engagement_rate": 0.0,
        },
        "trend": [],
        "top_sources": [],
        "recent_events": activity_log[:10],
    }

    try:
        client, property_name = _build_ga4_client_and_property()
        if not client:
            return jsonify(fallback_payload), 200

        today_report = client.run_report(
            RunReportRequest(
                property=property_name,
                date_ranges=[DateRange(start_date="today", end_date="today")],
                metrics=[
                    Metric(name="totalUsers"),
                    Metric(name="eventCount"),
                    Metric(name="sessions"),
                    Metric(name="engagementRate"),
                ],
            )
        )

        visitors_today = 0
        total_events = 0
        sessions_count = 0
        engagement_rate = 0.0
        if today_report.rows:
            metric_values = today_report.rows[0].metric_values
            visitors_today = int(float(metric_values[0].value or 0))
            total_events = int(float(metric_values[1].value or 0))
            sessions_count = int(float(metric_values[2].value or 0))
            engagement_rate = float(metric_values[3].value or 0) * 100

        trend_report = client.run_report(
            RunReportRequest(
                property=property_name,
                date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
                dimensions=[Dimension(name="date")],
                metrics=[Metric(name="sessions")],
                order_bys=[{"dimension": {"dimension_name": "date"}}],
            )
        )
        trend = []
        for row in trend_report.rows:
            raw_date = row.dimension_values[0].value
            label = f"{raw_date[4:6]}/{raw_date[6:8]}"
            value = int(float(row.metric_values[0].value or 0))
            trend.append({"label": label, "value": value})

        source_report = client.run_report(
            RunReportRequest(
                property=property_name,
                date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
                dimensions=[Dimension(name="sessionDefaultChannelGroup")],
                metrics=[Metric(name="sessions")],
                limit=4,
            )
        )
        top_sources = []
        for row in source_report.rows:
            top_sources.append({
                "name": row.dimension_values[0].value,
                "value": int(float(row.metric_values[0].value or 0)),
            })

        payload = {
            "source": "ga4",
            "kpis": {
                "visitors_today": visitors_today,
                # If custom conversion event isn't configured, this acts as activity volume.
                "contact_leads": total_events,
                "sessions": sessions_count,
                "engagement_rate": round(engagement_rate, 2),
            },
            "trend": trend,
            "top_sources": top_sources,
            "recent_events": activity_log[:10],
        }
        return jsonify(payload), 200
    except Exception as e:
        fallback_payload["error"] = str(e)
        return jsonify(fallback_payload), 200

if __name__ == "__main__":
    print("Starting NovaStack Labs on http://localhost:5000/")
    port = int(os.getenv("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)

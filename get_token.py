"""
Run this ONCE to get your GOOGLE_REFRESH_TOKEN.

Steps:
  1. Go to https://console.cloud.google.com
  2. Create a project (or select existing)
  3. Enable the Gmail API
  4. Go to APIs & Services > Credentials > Create Credentials > OAuth client ID
  5. Choose "Desktop app", download the JSON, rename it to client_secret.json
     and place it next to this file
  6. Run:  python get_token.py
  7. A browser tab opens — sign in and grant Gmail send permission
  8. Copy the printed values into your .env file
"""

import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
creds = flow.run_local_server(port=0)

print("\n✅ Add these to your .env (and Railway environment variables):\n")
print(f"GOOGLE_CLIENT_ID={creds.client_id}")
print(f"GOOGLE_CLIENT_SECRET={creds.client_secret}")
print(f"GOOGLE_REFRESH_TOKEN={creds.refresh_token}")
print(f"MAIL_SENDER=your-gmail@gmail.com")
print(f"MAIL_RECEIVER=where-you-want-emails@gmail.com")

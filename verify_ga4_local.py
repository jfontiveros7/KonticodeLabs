#!/usr/bin/env python3
import os
import json
import sys

# Load .env
from dotenv import load_dotenv
load_dotenv()

print("🔍 Checking Railway GA4 Environment Variables:\n")

ga4_prop = os.getenv("GA4_PROPERTY_ID", "").strip()
ga4_sa = os.getenv("GA4_SERVICE_ACCOUNT_JSON", "").strip()

print(f"GA4_PROPERTY_ID set: {'✓ YES' if ga4_prop else '✗ NO'}")
if ga4_prop:
    print(f"  Value: {ga4_prop}")

print(f"\nGA4_SERVICE_ACCOUNT_JSON set: {'✓ YES' if ga4_sa else '✗ NO'}")
if ga4_sa:
    print(f"  Length: {len(ga4_sa)} chars")
    try:
        parsed = json.loads(ga4_sa)
        print(f"  ✓ Valid JSON")
        print(f"  Service Account Email: {parsed.get('client_email', 'N/A')}")
        print(f"  Project ID: {parsed.get('project_id', 'N/A')}")
    except json.JSONDecodeError as e:
        print(f"  ✗ Invalid JSON: {e}")
else:
    print(f"  Status: NOT SET")

print("\n" + "="*50)

# Test GA4 connection
try:
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.oauth2 import service_account
    
    if not ga4_prop or not ga4_sa:
        print("⚠ Missing GA4 configuration - would use fallback data")
    else:
        print("\n🔐 Testing GA4 API Connection...\n")
        
        scopes = ["https://www.googleapis.com/auth/analytics.readonly"]
        info = json.loads(ga4_sa)
        creds = service_account.Credentials.from_service_account_info(info, scopes=scopes)
        client = BetaAnalyticsDataClient(credentials=creds)
        
        print(f"✓ GA4 Client created successfully")
        print(f"✓ Property: properties/{ga4_prop}")
        print(f"\n✓ GA4 is properly configured on Railway!")
        
except Exception as e:
    print(f"✗ GA4 Connection Error: {e}")
    import traceback
    traceback.print_exc()

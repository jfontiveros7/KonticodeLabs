#!/usr/bin/env python3
import json
import ssl
import sys
import time
from urllib.request import urlopen, Request
from urllib.error import URLError
import urllib.parse

# Try to connect to local Flask and get analytics
time.sleep(2)  # Give Flask time to start

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

print("Testing local Flask analytics endpoint...\n")

try:
    # First, create a session by logging in
    login_payload = json.dumps({
        "username": "jfontiveros7",
        "password": "SoccerBond007#"
    }).encode('utf-8')
    
    login_req = Request(
        "http://localhost:5000/admin/login",
        data=login_payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    with urlopen(login_req, timeout=5) as resp:
        print(f"✓ Login response: {resp.status}")
        headers = resp.headers
        cookies = headers.get('Set-Cookie', '')
        print(f"  Cookies: {cookies[:50]}...")
    
    # Now try to access analytics (without session, expect 401)
    print("\n📊 Testing /api/admin/analytics endpoint:")
    analytics_req = Request("http://localhost:5000/api/admin/analytics")
    try:
        with urlopen(analytics_req, timeout=5) as resp:
            data = json.load(resp)
            source = data.get("source", "unknown")
            kpis = data.get("kpis", {})
            
            print(f"✓ Status: {resp.status}")
            print(f"✓ Data Source: {source}")
            print(f"  Visitors Today: {kpis.get('visitors_today', 0)}")
            print(f"  Contact Leads: {kpis.get('contact_leads', 0)}")
            print(f"  Sessions: {kpis.get('sessions', 0)}")
            print(f"  Engagement Rate: {kpis.get('engagement_rate', 0):.1f}%")
            
            if source == "fallback":
                print("\n⚠ Still using FALLBACK data")
            else:
                print(f"\n✓ Using LIVE GA4 data from property {data.get('property_id')}!")
                
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print(f"Expected 401 (Unauthorized) - need to pass session cookie")
            print("This is expected for unauthenticated requests")
        else:
            print(f"✗ HTTP Error {e.code}: {e.reason}")
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

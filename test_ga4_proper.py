#!/usr/bin/env python3
import urllib.request
import urllib.parse
import http.cookiejar
import json
import time

time.sleep(1)

# Create session with cookie jar
cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

print("Testing GA4 Analytics Integration\n")
print("="*50)

try:
    # Step 1: Login with form data
    print("\n1️⃣  Logging in with admin credentials...")
    login_data = urllib.parse.urlencode({
        'username': 'jfontiveros7',
        'password': 'SoccerBond007#'
    }).encode('utf-8')
    
    login_req = urllib.request.Request(
        "http://localhost:5000/admin/login",
        data=login_data,
        method="POST"
    )
    
    login_resp = opener.open(login_req, timeout=5)
    print(f"   ✓ Login successful (status {login_resp.status})")
    
    # Step 2: Fetch analytics
    print("\n2️⃣  Fetching GA4 analytics data...")
    analytics_req = urllib.request.Request(
        "http://localhost:5000/api/admin/analytics",
        method="GET",
        headers={"Accept": "application/json"}
    )
    
    analytics_resp = opener.open(analytics_req, timeout=5)
    data = json.load(analytics_resp)
    
    source = data.get("source", "unknown")
    kpis = data.get("kpis", {})
    trend = data.get("trend", [])
    
    print(f"\n   ✓ Status: {analytics_resp.status}")
    print(f"   📊 Source: {source.upper()}")
    print(f"\n   KPIs:")
    print(f"   ├─ Visitors Today: {kpis.get('visitors_today', 0)}")
    print(f"   ├─ Contact Leads: {kpis.get('contact_leads', 0)}")
    print(f"   ├─ Sessions: {kpis.get('sessions', 0)}")
    print(f"   └─ Engagement: {kpis.get('engagement_rate', 0):.1f}%")
    
    if trend:
        print(f"\n   7-Day Trend ({len(trend)} days):")
        for day in trend[-3:]:
            print(f"   └─ {day['label']}: {day['value']} sessions")
    
    print(f"\n" + "="*50)
    
    if source == "ga4":
        print("✅ SUCCESS: Live GA4 data is flowing!")
    else:
        print(f"📌 Data source: {source}")
        if source == "fallback" and kpis.get('visitors_today') == 0:
            print("   (GA4 not returning data, but connection successful)")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

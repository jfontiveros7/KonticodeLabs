#!/usr/bin/env python3
import json
import http.cookiejar
import urllib.request
import time

time.sleep(1)

# Create a cookie jar to maintain session
cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
urllib.request.install_opener(opener)

print("Testing GA4 Analytics Integration\n")
print("="*50)

try:
    # Step 1: Login
    print("\n1️⃣  Logging in to admin...")
    login_payload = json.dumps({
        "username": "jfontiveros7",
        "password": "SoccerBond007#"
    }).encode('utf-8')
    
    login_req = urllib.request.Request(
        "http://localhost:5000/admin/login",
        data=login_payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    login_resp = opener.open(login_req, timeout=5)
    login_data = json.load(login_resp)
    status = login_resp.status
    
    if status == 200:
        print(f"   ✓ Login successful (status {status})")
    else:
        print(f"   ⚠ Login returned {status}")
    
    # Step 2: Fetch analytics with authenticated session
    print("\n2️⃣  Fetching analytics data from GA4...")
    analytics_req = urllib.request.Request(
        "http://localhost:5000/api/admin/analytics",
        headers={"Content-Type": "application/json"},
        method="GET"
    )
    
    analytics_resp = opener.open(analytics_req, timeout=5)
    analytics_data = json.load(analytics_resp)
    
    source = analytics_data.get("source", "unknown")
    kpis = analytics_data.get("kpis", {})
    trend = analytics_data.get("trend", [])
    top_sources = analytics_data.get("top_sources", [])
    
    print(f"\n   ✓ Analytics Status: {analytics_resp.status}")
    print(f"   📊 Data Source: {source.upper()}")
    
    print(f"\n   ├─ KPIs:")
    print(f"   │  ├─ Visitors Today: {kpis.get('visitors_today', 0)}")
    print(f"   │  ├─ Contact Leads: {kpis.get('contact_leads', 0)}")
    print(f"   │  ├─ Sessions: {kpis.get('sessions', 0)}")
    print(f"   │  └─ Engagement Rate: {kpis.get('engagement_rate', 0):.1f}%")
    
    if trend:
        print(f"\n   ├─ 7-Day Trend: {len(trend)} days tracked")
        for day in trend[-3:]:
            print(f"   │  └─ {day['label']}: {day['value']} sessions")
    
    if top_sources:
        print(f"\n   ├─ Top Sources:")
        for src in top_sources[:3]:
            print(f"   │  └─ {src['name']}: {src['value']} sessions")
    
    print(f"\n" + "="*50)
    
    if source == "ga4":
        print("✅ SUCCESS: Live GA4 data is flowing!\n")
    elif source == "fallback":
        print("⚠️  Fallback data (GA4 not returning data yet)\n")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

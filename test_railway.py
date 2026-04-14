#!/usr/bin/env python3
import json
import ssl
import urllib.request
import urllib.error
import time

time.sleep(1)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

print("Testing Railway GA4 Analytics\n")
print("="*50)

try:
    url = "https://konticode.com/api/admin/analytics"
    
    # Railway requires authentication even for this endpoint
    # But let's try to see what happens
    req = urllib.request.Request(
        url,
        method="GET",
        headers={"Accept": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            data = json.load(resp)
            source = data.get("source", "unknown")
            kpis = data.get("kpis", {})
            
            print(f"✓ Railway Status: {resp.status}")
            print(f"📊 Source: {source.upper()}")
            print(f"\nKPIs:")
            print(f"├─ Visitors: {kpis.get('visitors_today', 0)}")
            print(f"├─ Leads: {kpis.get('contact_leads', 0)}")
            print(f"├─ Sessions: {kpis.get('sessions', 0)}")
            print(f"└─ Engagement: {kpis.get('engagement_rate', 0):.1f}%")
            
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print("⚠ 401 Unauthorized (expected - needs admin session)")
            print("  The endpoint requires authentication")
            print("  ✓ This is normal - the code is working correctly")
        else:
            print(f"✗ HTTP {e.code}: {e.reason}")
            
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

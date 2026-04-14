#!/usr/bin/env python3
import json
import ssl
import sys
from urllib.request import urlopen, Request
from urllib.error import URLError

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

try:
    req = Request("https://konticode.com/api/admin/analytics")
    with urlopen(req, context=ctx, timeout=5) as resp:
        data = json.load(resp)
        source = data.get("source", "unknown")
        visitors = data.get("kpis", {}).get("visitors_today", 0)
        leads = data.get("kpis", {}).get("contact_leads", 0)
        sessions = data.get("kpis", {}).get("sessions", 0)
        
        print(f"✓ Data Source: {source}")
        print(f"  Visitors Today: {visitors}")
        print(f"  Contact Leads: {leads}")
        print(f"  Sessions: {sessions}")
        
        if source == "fallback":
            print("\n⚠ Still using FALLBACK data (GA4 env vars may not be set)")
        else:
            print("\n✓ Using LIVE GA4 data!")
            
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)

#!/usr/bin/env python3
"""Test eastmoney API to find correct pagination params"""
import requests
import json

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0'})

url = "https://push2.eastmoney.com/api/qt/clist/get"
params = {
    'cb': 'jQuery',
    'pn': 1,
    'pz': 5500,
    'po': 1,
    'np': 1,
    'fltt': 2,
    'invt': 2,
    'fid': 'f3',
    'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23',
    'fields': 'f12,f14'
}

resp = session.get(url, params=params, timeout=20)
text = resp.text.strip()
json_str = text[text.index('(')+1:text.rindex(')')]
data = json.loads(json_str)

total = data.get('data', {}).get('total', 0)
diff = data.get('data', {}).get('diff', [])
print(f"total={total}, returned={len(diff)}")

# Check specific stocks
codes_to_check = ['002146', '601288', '000001', '600000']
for code in codes_to_check:
    found = [i for i in diff if i.get('f12') == code]
    print(f"  {code}: {'FOUND - ' + found[0]['f14'] if found else 'NOT FOUND'}")

# Show first/last 5
print(f"\nFirst 5: {[(i['f12'], i['f14']) for i in diff[:5]]}")
print(f"Last 5: {[(i['f12'], i['f14']) for i in diff[-5:]]}")

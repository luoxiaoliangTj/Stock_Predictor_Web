#!/usr/bin/env python3
"""Test paginated fetch"""
import requests
import json
import time

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0'})

url = "https://push2.eastmoney.com/api/qt/clist/get"
all_stocks = {}

for pn in range(1, 60):  # up to 60 pages
    params = {
        'cb': 'jQuery',
        'pn': pn,
        'pz': 100,
        'po': 1,
        'np': 1,
        'fltt': 2,
        'invt': 2,
        'fid': 'f3',
        'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23',
        'fields': 'f12,f14'
    }
    try:
        resp = session.get(url, params=params, timeout=15)
        text = resp.text.strip()
        json_str = text[text.index('(')+1:text.rindex(')')]
        data = json.loads(json_str)
        
        diff = data.get('data', {}).get('diff', [])
        if not diff:
            break
        for item in diff:
            code = item.get('f12', '')
            name = item.get('f14', '')
            if code and name:
                all_stocks[code] = name
        print(f"Page {pn}: got {len(diff)} stocks, total so far: {len(all_stocks)}")
        
        if len(diff) < 100:
            break
        time.sleep(0.05)  # be nice to the API
    except Exception as e:
        print(f"Page {pn} failed: {e}")
        break

print(f"\nTotal stocks: {len(all_stocks)}")
# Check specific stocks
for code in ['002146', '601288', '000001', '600000']:
    name = all_stocks.get(code, 'NOT FOUND')
    print(f"  {code}: {name}")

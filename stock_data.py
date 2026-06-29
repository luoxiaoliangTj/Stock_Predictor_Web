#!/usr/bin/env python3
"""
Stock Data Fetcher - 股票数据获取模块
数据源: 腾讯行情(qt.gtimg.cn) + 东方财富(EM)
"""

import requests
import json
import re
from datetime import datetime
from typing import Optional, Dict, Any, List


class StockDataFetcher:
    """股票数据获取器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_realtime_quote(self, code: str) -> Optional[Dict[str, Any]]:
        """
        获取实时行情 (腾讯API)
        格式: https://qt.gtimg.cn/q=sz002146 或 https://qt.gtimg.cn/q=sh601288
        """
        # 判断交易所前缀
        prefix = "sh" if code.startswith("6") else "sz"
        url = f"https://qt.gtimg.cn/q={prefix}{code}"
        
        try:
            resp = self.session.get(url, timeout=10)
            resp.encoding = 'gbk'
            text = resp.text.strip()
            
            # 解析格式: v_sz002146="51~荣盛发展~002146~1.04~..."
            match = re.search(r'"(.+)"', text)
            if not match:
                return None
            
            parts = match.group(1).split('~')
            if len(parts) < 50:
                return None
            
            # 解析时间 (格式: 20260629161436)
            time_str = parts[30] if len(parts) > 30 else ""
            if len(time_str) == 14:
                dt = datetime.strptime(time_str, "%Y%m%d%H%M%S")
                timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            return {
                'code': parts[2],
                'name': parts[1],
                'price': float(parts[3]) if parts[3] else 0.0,
                'prev_close': float(parts[4]) if parts[4] else 0.0,
                'open': float(parts[5]) if parts[5] else 0.0,
                'high': float(parts[33]) if len(parts) > 33 and parts[33] else 0.0,
                'low': float(parts[34]) if len(parts) > 34 and parts[34] else 0.0,
                'volume': int(parts[6]) if parts[6] else 0,  # 成交量(手)
                'turnover': float(parts[37]) if len(parts) > 37 and parts[37] else 0.0,  # 成交额(万)
                'change': float(parts[31]) if len(parts) > 31 and parts[31] else 0.0,
                'change_pct': float(parts[32]) if len(parts) > 32 and parts[32] else 0.0,
                'pe': float(parts[39]) if len(parts) > 39 and parts[39] else 0.0,
                'pb': float(parts[46]) if len(parts) > 46 and parts[46] else 0.0,
                'amplitude': float(parts[43]) if len(parts) > 43 and parts[43] else 0.0,  # 振幅%
                'market_cap': float(parts[45]) if len(parts) > 45 and parts[45] else 0.0,  # 总市值(亿)
                'float_cap': float(parts[44]) if len(parts) > 44 and parts[44] else 0.0,  # 流通市值(亿)
                'timestamp': timestamp
            }
        except Exception as e:
            print(f"获取行情失败: {e}")
            return None
    
    def get_announcements(self, code: str, limit: int = 10) -> List[Dict[str, str]]:
        """
        获取最新公告 (东方财富API)
        """
        url = (
            f"https://np-anotice-stock.eastmoney.com/api/security/ann"
            f"?cb=jQuery&sr=-1&page_size={limit}&page_index=1"
            f"&ann_type=A&client_source=web&stock_list={code}"
            f"&f_node=0&s_node=0"
        )
        
        try:
            resp = self.session.get(url, timeout=10)
            text = resp.text.strip()
            
            # 去掉 jQuery( 和末尾的 )
            json_str = text[text.index('(') + 1 : text.rindex(')')]
            data = json.loads(json_str)
            
            announcements = []
            for item in data.get('data', {}).get('list', []):
                announcements.append({
                    'date': item.get('notice_date', '')[:10],
                    'title': item.get('title_ch', '')
                })
            
            return announcements
        except Exception as e:
            print(f"获取公告失败: {e}")
            return []
    
    def get_capital_flow(self, code: str) -> Optional[Dict[str, Any]]:
        """
        获取资金流向 (东方财富API)
        """
        # 判断交易所
        secid = f"0.{code}" if code.startswith(("0", "3")) else f"1.{code}"
        url = (
            f"https://push2.eastmoney.com/api/qt/stock/fflow/daykline/get"
            f"?cb=jQuery&lmt=1&klt=101&secid={secid}"
            f"&fields1=f1,f2,f3,f7&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65"
        )
        
        try:
            resp = self.session.get(url, timeout=10)
            text = resp.text.strip()
            
            json_str = text[text.index('(') + 1 : text.rindex(')')]
            data = json.loads(json_str)
            
            klines = data.get('data', {}).get('klines', [])
            if not klines:
                return None
            
            # 取最近一天
            latest = klines[-1].split(',')
            if len(latest) >= 6:
                return {
                    'date': latest[0],
                    'main_inflow': float(latest[1]) if latest[1] != '-' else 0.0,  # 主力净流入
                    'small_inflow': float(latest[2]) if latest[2] != '-' else 0.0,  # 小单净流入
                    'mid_inflow': float(latest[3]) if latest[3] != '-' else 0.0,   # 中单净流入
                    'big_inflow': float(latest[4]) if latest[4] != '-' else 0.0,   # 大单净流入
                    'super_inflow': float(latest[5]) if latest[5] != '-' else 0.0  # 超大单净流入
                }
            return None
        except Exception as e:
            print(f"获取资金流向失败: {e}")
            return None
    
    def get_stock_name_map(self) -> Dict[str, str]:
        """
        获取股票代码-名称映射表 (用于搜索)
        """
        # 从两个交易所获取股票列表
        stocks = {}
        
        # 上证A股
        url_sh = "https://push2.eastmoney.com/api/qt/clist/get?cb=jQuery&pn=1&pz=5000&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23&fields=f12,f14"
        # 深证A股
        url_sz = "https://push2.eastmoney.com/api/qt/clist/get?cb=jQuery&pn=1&pz=5000&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23&fields=f12,f14"
        
        for url in [url_sh, url_sz]:
            try:
                resp = self.session.get(url, timeout=15)
                text = resp.text.strip()
                json_str = text[text.index('(') + 1 : text.rindex(')')]
                data = json.loads(json_str)
                
                for item in data.get('data', {}).get('diff', []):
                    code = item.get('f12', '')
                    name = item.get('f14', '')
                    if code and name:
                        stocks[code] = name
            except Exception as e:
                print(f"获取股票列表失败: {e}")
        
        return stocks


def search_stock(query: str, stock_map: Dict[str, str]) -> List[Dict[str, str]]:
    """
    搜索股票 - 支持代码/名称/拼音首字母
    """
    results = []
    query = query.strip().lower()
    
    for code, name in stock_map.items():
        # 代码匹配
        if query in code:
            results.append({'code': code, 'name': name, 'match': 'code'})
        # 名称匹配
        elif query in name.lower():
            results.append({'code': code, 'name': name, 'match': 'name'})
    
    # 按匹配精度排序: 代码 > 名称
    results.sort(key=lambda x: (0 if x['match'] == 'code' else 1, x['code']))
    
    return results[:10]  # 最多返回10个


if __name__ == "__main__":
    # 测试
    fetcher = StockDataFetcher()
    
    print("=== 测试行情获取 ===")
    quote = fetcher.get_realtime_quote("002146")
    if quote:
        print(f"代码: {quote['code']}")
        print(f"名称: {quote['name']}")
        print(f"价格: {quote['price']}")
        print(f"涨跌幅: {quote['change_pct']}%")
        print(f"时间: {quote['timestamp']}")
    
    print("\n=== 测试公告获取 ===")
    anns = fetcher.get_announcements("002146", limit=5)
    for ann in anns:
        print(f"{ann['date']} {ann['title']}")
    
    print("\n=== 测试资金流向 ===")
    flow = fetcher.get_capital_flow("002146")
    if flow:
        print(f"日期: {flow['date']}")
        print(f"主力净流入: {flow['main_inflow']:.2f}万")

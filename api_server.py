#!/usr/bin/env python3
"""
Flask API Server - 提供股票深度分析接口
运行: python3 api_server.py
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
import os
from pathlib import Path
import json
import threading
import time

# 添加项目目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from stock_analyzer import InvestmentAnalyzer
from stock_data import StockDataFetcher

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 初始化数据获取器
stock_fetcher = StockDataFetcher()

# 分析缓存
analysis_cache = {}
cache_lock = threading.Lock()


def get_analysis(code):
    """获取分析结果（带缓存）"""
    with cache_lock:
        if code in analysis_cache:
            entry = analysis_cache[code]
            # 缓存5分钟
            if time.time() - entry['timestamp'] < 300:
                return entry['data']
    
    # 缓存未命中，重新分析
    analyzer = InvestmentAnalyzer()
    result = analyzer.analyze(code)
    
    with cache_lock:
        analysis_cache[code] = {
            'timestamp': time.time(),
            'data': result
        }
    
    return result


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({'status': 'ok'})


@app.route('/analyze', methods=['GET'])
def analyze():
    """股票深度分析接口"""
    code = request.args.get('code', '').strip()
    
    if not code:
        return jsonify({'error': '缺少股票代码参数'}), 400
    
    try:
        result = get_analysis(code)
        
        if not result:
            return jsonify({'error': f'无法获取 {code} 的数据'}), 404
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': f'分析失败: {str(e)}'}), 500


@app.route('/cache/clear', methods=['POST'])
def clear_cache():
    """清除缓存"""
    global analysis_cache
    with cache_lock:
        analysis_cache.clear()
    return jsonify({'status': 'ok'})


@app.route('/api/stock/search', methods=['GET'])
def search_stock():
    """股票搜索接口 - 实时调用东方财富API单页搜索"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'error': '缺少搜索参数 q'}), 400
    
    try:
        # 直接调用东方财富API单页搜索（50条）
        url = "https://push2.eastmoney.com/api/qt/clist/get"
        params = {
            'pn': 1,
            'pz': 50,
            'po': 1,
            'np': 1,
            'fltt': 2,
            'invt': 2,
            'fid': 'f3',
            'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23',
            'fields': 'f12,f14',
            'search': query
        }
        
        resp = stock_fetcher.session.get(url, params=params, timeout=10)
        text = resp.text.strip()
        
        # 提取JSON数据
        json_str = text[text.index('(') + 1 : text.rindex(')')]
        data = json.loads(json_str)
        
        diff = data.get('data', {}).get('diff', [])
        
        results = []
        for item in diff:
            code = item.get('f12', '')
            name = item.get('f14', '')
            if code and name:
                results.append({'code': code, 'name': name})
        
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': f'搜索失败: {str(e)}'}), 500


if __name__ == '__main__':
    print("启动股票分析API服务器...")
    print("访问: http://localhost:5000/health")
    print("分析接口: http://localhost:5000/analyze?code=002146")
    app.run(host='0.0.0.0', port=5000, debug=False)

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

app = Flask(__name__)
CORS(app)  # 允许跨域请求

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


if __name__ == '__main__':
    print("启动股票分析API服务器...")
    print("访问: http://localhost:5000/health")
    print("分析接口: http://localhost:5000/analyze?code=002146")
    app.run(host='0.0.0.0', port=5000, debug=False)

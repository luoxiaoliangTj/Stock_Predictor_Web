#!/usr/bin/env python3
"""
Stock Page Generator - 股票页面生成器
输入: 股票代码
输出: 完整HTML页面 (包含实时数据+公告+资金流向+AI研判)
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

from stock_data import StockDataFetcher, search_stock


def format_number(num: float, unit: str = "") -> str:
    """格式化数字"""
    if num == 0:
        return f"0{unit}"
    abs_num = abs(num)
    if abs_num >= 1e8:
        return f"{num/1e8:.2f}亿{unit}"
    elif abs_num >= 1e4:
        return f"{num/1e4:.2f}万{unit}"
    else:
        return f"{num:.2f}{unit}"


def generate_analysis(quote: dict, announcements: list, flow: dict) -> str:
    """
    基于数据生成AI研判
    分析逻辑: 价格变动 + 公告信息 + 资金流向
    """
    analysis_parts = []
    
    # 1. 价格分析
    price = quote['price']
    change_pct = quote['change_pct']
    name = quote['name']
    
    if change_pct > 5:
        analysis_parts.append(f"<p><strong>强势上涨:</strong> {name}今日大涨{change_pct}%，收盘价{price}元，市场情绪积极。需关注是否有重大利好支撑，警惕短期获利回吐风险。</p>")
    elif change_pct > 2:
        analysis_parts.append(f"<p><strong>温和上涨:</strong> {name}今日上涨{change_pct}%，收盘价{price}元，走势稳健。可关注后续量能是否配合。</p>")
    elif change_pct > -2:
        analysis_parts.append(f"<p><strong>震荡整理:</strong> {name}今日变动{change_pct}%，收盘价{price}元，处于震荡区间。建议观望，等待方向明确。</p>")
    elif change_pct > -5:
        analysis_parts.append(f"<p><strong>温和下跌:</strong> {name}今日下跌{abs(change_pct)}%，收盘价{price}元。需关注是否有利空消息，控制仓位风险。</p>")
    else:
        analysis_parts.append(f"<p><strong>大幅下跌:</strong> {name}今日大跌{abs(change_pct)}%，收盘价{price}元。可能存在重大利空，建议关注公司公告，谨慎操作。</p>")
    
    # 2. 公告分析
    if announcements:
        latest = announcements[0]
        analysis_parts.append(f"<p><strong>最新公告:</strong> {latest['date']}发布「{latest['title']}」，建议仔细阅读公告全文，评估对公司基本面的影响。</p>")
    
    # 3. 资金流向分析
    if flow:
        main_flow = flow.get('main_inflow', 0)
        if main_flow > 0:
            analysis_parts.append(f"<p><strong>资金流入:</strong> 主力净流入{format_number(main_flow, '元')}，资金面偏积极，但需结合价格走势综合判断。</p>")
        else:
            analysis_parts.append(f"<p><strong>资金流出:</strong> 主力净流出{format_number(abs(main_flow), '元')}，资金撤离明显，短期承压。</p>")
    
    # 4. 综合判断
    pe = quote.get('pe', 0)
    pb = quote.get('pb', 0)
    
    fundamentals = []
    if pe > 0:
        fundamentals.append(f"PE {pe:.2f}")
    if pb > 0:
        fundamentals.append(f"PB {pb:.2f}")
    
    if fundamentals:
        analysis_parts.append(f"<p><strong>估值水平:</strong> {', '.join(fundamentals)}。</p>")
    
    return "\n".join(analysis_parts)


def generate_stock_page(code: str, fetcher: StockDataFetcher, include_deep_analysis: bool = True) -> str:
    """生成单个股票的完整HTML页面"""
    
    # 获取数据
    quote = fetcher.get_realtime_quote(code)
    if not quote:
        return None
    
    announcements = fetcher.get_announcements(code, limit=10)
    flow = fetcher.get_capital_flow(code)
    
    # 生成AI分析
    analysis = generate_analysis(quote, announcements, flow)
    
    # 确定涨跌颜色
    change_class = "up" if quote['change_pct'] > 0 else "down" if quote['change_pct'] < 0 else ""
    change_sign = "+" if quote['change_pct'] > 0 else ""
    
    # 生成公告HTML
    ann_html = ""
    for ann in announcements:
        ann_html += f"""
        <div class="ann-item">
            <div class="ann-date">{ann['date']}</div>
            <div class="ann-title">{ann['title']}</div>
        </div>"""
    
    # 生成资金流向HTML
    flow_html = ""
    if flow:
        flow_items = [
            ("主力净流入", flow.get('main_inflow', 0)),
            ("超大单净流入", flow.get('super_inflow', 0)),
            ("大单净流入", flow.get('big_inflow', 0)),
            ("中单净流入", flow.get('mid_inflow', 0)),
            ("小单净流入", flow.get('small_inflow', 0)),
        ]
        for label, value in flow_items:
            color_class = "up" if value > 0 else "down" if value < 0 else ""
            flow_html += f"""
            <div class="flow-item">
                <div class="flow-label">{label}</div>
                <div class="flow-value {color_class}">{format_number(value, '元')}</div>
            </div>"""
    
    # 深度分析部分
    deep_analysis_html = ""
    if include_deep_analysis:
        deep_analysis_html = f"""
    <div class="section">
        <div class="section-title">
            深度分析 
            <button class="analyze-btn" data-code="{quote['code']}" onclick="loadDeepAnalysis('{quote['code']}')">AI深度分析</button>
        </div>
        <div id="deep-analysis" class="analysis deep-analysis" style="display: none;">
            <div class="loading">分析中，请稍候...</div>
        </div>
    </div>"""
    
    # 组装页面
    body = f"""
<div class="header">
    <div class="stock-name">{quote['name']}</div>
    <div class="stock-code">{quote['code']}</div>
</div>

<div class="price-section">
    <div class="price-row">
        <span class="price">{quote['price']}</span>
        <span class="change {change_class}">{change_sign}{quote['change']}</span>
        <span class="change {change_class}">{change_sign}{quote['change_pct']}%</span>
    </div>
    <div class="timestamp">数据时间: {quote['timestamp']}</div>
    
    <div class="quote-grid">
        <div class="quote-item">
            <div class="quote-label">今开</div>
            <div class="quote-value">{quote['open']}</div>
        </div>
        <div class="quote-item">
            <div class="quote-label">最高</div>
            <div class="quote-value">{quote['high']}</div>
        </div>
        <div class="quote-item">
            <div class="quote-label">最低</div>
            <div class="quote-value">{quote['low']}</div>
        </div>
        <div class="quote-item">
            <div class="quote-label">成交量</div>
            <div class="quote-value">{format_number(quote['volume'], '手')}</div>
        </div>
        <div class="quote-item">
            <div class="quote-label">成交额</div>
            <div class="quote-value">{format_number(quote['turnover'], '元')}</div>
        </div>
        <div class="quote-item">
            <div class="quote-label">振幅</div>
            <div class="quote-value">{quote['amplitude']}%</div>
        </div>
        <div class="quote-item">
            <div class="quote-label">市盈率</div>
            <div class="quote-value">{quote['pe'] if quote['pe'] > 0 else '-'}</div>
        </div>
        <div class="quote-item">
            <div class="quote-label">市净率</div>
            <div class="quote-value">{quote['pb'] if quote['pb'] > 0 else '-'}</div>
        </div>
        <div class="quote-item">
            <div class="quote-label">总市值</div>
            <div class="quote-value">{format_number(quote['market_cap'], '亿')}</div>
        </div>
    </div>
</div>

<div class="section">
    <div class="section-title">最新公告</div>
    {ann_html}
</div>

<div class="section">
    <div class="section-title">资金流向 ({flow['date'] if flow else '暂无'})</div>
    <div class="flow-grid">
        {flow_html}
    </div>
</div>

{deep_analysis_html}

<div class="footer">
    <p>数据来源: 腾讯财经 + 东方财富</p>
    <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <button class="refresh-btn" onclick="location.reload()">刷新数据</button>
</div>"""
    
    # 读取模板并替换
    template_path = Path(__file__).parent / "template.html"
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
    
    html = template.replace("{{body}}", body)
    html = html.replace("{{code}}", quote['code'])
    html = html.replace("{{name}}", quote['name'])
    
    return html


def generate_index_page(fetcher: StockDataFetcher) -> str:
    """生成搜索首页"""
    
    body = """
<div class="index-container">
    <div class="stock-name" style="font-size: 32px; margin-bottom: 8px;">Stock Predictor</div>
    <div class="index-subtitle">输入股票代码、名称或拼音首字母</div>
    
    <div class="search-box">
        <input type="text" class="search-input" id="searchInput" placeholder="例如: 002146 / 荣盛发展 / RS" autofocus>
        <button class="search-btn" onclick="searchStock()">查询</button>
    </div>
    
    <div class="results" id="results"></div>
</div>

<script>
// 股票列表数据 (由Python预生成)
const stockList = __STOCK_LIST_PLACEHOLDER__;

function searchStock() {
    const query = document.getElementById('searchInput').value.trim().toLowerCase();
    if (!query) return;
    
    const results = [];
    
    for (const [code, name] of Object.entries(stockList)) {
        if (code.includes(query) || name.toLowerCase().includes(query)) {
            results.push({code, name});
        }
    }
    
    // 按匹配精度排序
    results.sort((a, b) => {
        const aCodeMatch = a.code.includes(query) ? 0 : 1;
        const bCodeMatch = b.code.includes(query) ? 0 : 1;
        return aCodeMatch - bCodeMatch || a.code.localeCompare(b.code);
    });
    
    const resultsDiv = document.getElementById('results');
    if (results.length === 0) {
        resultsDiv.innerHTML = '<p style="text-align:center; color:#757575; padding:20px;">未找到匹配的股票</p>';
        return;
    }
    
    resultsDiv.innerHTML = results.slice(0, 10).map(r => 
        `<div class="result-item" onclick="window.location.href='generated/${r.code}.html'">
            <span>${r.name}</span>
            <span class="result-code">${r.code}</span>
        </div>`
    ).join('');
}

// 回车搜索
document.getElementById('searchInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') searchStock();
});
</script>"""
    
    # 读取模板
    template_path = Path(__file__).parent / "template.html"
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
    
    # 获取股票列表
    stock_map = fetcher.get_stock_name_map()
    stock_json = json.dumps(stock_map, ensure_ascii=False)
    
    html = template.replace("{{body}}", body)
    html = html.replace("{{code}}", "Stock Predictor")
    html = html.replace("{{name}}", "")
    html = html.replace("__STOCK_LIST_PLACEHOLDER__", stock_json)
    
    return html


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python3 stock_web.py <股票代码> [--index]")
        print("示例: python3 stock_web.py 002146")
        print("       python3 stock_web.py --index  (生成搜索首页)")
        sys.exit(1)
    
    fetcher = StockDataFetcher()
    
    if sys.argv[1] == "--index":
        # 生成搜索首页
        print("正在生成搜索首页...")
        html = generate_index_page(fetcher)
        
        output_path = Path(__file__).parent / "index.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✓ 搜索首页已生成: {output_path}")
        print(f"  股票数量: {len(fetcher.get_stock_name_map())}")
    
    else:
        # 生成股票页面
        code = sys.argv[1]
        print(f"正在获取 {code} 的数据...")
        
        html = generate_stock_page(code, fetcher)
        if not html:
            print(f"✗ 无法获取 {code} 的数据")
            sys.exit(1)
        
        output_path = Path(__file__).parent / "generated" / f"{code}.html"
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✓ 股票页面已生成: {output_path}")


if __name__ == "__main__":
    main()

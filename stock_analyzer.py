#!/usr/bin/env python3
"""
深度分析器 - 调用Hermes进行AI投资研究分析
输入: 股票代码
输出: JSON格式分析报告
"""

import sys
import json
import subprocess
from datetime import datetime
from typing import Optional, Dict, Any

from stock_data import StockDataFetcher


class InvestmentAnalyzer:
    """投资分析器 - 基于AI Berkshire框架的简化版"""
    
    def __init__(self):
        self.fetcher = StockDataFetcher()
        self.cache = {}  # 简单内存缓存
    
    def analyze(self, code: str) -> Optional[Dict[str, Any]]:
        """对股票进行AI投资分析"""
        
        # 检查缓存
        if code in self.cache:
            return self.cache[code]
        
        # 获取基础数据
        quote = self.fetcher.get_realtime_quote(code)
        if not quote:
            return None
        
        announcements = self.fetcher.get_announcements(code, limit=5)
        flow = self.fetcher.get_capital_flow(code)
        
        # 调用Hermes进行AI分析
        analysis = self._call_hermes_analysis(code, quote, announcements, flow)
        
        result = {
            "code": code,
            "name": quote['name'],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "quote": {
                "price": quote['price'],
                "change_pct": quote['change_pct'],
                "open": quote['open'],
                "high": quote['high'],
                "low": quote['low'],
                "volume": quote['volume'],
                "turnover": quote['turnover'],
                "pe": quote['pe'],
                "pb": quote['pb']
            },
            "announcements": announcements,
            "capital_flow": flow,
            "analysis": analysis
        }
        
        # 缓存5分钟
        self.cache[code] = result
        return result
    
    def _call_hermes_analysis(self, code: str, quote: dict, 
                              announcements: list, flow: dict) -> str:
        """
        调用Hermes进行AI分析
        使用终端执行 hermes chat -q 单查询模式
        """
        prompt = f"""你是一个专业投资分析师，请基于以下数据对股票 {code} ({quote['name']}) 进行简要分析：

【实时行情】
- 当前价: {quote['price']}元
- 涨跌幅: {quote['change_pct']}%
- 今开: {quote['open']}元
- 最高: {quote['high']}元
- 最低: {quote['low']}元
- 成交量: {quote['volume']}手
- 成交额: {quote['turnover']:.2f}万元
- 市盈率: {quote['pe'] if quote['pe'] > 0 else '暂无'}
- 市净率: {quote['pb'] if quote['pb'] > 0 else '暂无'}

【最新公告】
{chr(10).join([f"- {a['date']}: {a['title']}" for a in announcements[:3]])}

【资金流向】
{f"- 主力净流入: {flow['main_inflow']:.2f}万元" if flow and flow.get('main_inflow') else "暂无数据"}

请基于以上数据，从以下维度进行简要分析（每点1-2句话）：
1. 价格走势判断（强势/震荡/弱势）
2. 公告影响评估（利好/利空/中性）
3. 资金流向解读（主力吸筹/出货/观望）
4. 短期操作建议（持有/观望/谨慎关注）

要求：分析必须基于给出的数据，不要虚构；语言简洁专业；直接输出分析结果，不要多余内容。"""

        try:
            result = subprocess.run(
                ["hermes", "chat", "-Q", "-q", prompt],
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode == 0:
                return result.stdout.strip()[:2000]
            return f"分析失败: {result.stderr[:200]}"
        except subprocess.TimeoutExpired:
            return "分析超时，请稍后重试"
        except Exception as e:
            return f"分析失败: {str(e)}"


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python3 stock_analyzer.py <股票代码>")
        sys.exit(1)
    
    code = sys.argv[1]
    analyzer = InvestmentAnalyzer()
    
    result = analyzer.analyze(code)
    if not result:
        print(f"✗ 无法获取 {code} 的数据")
        sys.exit(1)
    
    # 输出JSON
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

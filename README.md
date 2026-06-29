# Stock Predictor Web

简洁 A 股实时行情研判系统。在线演示: 即将上线

## 特性

- 任意 A 股查询 (代码 / 名称 / 拼音首字母)
- 实时行情 + 公告 + 资金流向
- 基于最新数据的 AI 研判
- 纯静态页面，零依赖，秒级加载
- 移动端友好

## 本地运行

```bash
# 克隆
git clone https://github.com/<user>/Stock_Predictor.git
cd Stock_Predictor/web

# 生成首页
python3 stock_web.py --index

# 生成股票页面
python3 stock_web.py 002146
python3 stock_web.py 601288

# 部署
bash deploy.sh
```

## 页面预览

### 搜索首页
简洁输入框，输入代码/名称/拼音即搜索。

### 股票详情页
```
荣盛发展 (002146)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1.04  ↓0.06  ↓5.45%
数据时间: 2026-06-29 16:14:36

今开: 1.10  最高: 1.10  最低: 0.99
成交量: 174.15万手  成交额: 1.80亿元  振幅: 10.00%
市盈率: -0.49   市净率: 0.89   总市值: 40.68亿

📋 最新公告
2026-06-30 关于经营债务化解情况的自愿性信息披露公告
2026-06-30 关于金融债务化解情况的自愿性信息披露公告
...

💰 资金流向
主力净流入: -1704.69万元 (流出)
...

📊 实时研判
基于当前行情、公告、资金流向的综合分析
```

## 数据来源

| 数据 | 来源 | API |
|------|------|-----|
| 实时行情 | 腾讯财经 | `qt.gtimg.cn` |
| 公告 | 东方财富 | `np-anotice-stock.eastmoney.com` |
| 资金流向 | 东方财富 | `push2.eastmoney.com` |

## 技术栈

- Python 3 (requests)
- HTML / CSS (零 JavaScript 依赖)
- GitHub Pages 托管

## 项目结构

```
web/
├── stock_data.py    # 数据获取模块
├── stock_web.py     # 页面生成器
├── template.html    # HTML 模板
├── deploy.sh        # 部署脚本
├── index.html       # 搜索首页 (生成)
└── generated/       # 股票页面 (生成)
    ├── 002146.html
    ├── 601288.html
    └── ...
```

## License

MIT

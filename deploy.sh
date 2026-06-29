#!/bin/bash
# deploy.sh - 部署到 GitHub Pages
# 每次运行: 重新生成所有页面 → 推送到 GitHub

set -e

cd "$(dirname "$0")"

echo "=== Stock Predictor Web 部署 ==="
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"

# 1. 生成搜索首页
echo "生成搜索首页..."
python3 stock_web.py --index

# 2. 生成默认关注的股票页面
DEFAULT_STOCKS="002146 601288 000001 600036 000858 601398"

for code in $DEFAULT_STOCKS; do
    echo "生成 $code ..."
    python3 stock_web.py $code
done

# 3. 推送到 GitHub
echo "推送到 GitHub..."
git add -A
git commit -m "Update stock pages: $(date '+%Y-%m-%d %H:%M')"
git push origin main

echo "=== 部署完成 ==="
echo "访问: https://<your-username>.github.io/Stock_Predictor/"

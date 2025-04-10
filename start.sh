#!/bin/bash
# 確保環境變數已經設置
echo "正在啟動 Kimibot..."

# 確保Python可以找到模塊
export PYTHONPATH=$PYTHONPATH:/app

# 啟動應用
exec gunicorn --bind 0.0.0.0:8080 --workers 2 --threads 4 --timeout 60 webhook:app 
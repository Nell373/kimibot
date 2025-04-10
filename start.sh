#!/bin/bash
# 該腳本用於在容器中啟動應用程序

# 設置環境變量（如果未設置）
export HOST=${HOST:-"0.0.0.0"}
export PORT=${PORT:-"8080"}

# 確保數據庫目錄存在
mkdir -p /app/database

# 顯示當前工作目錄和文件列表，用於調試
echo "現在的工作目錄是: $(pwd)"
echo "文件列表:"
ls -la

# 將目錄添加到 PYTHONPATH
export PYTHONPATH=$PYTHONPATH:/app

# 執行主應用程序
echo "啟動應用程序..."
python /app/app.py

# 如果主程序失敗，嘗試執行備份啟動命令
if [ $? -ne 0 ]; then
    echo "主程序啟動失敗，嘗試使用備份啟動命令..."
    python /app/webhook.py --port=$PORT --host=$HOST 
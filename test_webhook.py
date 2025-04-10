#!/usr/bin/env python
"""
簡易測試腳本：僅用於開發環境，不包含簽名驗證

此腳本專門設計用於本地開發環境測試webhook功能，不生成X-Line-Signature。
與test_webhook_with_signature.py的區別：
1. 此腳本不計算X-Line-Signature，僅適用於配置了跳過簽名驗證的開發環境
2. 簡化的測試流程，僅發送基本消息
3. 不適用於生產環境或完整功能測試
4. 主要用於快速調試webhook的基本響應功能

使用方法：
- 確保.env文件中已設置FLASK_ENV=development
- 確保webhook.py已配置為開發模式下跳過簽名驗證
- 執行 python test_webhook.py
"""

import json
import requests
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

def test_webhook():
    """
    發送測試消息到webhook，不包含簽名驗證
    
    警告：此函數僅適用於開發環境，因為它不生成X-Line-Signature
    正式環境中LINE平台會要求驗證簽名，使用此腳本將導致請求被拒絕
    完整測試請使用test_webhook_with_signature.py
    
    此函數會:
    1. 構建一個模擬的LINE消息事件
    2. 不計算任何簽名(這是與test_webhook_with_signature.py的主要區別)
    3. 直接發送POST請求到webhook
    4. 顯示響應結果
    """
    # 從環境變數獲取webhook URL
    webhook_url = os.environ.get('WEBHOOK_URL', 'http://localhost:5000/api/webhook')
    
    # 確認環境變數設置
    env = os.environ.get('FLASK_ENV', '')
    if env != 'development':
        print("警告: 當前環境不是'development'。這個腳本設計僅用於開發環境!")
        print(f"當前FLASK_ENV={env}")
        proceed = input("繼續執行可能會失敗，是否繼續? (y/n): ")
        if proceed.lower() != 'y':
            print("測試已取消")
            return
    
    # 模擬 LINE 消息事件 - 與真實LINE平台發送的格式相同，但沒有簽名
    message_event = {
        "destination": "xxxxxxxxxx",
        "events": [
            {
                "type": "message",
                "message": {
                    "type": "text",
                    "id": "12345678901234",
                    "text": "測試消息: 您好，這是開發環境測試！"
                },
                "timestamp": 1625665287123,
                "source": {
                    "type": "user",
                    "userId": "test_user_id"
                },
                "replyToken": "test_reply_token",
                "mode": "active"
            }
        ]
    }
    
    # 轉換為 JSON 字符串
    body = json.dumps(message_event)
    
    # 注意：此處不計算簽名，這是簡化測試的關鍵點
    # 僅設置Content-Type頭，沒有X-Line-Signature
    headers = {
        'Content-Type': 'application/json',
        # 沒有 'X-Line-Signature' 頭，這要求webhook.py在開發環境中跳過簽名驗證
    }
    
    print("=====================================")
    print(f"發送測試消息到 {webhook_url}")
    print(f"環境: {env}")
    print("警告: 此測試僅適用於開發環境，不包含簽名驗證")
    print(f"消息內容: {body}")
    print("=====================================")
    
    try:
        response = requests.post(webhook_url, headers=headers, data=body)
        print(f"響應狀態: {response.status_code}")
        print(f"響應內容: {response.text}")
    except Exception as e:
        print(f"錯誤: {str(e)}")

if __name__ == "__main__":
    test_webhook() 
#!/usr/bin/env python
"""
完整測試腳本：模擬真實LINE平台請求，包含簽名驗證

此腳本用於模擬LINE平台向webhook發送消息，並生成有效的X-Line-Signature簽名。
與test_webhook.py的區別：
1. 此腳本計算並附加正確的X-Line-Signature，與LINE平台真實請求一致
2. 適用於任何環境（開發環境和生產環境均可使用）
3. 支援測試多種不同的LINE事件類型
4. 適合在部署前進行完整功能測試

使用方法：
- 確保.env文件中已設置LINE_CHANNEL_SECRET和LINE_CHANNEL_ACCESS_TOKEN
- 執行 python test_webhook_with_signature.py 
- 根據提示選擇單一消息測試或多種消息類型測試
"""
import json
import requests
import os
import base64
import hashlib
import hmac
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

def generate_signature(channel_secret, body):
    """使用 HMAC-SHA256 生成簽名
    
    這與LINE平台用於驗證請求來源的方法相同
    
    Args:
        channel_secret: LINE頻道密鑰
        body: 請求主體JSON字符串
        
    Returns:
        base64編碼的HMAC-SHA256簽名
    """
    hash = hmac.new(channel_secret.encode('utf-8'), body.encode('utf-8'), hashlib.sha256).digest()
    signature = base64.b64encode(hash).decode('utf-8')
    return signature

# 測試 webhook
def test_webhook():
    """模擬 LINE 平台發送消息到 webhook，包含真實簽名計算
    
    此函數會:
    1. 構建一個模擬的LINE消息事件
    2. 使用頻道密鑰計算正確的簽名
    3. 發送包含簽名的POST請求到webhook
    4. 顯示響應結果
    """
    
    # 從環境變數獲取webhook URL和頻道密鑰
    webhook_url = os.environ.get('WEBHOOK_URL', 'http://localhost:5000/api/webhook')
    channel_secret = os.environ.get('LINE_CHANNEL_SECRET', 'test_secret')
    
    # 模擬 LINE 消息事件
    message_event = {
        "destination": "xxxxxxxxxx",
        "events": [
            {
                "type": "message",
                "message": {
                    "type": "text",
                    "id": "12345678901234",
                    "text": "測試消息: 您好，這是 Bot 測試！"
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
    
    # 計算簽名 - 這模擬了LINE平台如何簽署請求
    signature = generate_signature(channel_secret, body)
    
    # 發送 POST 請求到 webhook，包含X-Line-Signature頭
    headers = {
        'Content-Type': 'application/json',
        'X-Line-Signature': signature  # 與test_webhook.py的主要區別：包含有效簽名
    }
    
    print("=====================================")
    print(f"發送測試消息到 {webhook_url}")
    print(f"使用 Channel Secret: {channel_secret}")
    print(f"生成的簽名: {signature}")
    print(f"消息內容: {body}")
    print("=====================================")
    
    try:
        response = requests.post(webhook_url, headers=headers, data=body)
        print(f"響應狀態: {response.status_code}")
        print(f"響應內容: {response.text}")
    except Exception as e:
        print(f"錯誤: {str(e)}")

def test_multiple_messages():
    """測試多種不同類型的消息
    
    依次發送不同格式的消息到webhook，模擬用戶可能發送的各種指令:
    - 普通對話消息
    - 記帳指令
    - 提醒設置指令
    - 查詢指令
    
    每個消息都會計算正確的簽名並顯示響應結果
    """
    messages = [
        "測試普通消息",
        "早餐 -120",
        "#明天早上9點 開會",
        "查詢本月支出"
    ]
    
    webhook_url = os.environ.get('WEBHOOK_URL', 'http://localhost:5000/api/webhook')
    channel_secret = os.environ.get('LINE_CHANNEL_SECRET', 'test_secret')
    
    for i, message_text in enumerate(messages):
        # 模擬 LINE 消息事件
        message_event = {
            "destination": "xxxxxxxxxx",
            "events": [
                {
                    "type": "message",
                    "message": {
                        "type": "text",
                        "id": f"1234567890123{i}",
                        "text": message_text
                    },
                    "timestamp": 1625665287123 + i,
                    "source": {
                        "type": "user",
                        "userId": "test_user_id"
                    },
                    "replyToken": f"test_reply_token_{i}",
                    "mode": "active"
                }
            ]
        }
        
        # 轉換為 JSON 字符串
        body = json.dumps(message_event)
        
        # 計算簽名
        signature = generate_signature(channel_secret, body)
        
        # 發送 POST 請求到 webhook
        headers = {
            'Content-Type': 'application/json',
            'X-Line-Signature': signature
        }
        
        print("\n=====================================")
        print(f"測試消息 {i+1}: \"{message_text}\"")
        print(f"發送到 {webhook_url}")
        print("=====================================")
        
        try:
            response = requests.post(webhook_url, headers=headers, data=body)
            print(f"響應狀態: {response.status_code}")
            print(f"響應內容: {response.text}")
        except Exception as e:
            print(f"錯誤: {str(e)}")
        
        # 暫停一下，避免請求太快
        import time
        time.sleep(1)

if __name__ == "__main__":
    print("選擇測試模式:")
    print("1. 單個消息測試")
    print("2. 多種消息類型測試")
    
    choice = input("請輸入選項 (1/2): ")
    
    if choice == "1":
        test_webhook()
    elif choice == "2":
        test_multiple_messages()
    else:
        print("無效的選項，退出測試。") 
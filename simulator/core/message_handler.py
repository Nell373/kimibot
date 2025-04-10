#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
LINE 智能記帳與提醒助手 - 訊息處理器
處理從LINE模擬器收到的訊息，並返回適當的回應
"""

import logging
import json
import requests
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

logger = logging.getLogger(__name__)

class MessageHandler:
    """處理訊息的類"""
    
    def __init__(self):
        """初始化訊息處理器"""
        # 修改為模擬器模式，不要嘗試連接外部webhook
        self.webhook_url = os.environ.get('WEBHOOK_URL', None)
        logger.info("訊息處理器初始化完成")
    
    def handle_message(self, user_id, message_text):
        """處理用戶發送的訊息"""
        try:
            logger.info(f"處理訊息: {message_text} (用戶: {user_id})")
            
            # 嘗試將訊息發送到實際的webhook
            if self.webhook_url:
                try:
                    # 構建LINE訊息事件
                    event = {
                        "type": "message",
                        "replyToken": "simulator_reply_token",
                        "source": {
                            "type": "user",
                            "userId": user_id
                        },
                        "message": {
                            "type": "text",
                            "id": "simulator_message_id",
                            "text": message_text
                        }
                    }
                    
                    webhook_data = {
                        "destination": "simulator",
                        "events": [event]
                    }
                    
                    # 發送請求到webhook
                    response = requests.post(
                        self.webhook_url,
                        headers={"Content-Type": "application/json"},
                        json=webhook_data,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        # 成功得到回應
                        return response.json() if response.content else {"text": "請求已處理，但無回應內容"}
                    else:
                        # 請求失敗
                        logger.error(f"Webhook請求失敗: {response.status_code} - {response.text}")
                        return {"text": f"Webhook請求失敗: {response.status_code}"}
                        
                except Exception as e:
                    logger.error(f"發送訊息到webhook時出錯: {str(e)}")
                    # 如果發送失敗，改用模擬回應
                    logger.info("改用模擬回應模式")
                    return self._get_simulated_response(message_text)
            else:
                # 模擬模式：提供模擬回應
                logger.info("使用模擬回應模式")
                return self._get_simulated_response(message_text)
                
        except Exception as e:
            logger.error(f"處理訊息時出錯: {str(e)}")
            return {"text": f"處理訊息時出錯: {str(e)}"}
    
    def _get_simulated_response(self, message_text):
        """生成模擬回應"""
        # 處理特殊命令
        if message_text == "__reload__":
            return {"text": "模擬器已重新載入"}
            
        # 簡單的關鍵字回應
        if "你好" in message_text or "哈囉" in message_text:
            return {"text": "哈囉！我是你的智能記帳與提醒助手，有什麼可以幫你的嗎？"}
        elif "記帳" in message_text:
            if any(str(num) in message_text for num in range(10)):
                # 假設包含數字的是記帳命令
                return {
                    "type": "flex",
                    "altText": "記帳確認",
                    "contents": {
                        "type": "bubble",
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "記帳成功！",
                                    "weight": "bold",
                                    "size": "xl"
                                },
                                {
                                    "type": "text",
                                    "text": f"已記錄: {message_text}"
                                }
                            ]
                        }
                    }
                }
            else:
                return {"text": "請輸入記帳金額，例如：「記帳 100 午餐」"}
        elif "提醒" in message_text:
            return {"text": "好的，我會提醒你！請告訴我提醒的時間和內容。"}
        elif "查詢" in message_text:
            return {"text": "您想查詢什麼資訊呢？可以查詢「本月支出」、「上週收入」等。"}
        else:
            return {"text": "不太理解您的意思。您可以試試：\n- 記帳 100 午餐\n- 明天早上8點提醒我開會\n- 查詢本月支出"}

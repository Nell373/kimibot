#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
LINE 聊天界面模擬器
用於模擬 LINE 聊天界面，發送訊息和接收回應
"""

import logging
import json
import requests
import hmac
import hashlib
import base64
import time
from datetime import datetime

logger = logging.getLogger(__name__)

class LineSimulator:
    """LINE 聊天界面模擬器"""
    
    def __init__(self):
        """初始化模擬器"""
        self.user_id = "simulator_user"
        self.webhook_url = None
        self.channel_secret = None
        self.message_history = []
        logger.info("LINE 模擬器初始化完成")
    
    def configure(self, webhook_url, channel_secret):
        """配置模擬器"""
        self.webhook_url = webhook_url
        self.channel_secret = channel_secret
        logger.info(f"LINE 模擬器配置完成: webhook_url={webhook_url}")
        return True
    
    def send_message(self, text, user_id=None):
        """發送訊息到 Webhook"""
        if not user_id:
            user_id = self.user_id
            
        if not self.webhook_url:
            logger.error("未設定 webhook_url，無法發送訊息")
            return {
                "success": False,
                "error": "未設定 webhook_url"
            }
        
        # 構建 LINE 訊息事件格式
        timestamp = int(time.time() * 1000)
        event = {
            "replyToken": f"simulator-reply-{timestamp}",
            "type": "message",
            "timestamp": timestamp,
            "source": {
                "type": "user",
                "userId": user_id
            },
            "message": {
                "id": f"simulator-msg-{timestamp}",
                "type": "text",
                "text": text
            }
        }
        
        # 構建完整的請求內容
        body = {
            "destination": "simulator",
            "events": [event]
        }
        
        # 記錄發送的訊息
        self.message_history.append({
            "type": "send",
            "text": text,
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id
        })
        
        try:
            # 生成簽名 (如果有設定 channel_secret)
            headers = {
                "Content-Type": "application/json",
                "X-Line-Simulator": "true"
            }
            
            if self.channel_secret:
                body_json = json.dumps(body)
                signature = self._generate_signature(body_json)
                headers["X-Line-Signature"] = signature
            
            # 發送請求到 Webhook
            response = requests.post(
                self.webhook_url,
                headers=headers,
                json=body
            )
            
            # 檢查響應
            if response.status_code == 200:
                logger.info(f"訊息發送成功: {text}")
                return {
                    "success": True,
                    "response": response.json() if response.content else {}
                }
            else:
                logger.error(f"訊息發送失敗: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"請求失敗: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            logger.error(f"發送訊息時發生錯誤: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def receive_message(self, message_data):
        """接收回應訊息"""
        # 記錄接收的訊息
        self.message_history.append({
            "type": "receive",
            "data": message_data,
            "timestamp": datetime.now().isoformat()
        })
        logger.info(f"接收到回應: {json.dumps(message_data)[:100]}...")
        return message_data
    
    def get_message_history(self):
        """獲取訊息歷史記錄"""
        return self.message_history
    
    def clear_history(self):
        """清除訊息歷史記錄"""
        self.message_history = []
        return True
    
    def _generate_signature(self, body):
        """生成 X-Line-Signature"""
        if not self.channel_secret:
            return ""
            
        hash = hmac.new(
            self.channel_secret.encode('utf-8'),
            body.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        signature = base64.b64encode(hash).decode('utf-8')
        return signature 
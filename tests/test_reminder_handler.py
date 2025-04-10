#!/usr/bin/env python
import sys
import os
import logging
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

# 將項目根目錄添加到系統路徑中
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from handlers.message_handler import MessageHandler
from database.firebase_manager import FirebaseManager
from line_api import LineBotApi

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestReminderHandler(unittest.TestCase):
    """測試提醒處理功能"""
    
    def setUp(self):
        """初始化測試環境"""
        # 創建 mock 對象
        self.line_bot_api = MagicMock(spec=LineBotApi)
        self.firebase_manager = MagicMock(spec=FirebaseManager)
        
        # 設置 firebase_manager 的模擬返回值
        self.firebase_manager.get_user.return_value = {
            "id": "test_user_id",
            "display_name": "Test User",
            "accounts": ["銀行", "現金", "信用卡"]
        }
        self.firebase_manager.add_reminder.return_value = "reminder_id_123"
        
        # 創建 MessageHandler 實例
        self.message_handler = MessageHandler(
            line_bot_api=self.line_bot_api,
            firebase_manager=self.firebase_manager
        )
    
    def test_handle_reminder(self):
        """測試處理提醒功能"""
        # 創建模擬的解析結果
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow_str = tomorrow.strftime('%Y-%m-%d')
        
        # 測試用例
        test_cases = [
            # 基本提醒
            {
                "type": "reminder",
                "data": {
                    "content": "開會",
                    "time": "09:00",
                    "date": tomorrow_str,
                    "remind_before": 15,
                }
            },
            # 帶提前提醒的提醒
            {
                "type": "reminder",
                "data": {
                    "content": "去醫院",
                    "time": "14:30",
                    "date": tomorrow_str,
                    "remind_before": 30,
                }
            },
            # 帶重複的提醒
            {
                "type": "reminder",
                "data": {
                    "content": "吃藥",
                    "time": "08:00",
                    "date": tomorrow_str,
                    "remind_before": 15,
                    "repeat_type": "daily",
                    "repeat_value": 1
                }
            }
        ]
        
        # 運行測試
        user_id = "test_user_id"
        for i, test_case in enumerate(test_cases):
            logger.info(f"測試用例 #{i+1}")
            
            # 調用處理方法
            self.message_handler._handle_reminder(user_id, test_case["data"])
            
            # 驗證 firebase_manager.get_user 被調用
            self.firebase_manager.get_user.assert_called_with(user_id)
            
            # 驗證 firebase_manager.add_reminder 被調用
            self.firebase_manager.add_reminder.assert_called()
            
            # 驗證 line_bot_api.reply_message 被調用
            self.line_bot_api.reply_flex_message.assert_called()
            
            # 檢查傳遞給 add_reminder 的參數
            _, kwargs = self.firebase_manager.add_reminder.call_args
            reminder_data = kwargs.get("reminder_data", {})
            
            # 檢查提醒數據是否正確
            self.assertEqual(reminder_data["content"], test_case["data"]["content"])
            self.assertEqual(reminder_data["remind_before"], test_case["data"]["remind_before"])
            
            # 檢查重複設置 (如果有)
            if "repeat_type" in test_case["data"]:
                self.assertEqual(reminder_data["repeat_type"], test_case["data"]["repeat_type"])
                self.assertEqual(reminder_data["repeat_value"], test_case["data"]["repeat_value"])
            
            logger.info(f"測試通過: {reminder_data}")
        
        logger.info(f"所有測試用例通過！共 {len(test_cases)} 項測試。")

if __name__ == "__main__":
    unittest.main() 
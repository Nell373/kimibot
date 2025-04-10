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
from database.db_utils import DatabaseUtils
from linebot import LineBotApi

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
        self.db = MagicMock(spec=DatabaseUtils)
        
        # 設置 db 的模擬返回值
        self.db.get_user.return_value = {
            "user_id": "test_user_id",
            "display_name": "Test User",
            "accounts": ["銀行", "現金", "信用卡"]
        }
        self.db.add_reminder.return_value = "reminder_id_123"
        
        # 創建 MessageHandler 實例
        self.message_handler = MessageHandler(
            line_bot_api=self.line_bot_api,
            db=self.db
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
                "content": "開會",
                "time": "09:00",
                "date": tomorrow_str,
                "remind_before": 15,
            },
            # 帶提前提醒的提醒
            {
                "content": "去醫院",
                "time": "14:30",
                "date": tomorrow_str,
                "remind_before": 30,
            },
            # 帶重複的提醒
            {
                "content": "吃藥",
                "time": "08:00",
                "date": tomorrow_str,
                "remind_before": 15,
                "repeat": "daily",
                "repeat_value": 1
            }
        ]
        
        # 模擬reply_token
        reply_token = "test-reply-token"
        
        # 運行測試
        user_id = "test_user_id"
        for i, test_case in enumerate(test_cases):
            logger.info(f"測試用例 #{i+1}")
            
            # 調用處理方法
            self.message_handler._handle_reminder(user_id, reply_token, test_case)
            
            # 驗證 db.get_user 被調用
            self.db.get_user.assert_called_with(user_id)
            
            # 驗證 db.add_reminder 被調用
            self.db.add_reminder.assert_called()
            
            # 驗證 line_bot_api.reply_message 被調用
            self.line_bot_api.reply_message.assert_called()
            
            # 檢查傳遞給 add_reminder 的參數
            args, _ = self.db.add_reminder.call_args
            
            # 檢查參數
            self.assertEqual(args[0], user_id)
            self.assertEqual(args[1], test_case["content"])
            
            # 檢查日期時間格式是否正確 (應該是YYYY-MM-DDThh:mm:ss)
            expected_due_time = f"{test_case['date']}T{test_case['time']}:00"
            self.assertEqual(args[2], expected_due_time)
            
            # 檢查提醒參數
            self.assertEqual(args[4], test_case["remind_before"])
            
            # 檢查重複設置 (如果有)
            if "repeat" in test_case:
                self.assertEqual(args[5], test_case["repeat"])
                self.assertEqual(args[6], test_case["repeat_value"])
            
            logger.info(f"測試通過: {test_case}")
        
        logger.info(f"所有測試用例通過！共 {len(test_cases)} 項測試。")

if __name__ == "__main__":
    unittest.main() 
#!/usr/bin/env python
import sys
import os
import logging
from datetime import datetime, timedelta

# 將項目根目錄添加到系統路徑中
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.text_parser import TextParser

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_reminder_parser():
    """測試提醒解析功能"""
    parser = TextParser()
    
    # 測試用例
    test_cases = [
        # 基本格式: #內容
        ("#明天上午9點開會", "開會", "09:00", (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')),
        
        # 分鐘/小時後格式
        ("30分鐘後提醒我煮飯", "提醒我煮飯", None, None),  # 時間應在30分鐘後
        ("2小時後提醒我看電影", "提醒我看電影", None, None),  # 時間應在2小時後
        
        # 下週/本週格式
        ("下週二開會", "開會", "09:00", None),  # 日期應是下週二
        ("這週五下午3點看醫生", "看醫生", "15:00", None),  # 日期應是本週五
        
        # 自然語言格式
        ("提醒我明天早上8點半吃藥", "吃藥", "08:30", (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')),
        ("#後天晚上7點看電影", "看電影", "19:00", (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')),
        
        # 帶提前提醒的格式
        ("明天中午12點開會 提前20分鐘提醒", "開會", "12:00", (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'), 20),
        
        # 重複提醒格式
        ("每天早上7點起床", "起床", "07:00", datetime.now().strftime('%Y-%m-%d'), 15, "daily"),
        ("每週一下午2點開會", "開會", "14:00", None, 15, "weekly")
    ]
    
    # 運行測試
    for i, test_case in enumerate(test_cases):
        text = test_case[0]
        expected_content = test_case[1]
        expected_time = test_case[2]
        expected_date = test_case[3]
        expected_remind_before = test_case[4] if len(test_case) > 4 else 15
        expected_repeat = test_case[5] if len(test_case) > 5 else None
        
        logger.info(f"測試用例 #{i+1}: {text}")
        
        # 解析文本
        result = parser.parse_text(text)
        
        # 檢查結果類型
        assert result["type"] == "reminder", f"預期類型為 'reminder'，但得到 '{result['type']}'"
        
        # 檢查內容
        data = result["data"]
        assert "content" in data, "結果中缺少 'content' 字段"
        assert data["content"] == expected_content or expected_content in data["content"], \
            f"預期提醒內容為 '{expected_content}'，但得到 '{data['content']}'"
        
        # 檢查時間 (如果有指定)
        if expected_time:
            assert "time" in data, "結果中缺少 'time' 字段"
            assert data["time"] == expected_time, \
                f"預期時間為 '{expected_time}'，但得到 '{data['time']}'"
        
        # 檢查日期 (如果有指定)
        if expected_date:
            assert "date" in data, "結果中缺少 'date' 字段"
            assert data["date"] == expected_date, \
                f"預期日期為 '{expected_date}'，但得到 '{data['date']}'"
        
        # 檢查提前提醒時間
        assert "remind_before" in data, "結果中缺少 'remind_before' 字段"
        assert data["remind_before"] == expected_remind_before, \
            f"預期提前提醒時間為 {expected_remind_before}，但得到 {data['remind_before']}"
        
        # 檢查重複頻率 (如果有指定)
        if expected_repeat:
            assert "repeat" in data, "結果中缺少 'repeat' 字段"
            assert data["repeat"] == expected_repeat, \
                f"預期重複頻率為 '{expected_repeat}'，但得到 '{data['repeat']}'"
        
        logger.info(f"測試通過: {data}")
    
    logger.info(f"所有測試用例通過！共 {len(test_cases)} 項測試。")

if __name__ == "__main__":
    test_reminder_parser() 
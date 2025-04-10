#!/usr/bin/env python
import os
import json
import logging
import requests
from datetime import datetime, timedelta
import re

# 設置日誌
logging.basicConfig(
    level=logging.INFO if os.environ.get('LOG_LEVEL') != 'debug' else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AIParser:
    """AI 語意分析解析器，用於分析用戶輸入的自然語言並轉換為結構化資料"""
    
    def __init__(self):
        """初始化 AI 解析器"""
        self.api_key = os.environ.get('CURSOR_API_KEY')
        self.api_url = os.environ.get('CURSOR_API_URL')
        self.prompt_template = self._load_prompt_template()
        self.is_development = os.environ.get('FLASK_ENV') == 'development'
        
    def _load_prompt_template(self):
        """載入提示詞模板"""
        try:
            with open('multi_parser.prompt.txt', 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"載入提示詞模板失敗: {str(e)}")
            # 預設提示詞，以防文件無法載入
            return """你是 LINE 智能記帳與提醒助手的核心 AI 引擎。你的任務是分析用戶輸入的自然語言，並將其解析為結構化資料。"""
    
    def parse_text(self, user_input):
        """解析用戶輸入文本，返回結構化資料"""
        # 檢查輸入是否為空
        if not user_input or not user_input.strip():
            return self._create_default_response("請輸入有效的文字。")
        
        # 根據關鍵字嘗試快速匹配
        result = self._try_quick_match(user_input)
        if result:
            return result
        
        # 使用 Cursor API 進行分析
        try:
            return self._call_cursor_api(user_input)
        except Exception as e:
            logger.error(f"Cursor API 調用失敗: {str(e)}")
            # 在開發環境中使用簡單規則進行回應
            if self.is_development:
                logger.info("在開發環境中使用簡單規則進行回應")
                return self._fallback_parsing(user_input)
            return self._create_default_response("抱歉，我無法理解您的輸入。請嘗試使用更清晰的表達方式。")
    
    def _try_quick_match(self, user_input):
        """嘗試使用簡單規則匹配常見輸入模式"""
        # 移除首尾空白
        text = user_input.strip()
        
        # 檢查是否為記帳操作
        if re.search(r'[+-]\d+', text) or '收入' in text or '支出' in text:
            return self._parse_accounting(text)
        
        # 檢查是否為提醒操作
        if text.startswith('#'):
            return self._parse_reminder(text)
        
        # 檢查是否為查詢操作
        if '查詢' in text or '報表' in text or '統計' in text:
            return self._parse_query(text)
        
        # 無法快速匹配，返回 None
        return None
    
    def _call_cursor_api(self, user_input):
        """調用 Cursor API 進行自然語言分析"""
        if not self.api_key:
            raise ValueError("未設置 Cursor API 金鑰")
        
        prompt = self.prompt_template.replace('{{user_input}}', user_input)
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'prompt': prompt,
            'temperature': 0.1,  # 較低的溫度以獲得更確定性的回應
            'max_tokens': 500    # 限制回應長度
        }
        
        response = requests.post(self.api_url, headers=headers, json=payload)
        
        if response.status_code != 200:
            raise Exception(f"API 請求失敗: {response.status_code}, {response.text}")
        
        try:
            result = response.json()
            # 提取 JSON 內容
            content = result.get('choices', [{}])[0].get('text', '')
            # 解析 JSON 字符串
            json_match = re.search(r'```json(.*?)```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                json_str = content.strip()
            
            # 確保是有效的 JSON
            parsed_result = json.loads(json_str)
            return parsed_result
        except Exception as e:
            logger.error(f"解析 API 回應失敗: {str(e)}")
            raise
    
    def _fallback_parsing(self, user_input):
        """當 API 調用失敗時使用的簡單規則解析"""
        text = user_input.strip()
        
        # 記帳操作的簡單解析
        if '+' in text or '-' in text:
            return self._parse_accounting(text)
        
        # 提醒操作的簡單解析
        if text.startswith('#'):
            return self._parse_reminder(text)
        
        # 查詢操作的簡單解析
        if '查詢' in text:
            return self._parse_query(text)
        
        # 無法解析，返回一般對話
        return self._create_default_response(user_input)
    
    def _parse_accounting(self, text):
        """解析記帳操作"""
        try:
            # 提取金額
            amount_match = re.search(r'([+-])\s*(\d+)', text)
            if amount_match:
                sign, amount = amount_match.groups()
                amount = int(amount)
                if sign == '-':
                    amount = -amount
                    transaction_type = "expense"
                else:
                    transaction_type = "income"
            else:
                # 沒有明確金額，嘗試從文字判斷
                if '收入' in text:
                    amount = 0  # 無法確定具體金額
                    transaction_type = "income"
                else:
                    amount = 0  # 無法確定具體金額
                    transaction_type = "expense"
            
            # 提取項目名稱（假設在金額前的文字）
            item_match = re.search(r'(.*?)(?:[+-]\s*\d+|$)', text)
            item = item_match.group(1).strip() if item_match else "未指定項目"
            
            # 提取分類（如果有）
            category_match = re.search(r'\[(.*?)\]', text)
            category = category_match.group(1) if category_match else "一般"
            
            # 提取帳戶（如果有）
            account_match = re.search(r'<(.*?)>', text)
            account = account_match.group(1) if account_match else "現金"
            
            # 提取日期（如果有）
            date_match = re.search(r'@(.*?)(?:\s|$)', text)
            if date_match:
                date_text = date_match.group(1)
                if date_text == "今天":
                    date = datetime.now().strftime('%Y-%m-%d')
                elif date_text == "昨天":
                    date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                elif date_text == "前天":
                    date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
                else:
                    # 嘗試解析其他日期格式
                    try:
                        if '/' in date_text:
                            parts = date_text.split('/')
                            if len(parts) == 2:
                                month, day = parts
                                year = datetime.now().year
                            else:
                                year, month, day = parts
                            date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        else:
                            date = datetime.now().strftime('%Y-%m-%d')
                    except:
                        date = datetime.now().strftime('%Y-%m-%d')
            else:
                date = datetime.now().strftime('%Y-%m-%d')
            
            # 返回結構化數據
            return {
                "type": "accounting",
                "data": {
                    "item": item,
                    "amount": abs(amount),
                    "transaction_type": transaction_type,
                    "category": category,
                    "account": account,
                    "date": date
                }
            }
        except Exception as e:
            logger.error(f"解析記帳操作失敗: {str(e)}")
            return self._create_default_response("解析記帳信息失敗，請確保格式正確，例如：'午餐 -120'")
    
    def _parse_reminder(self, text):
        """解析提醒操作"""
        try:
            # 移除開頭的 #
            text = text[1:].strip()
            
            # 提取標題（假設在時間之後的所有文字）
            title_match = re.search(r'(?:\d{1,2}[:：]\d{1,2}|上午|下午|早上|晚上|中午)(?:.*?)(\S.*)', text)
            title = title_match.group(1).strip() if title_match else text
            
            # 提取提前提醒時間（如果有）
            remind_before = 15  # 預設提前 15 分鐘
            remind_match = re.search(r'提前(\d+)分鐘提醒', text)
            if remind_match:
                remind_before = int(remind_match.group(1))
            
            # 提取重複類型（如果有）
            repeat_type = "none"
            repeat_value = None
            if "每週" in text or "每周" in text:
                repeat_type = "weekly"
                week_days = {
                    "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "日": 0, "天": 0
                }
                for day, value in week_days.items():
                    if f"每週{day}" in text or f"每周{day}" in text:
                        repeat_value = value
                        break
            elif "每月" in text:
                repeat_type = "monthly"
                day_match = re.search(r'每月(\d+)號', text)
                if day_match:
                    repeat_value = int(day_match.group(1))
            elif "每天" in text:
                repeat_type = "daily"
            
            # 提取時間
            now = datetime.now()
            due_time = now.replace(hour=9, minute=0, second=0)  # 預設早上9點
            
            # 嘗試解析時間表達式
            time_patterns = [
                (r'明天', timedelta(days=1)),
                (r'後天|後日', timedelta(days=2)),
                (r'大後天', timedelta(days=3)),
                (r'下週|下周', timedelta(weeks=1)),
                (r'下個月|下月', timedelta(days=30))
            ]
            
            for pattern, delta in time_patterns:
                if re.search(pattern, text):
                    due_time = now + delta
                    break
            
            # 嘗試解析具體時間
            time_match = re.search(r'(\d{1,2})[:：](\d{1,2})', text)
            if time_match:
                hour, minute = map(int, time_match.groups())
                due_time = due_time.replace(hour=hour, minute=minute)
            elif "上午" in text or "早上" in text:
                hour_match = re.search(r'(上午|早上)(\d{1,2})點', text)
                if hour_match:
                    hour = int(hour_match.group(2))
                    due_time = due_time.replace(hour=hour)
            elif "下午" in text or "晚上" in text:
                hour_match = re.search(r'(下午|晚上)(\d{1,2})點', text)
                if hour_match:
                    hour = int(hour_match.group(2))
                    hour = hour if hour >= 12 else hour + 12
                    due_time = due_time.replace(hour=hour)
            
            # 返回結構化數據
            return {
                "type": "reminder",
                "data": {
                    "title": title,
                    "due_time": due_time.isoformat(),
                    "remind_before": remind_before,
                    "repeat_type": repeat_type,
                    "repeat_value": repeat_value
                }
            }
        except Exception as e:
            logger.error(f"解析提醒操作失敗: {str(e)}")
            return self._create_default_response("解析提醒信息失敗，請確保格式正確，例如：'#明天早上9點 開會'")
    
    def _parse_query(self, text):
        """解析查詢操作"""
        try:
            query_type = "expense"  # 預設查詢支出
            if "收入" in text:
                query_type = "income"
            elif "提醒" in text:
                query_type = "reminder"
            
            time_range = "month"  # 預設查詢本月
            time_value = "current"
            
            if "今天" in text or "本日" in text:
                time_range = "day"
                time_value = "current"
            elif "昨天" in text:
                time_range = "day"
                time_value = "previous"
            elif "本週" in text or "這週" in text or "本周" in text or "這周" in text:
                time_range = "week"
                time_value = "current"
            elif "上週" in text or "上周" in text:
                time_range = "week"
                time_value = "previous"
            elif "本月" in text or "這個月" in text:
                time_range = "month"
                time_value = "current"
            elif "上個月" in text or "上月" in text:
                time_range = "month"
                time_value = "previous"
            
            # 提取可能的分類
            category = None
            categories = ["飲食", "交通", "購物", "娛樂", "醫療", "教育", "居家", "其他"]
            for cat in categories:
                if cat in text:
                    category = cat
                    break
            
            # 返回結構化數據
            return {
                "type": "query",
                "data": {
                    "query_type": query_type,
                    "time_range": time_range,
                    "time_value": time_value,
                    "category": category
                }
            }
        except Exception as e:
            logger.error(f"解析查詢操作失敗: {str(e)}")
            return self._create_default_response("解析查詢信息失敗，請確保格式正確，例如：'查詢本月支出'")
    
    def _create_default_response(self, message):
        """創建預設回應"""
        return {
            "type": "conversation",
            "data": {
                "message": message,
                "keywords": []
            }
        } 
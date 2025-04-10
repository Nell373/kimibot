#!/usr/bin/env python
import re
import logging
import os
from datetime import datetime, timedelta

# 設置日誌
logging.basicConfig(
    level=logging.INFO if os.environ.get('LOG_LEVEL') != 'debug' else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TextParser:
    """自然語言解析器，用於分析用戶輸入並轉換為結構化資料"""
    
    def __init__(self):
        """初始化解析器"""
        self.is_development = os.environ.get('FLASK_ENV') == 'development'
        
        # 定義可能的支出和收入關鍵詞
        self.expense_keywords = [
            "支出", "花費", "消費", "付款", "付", "買", "購買", 
            "嗯", "花了", "支付", "花", "用了", "出", "花掉"
        ]
        self.income_keywords = [
            "收入", "賺", "收", "得到", "獲得", "贏得", "收款", 
            "進", "入帳", "收到", "發薪水", "薪資", "薪水"
        ]
        
        # 定義常見的消費類別和關鍵詞映射
        self.expense_categories_mapping = {
            "飲食": ["飯", "餐", "食", "吃", "喝", "飲料", "水", "早餐", "午餐", "晚餐", "宵夜", "點心", "零食", "咖啡"],
            "交通": ["車", "票", "機票", "高鐵", "捷運", "公車", "計程車", "油費", "加油", "停車", "過路費", "uber", "ubike"],
            "購物": ["買", "購", "衣", "服", "鞋", "包", "電子", "3C", "家電", "傢俱", "裝飾", "日用品"],
            "娛樂": ["電影", "遊戲", "旅遊", "旅行", "玩", "唱歌", "KTV", "party", "趴踢", "爬山", "運動", "健身", "展覽"],
            "醫療": ["醫", "藥", "看病", "掛號", "門診", "住院", "手術", "保健", "牙醫", "眼科", "檢查"],
            "教育": ["學", "書", "課", "班", "教材", "補習", "講義", "文具", "考試", "證照"],
            "居家": ["房租", "水費", "電費", "瓦斯費", "網路費", "管理費", "裝修", "清潔", "家具", "家電", "電話費"],
            "其他": []
        }
        
        # 定義常見的收入類別和關鍵詞映射
        self.income_categories_mapping = {
            "薪資": ["薪水", "薪資", "工資", "工作", "月薪", "週薪", "年薪", "加班費", "兼職"],
            "獎金": ["獎金", "分紅", "年終", "獎勵", "禮金", "紅包", "抽獎"],
            "投資": ["股", "投資", "基金", "股利", "利息", "租金", "理財", "定存", "股票", "債券", "配息"],
            "退款": ["退款", "退費", "賠償", "保險理賠", "報銷", "補貼", "退稅"],
            "其他": []
        }
        
        # 定義常見的帳戶類型和關鍵詞
        self.account_mapping = {
            "現金": ["現金", "錢包", "口袋", "cash"],
            "信用卡": ["信用卡", "卡", "visa", "master", "jcb", "刷卡"],
            "銀行": ["銀行", "帳戶", "轉帳", "ATM", "金融卡", "存款"],
            "電子支付": ["電子支付", "行動支付", "Line Pay", "街口", "悠遊付", "Apple Pay", "Google Pay", "支付寶", "微信支付", "Pi拍錢包"]
        }
        
    def parse_text(self, user_input):
        """解析用戶輸入文本，返回結構化資料"""
        # 檢查輸入是否為空
        if not user_input or not user_input.strip():
            return self._create_default_response("請輸入有效的文字。")
        
        # 嘗試匹配常見的輸入模式
        text = user_input.strip()
        
        # 檢查是否為新增帳戶操作
        if text.startswith("新增帳戶") or text.startswith("添加帳戶") or text.startswith("加入帳戶"):
            return self._parse_account_command(text)
        
        # 檢查是否為記帳操作 (增加更多記帳相關的關鍵詞匹配)
        if (re.search(r'[+-]?\d+\.?\d*', text) and any(keyword in text for keyword in self.expense_keywords + self.income_keywords)) or \
           re.search(r'[+-]\d+', text) or \
           any(keyword in text for keyword in ["收入", "支出", "記帳", "記個帳", "記錄一筆", "消費", "花了", "賺了"]):
            return self._parse_accounting(text)
        
        # 檢查是否為提醒操作
        if text.startswith('#') or re.search(r'提醒我|提醒|備忘|備註', text):
            return self._parse_reminder(text)
        
        # 檢查是否為查詢操作
        if any(keyword in text for keyword in ["查詢", "報表", "統計", "顯示", "列出", "多少", "花費", "花了多少", "賺了多少", "查看", "查一下"]):
            return self._parse_query(text)
        
        # 無法快速匹配，返回一般對話
        return self._create_default_response(f"我無法理解您的輸入「{text}」。請嘗試使用記帳、提醒或查詢的格式。")
    
    def _parse_account_command(self, text):
        """解析帳戶相關命令"""
        try:
            # 提取帳戶名稱
            # 移除命令前綴
            clean_text = re.sub(r'^(新增帳戶|添加帳戶|加入帳戶)\s*', '', text)
            
            # 如果沒有提供帳戶名稱
            if not clean_text.strip():
                return self._create_default_response("請提供帳戶名稱，格式：新增帳戶 [帳戶名稱]")
            
            account_name = clean_text.strip()
            
            # 返回結構化數據
            return {
                "type": "account_command",
                "data": {
                    "action": "add_account",
                    "account_name": account_name
                }
            }
        except Exception as e:
            logger.error(f"解析帳戶命令失敗: {str(e)}")
            return self._create_default_response("解析帳戶命令失敗，請確保格式正確，例如：「新增帳戶 現金」")
    
    def _parse_accounting(self, text):
        """解析記帳操作"""
        try:
            # 確定交易類型 (收入或支出)
            transaction_type = "expense"  # 預設為支出
            if any(keyword in text for keyword in self.income_keywords):
                transaction_type = "income"
            
            # 提取金額
            # 處理常見的金額表述方式
            amount_patterns = [
                # 標準格式：+/-數字
                r'([+-])?\s*(\d+\.?\d*)',
                # "花了/消費了/支付了/付了 數字元/塊/圓/RMB/NT/NT$"
                r'(?:花了|消費了|支付了|付了|用了)\s*(\d+\.?\d*)\s*(?:元|塊|圓|RMB|NT|NT\$)?',
                # "數字元/塊/圓/RMB/NT/NT$"
                r'(\d+\.?\d*)\s*(?:元|塊|圓|RMB|NT|NT\$)',
                # "賺了/收入/得到了 數字元/塊/圓/RMB/NT/NT$"
                r'(?:賺了|收入|得到了|獲得了)\s*(\d+\.?\d*)\s*(?:元|塊|圓|RMB|NT|NT\$)?',
                # "買了XX(數字)元/塊"
                r'買了.*?(\d+\.?\d*)\s*(?:元|塊|圓|RMB|NT|NT\$)?',
                # "XX花費(數字)元/塊"
                r'.*?花費\s*(\d+\.?\d*)\s*(?:元|塊|圓|RMB|NT|NT\$)?',
                # "使用XX支付(數字)元/塊"
                r'使用.*?支付\s*(\d+\.?\d*)\s*(?:元|塊|圓|RMB|NT|NT\$)?',
                # "薪資/工資(數字)元/塊"
                r'(?:薪資|工資|薪水)\s*(\d+\.?\d*)\s*(?:元|塊|圓|RMB|NT|NT\$)?'
            ]
            
            amount = 0
            amount_found = False
            
            for pattern in amount_patterns:
                amount_match = re.search(pattern, text)
                if amount_match:
                    # 對於第一種模式，檢查是否有+/-符號
                    if pattern == r'([+-])?\s*(\d+\.?\d*)':
                        sign = amount_match.group(1) if amount_match.group(1) else ""
                        amount = float(amount_match.group(2))
                        
                        # 根據前綴符號判斷交易類型
                        if sign == '+':
                            transaction_type = "income"
                        elif sign == '-':
                            transaction_type = "expense"
                    # 對於「賺了/收入」模式，設為收入
                    elif pattern.startswith(r'(?:賺了|收入|得到了|獲得了)') or pattern.startswith(r'(?:薪資|工資|薪水)'):
                        amount = float(amount_match.group(1))
                        transaction_type = "income"
                    # 對於其他模式，提取數字部分
                    else:
                        amount = float(amount_match.group(1))
                    
                    amount_found = True
                    break
            
            # 如果沒有找到金額，嘗試找出任何數字
            if not amount_found:
                number_match = re.search(r'(\d+\.?\d*)', text)
                if number_match:
                    amount = float(number_match.group(1))
                else:
                    amount = 0  # 無法確定具體金額
            
            # 提取項目名稱
            # 移除金額和特殊格式標記
            clean_text = re.sub(r'[+-]?\s*\d+\.?\d*\s*(?:元|塊|圓|RMB|NT|NT\$)?', '', text)
            clean_text = re.sub(r'(?:花了|消費了|支付了|付了|用了|賺了|收入|得到了|獲得了|花費)\s*\d+\.?\d*\s*(?:元|塊|圓|RMB|NT|NT\$)?', '', clean_text)
            clean_text = re.sub(r'\[.*?\]', '', clean_text)  # 移除分類標記 [分類]
            clean_text = re.sub(r'<.*?>', '', clean_text)    # 移除帳戶標記 <帳戶>
            clean_text = re.sub(r'@.*?(?:\s|$)', '', clean_text)  # 移除日期標記 @日期
            
            # 識別常見的消費場景
            common_expense_items = {
                "食品": ["超市", "大賣場", "菜市場", "買菜", "蔬菜", "水果", "肉類", "食品"],
                "餐飲": ["早餐", "午餐", "晚餐", "夜宵", "飯", "餐", "吃飯", "餐廳", "小吃", "飲料", "咖啡", "奶茶"],
                "交通": ["計程車", "出租車", "公車", "地鐵", "高鐵", "火車", "機票", "油費", "加油", "停車費", "交通"],
                "購物": ["衣服", "鞋子", "包包", "電子產品", "家電", "購物", "買", "商場", "百貨", "網購"],
                "娛樂": ["電影", "遊戲", "演唱會", "KTV", "唱歌", "酒吧", "娛樂"],
                "醫療": ["醫院", "診所", "醫生", "藥", "看病", "醫療"],
                "住宿": ["房租", "水電", "瓦斯", "電費", "水費", "網路費", "住宿"],
                "通訊": ["手機費", "電話費", "網路費", "通訊"],
                "學習": ["書", "課程", "學費", "補習", "學習"],
                "寵物": ["寵物", "狗", "貓", "寵物用品", "寵物食品"]
            }
            
            # 嘗試從文本中識別項目類型
            item_type = None
            for category, keywords in common_expense_items.items():
                if any(keyword in clean_text for keyword in keywords):
                    item_type = category
                    break
            
            # 移除額外的空格並取得項目名稱
            item = re.sub(r'\s+', ' ', clean_text).strip()
            
            # 如果項目為空，但找到了類型，則使用類型作為項目
            if not item and item_type:
                item = item_type
            
            # 如果項目仍為空，設置預設值
            if not item:
                if transaction_type == "expense":
                    item = "支出項目"
                else:
                    item = "收入項目"
            
            # 提取分類（如果有指定）
            category = None
            category_match = re.search(r'\[(.*?)\]', text)
            if category_match:
                category = category_match.group(1)
            else:
                # 如果沒有明確指定分類，但找到了項目類型，使用項目類型作為分類
                if item_type:
                    category = item_type
                # 否則，嘗試從項目中推斷分類
                else:
                    if transaction_type == "expense":
                        for cat, keywords in self.expense_categories_mapping.items():
                            if any(keyword in text for keyword in keywords):
                                category = cat
                                break
                    else:  # income
                        for cat, keywords in self.income_categories_mapping.items():
                            if any(keyword in text for keyword in keywords):
                                category = cat
                                break
            
            # 提取帳戶（如果有）
            account = None
            account_match = re.search(r'<(.*?)>', text)
            if account_match:
                account = account_match.group(1)
            else:
                # 更全面的帳戶提取邏輯
                account_patterns = [
                    # 直接提及帳戶："使用/用XX帳戶/卡/支付"
                    r'(?:使用|用|透過|經由|從)\s*([\w\s]+?)(?:帳戶|卡|支付)',
                    # 提及支付方式："用XX付款/支付"
                    r'(?:用|透過|使用)\s*([\w\s]+?)(?:付款|支付|付|刷|買)'
                ]
                
                for pattern in account_patterns:
                    acc_match = re.search(pattern, text)
                    if acc_match:
                        potential_account = acc_match.group(1).strip()
                        # 檢查是否與已知帳戶類型匹配
                        for acc_type, keywords in self.account_mapping.items():
                            if any(keyword.lower() in potential_account.lower() for keyword in keywords):
                                account = acc_type
                                break
                        # 如果沒有匹配到已知類型，直接使用提取的文本
                        if not account:
                            account = potential_account
                        break
                
                # 如果上述模式未匹配，嘗試從文本中尋找已知的帳戶關鍵詞
                if not account:
                    for acc, keywords in self.account_mapping.items():
                        if any(keyword in text for keyword in keywords):
                            account = acc
                            break
            
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
                        elif '-' in date_text:
                            parts = date_text.split('-')
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
                # 嘗試從文本中識別日期提示
                if "今天" in text:
                    date = datetime.now().strftime('%Y-%m-%d')
                elif "昨天" in text:
                    date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                elif "前天" in text:
                    date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
                else:
                    # 尋找形如"4月1日"或"4/1"或"昨天"的日期表達
                    date_patterns = [
                        r'(\d{1,2})(?:月|\/|-)(\d{1,2})(?:日|號)?',  # 4月1日, 4/1, 4-1
                        r'(\d{4})(?:年)(\d{1,2})(?:月|\/|-)(\d{1,2})(?:日|號)?',  # 2023年4月1日, 2023/4/1
                        r'(今天|昨天|前天)',  # 今天, 昨天, 前天
                        r'(?:上個?|這個?|下個?)?(星期|週|周)([一二三四五六日天])'  # 上週一, 這週二, 下週三
                    ]

                    for pattern in date_patterns:
                        date_match = re.search(pattern, text)
                        if date_match:
                            if pattern == r'(\d{1,2})(?:月|\/|-)(\d{1,2})(?:日|號)?':
                                month, day = date_match.groups()
                                year = datetime.now().year
                                date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                            elif pattern == r'(\d{4})(?:年)(\d{1,2})(?:月|\/|-)(\d{1,2})(?:日|號)?':
                                year, month, day = date_match.groups()
                                date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                            elif pattern == r'(今天|昨天|前天)':
                                day_text = date_match.group(1)
                                days_offset = {"今天": 0, "昨天": 1, "前天": 2}.get(day_text, 0)
                                date = (datetime.now() - timedelta(days=days_offset)).strftime('%Y-%m-%d')
                            elif pattern == r'(?:上個?|這個?|下個?)?(星期|週|周)([一二三四五六日天])':
                                week_prefix, weekday_text = date_match.groups() if date_match.groups()[0] else ("這", date_match.groups()[1])
                                weekday_mapping = {"一": 0, "二": 1, "三": 2, "四": 3, "五": 4, "六": 5, "日": 6, "天": 6}
                                target_weekday = weekday_mapping.get(weekday_text, 0)
                                
                                # 獲取當前日期的星期幾 (0-6, 0表示星期一)
                                current_weekday = datetime.now().weekday()
                                
                                # 計算目標日期與當前日期的差距
                                delta_days = 0
                                if week_prefix in ["上", "上個"]:
                                    # 上週：回到上週的對應天
                                    delta_days = target_weekday - current_weekday - 7
                                elif week_prefix in ["下", "下個"]:
                                    # 下週：去到下週的對應天
                                    delta_days = target_weekday - current_weekday + 7
                                else:
                                    # 本週：去到本週的對應天
                                    delta_days = target_weekday - current_weekday
                                
                                if delta_days < -7:
                                    delta_days += 7
                                elif delta_days > 7:
                                    delta_days -= 7
                                
                                date = (datetime.now() + timedelta(days=delta_days)).strftime('%Y-%m-%d')
                            break
                    else:
                        date = datetime.now().strftime('%Y-%m-%d')
            
            # 處理金額為負值的特殊情況
            if transaction_type == "expense":
                amount = abs(amount)
            
            # 返回結構化數據
            return {
                "type": "accounting",
                "data": {
                    "item": item,
                    "amount": amount,
                    "transaction_type": transaction_type,
                    "category": category,
                    "account": account,
                    "date": date
                }
            }
        except Exception as e:
            logger.error(f"解析記帳操作失敗: {str(e)}")
            return self._create_default_response("解析記帳信息失敗，請確保格式正確，例如：「午餐 -120」或「早餐花了80元」")
    
    def _parse_reminder(self, text):
        """
        解析設置提醒的操作
        支持的格式：
        - 提醒我明天早上8點去健身
        - 每天晚上10點提醒我睡覺
        - 下週一早上提醒我開會
        - 5月1日下午3點提醒繳稅
        """
        try:
            # 清理文本
            text = self._clean_text(text)
            
            # 確認是否是提醒操作
            if not any(keyword in text for keyword in ["提醒", "記得", "別忘了", "記住"]):
                return None
            
            # 提取提醒內容
            remind_patterns = [
                r'提醒(?:我|一下)?(.+?)(?:在|於|到時|$)',  # 提醒我XXX
                r'(?:記得|別忘了|記住)(.+?)(?:在|於|到時|$)',  # 記得XXX, 別忘了XXX
                r'(?:在|於)(.+?)(?:提醒|記得|記住|別忘)(?:我)?(.+?)(?:到時|$)',  # 在XXX提醒我YYY
            ]
            
            content = ""
            time_part = ""
            
            for pattern in remind_patterns:
                match = re.search(pattern, text)
                if match:
                    groups = match.groups()
                    if len(groups) == 1:
                        # 提取出可能包含時間和內容的文本
                        full_text = groups[0].strip()
                        # 尋找時間表達式
                        time_match = re.search(r'(今天|明天|後天|大後天|\d+月\d+日|下週[一二三四五六日天]|週[一二三四五六日天]|星期[一二三四五六日天]|下個?月\d+號?)?(早上|上午|中午|下午|晚上)?(\d+點|\d+[:：]\d+)?', full_text)
                        
                        if time_match:
                            time_info = ''.join([x for x in time_match.groups() if x])
                            if time_info:
                                time_part = time_info
                                # 從完整文本中移除時間信息，剩下的就是提醒內容
                                content = full_text.replace(time_info, '').strip()
                                
                        if not content:  # 如果沒有分離出內容，整個文本就是內容
                            content = full_text
                    
                    elif len(groups) == 2:
                        # 第一部分是時間，第二部分是內容
                        time_part = groups[0].strip()
                        content = groups[1].strip()
                    
                    break
            
            if not content:
                # 如果沒有找到內容，可能需要更進一步的處理
                # 這裡可以添加更多的匹配模式
                return None
            
            # 解析日期時間
            parsed_time = self._parse_reminder_time(time_part, text)
            
            return {
                "content": content,
                "time": parsed_time,
                "is_recurring": "每" in text or "每天" in text or "每週" in text or "每月" in text
            }
        
        except Exception as e:
            logging.error(f"解析提醒操作時發生錯誤: {e}")
            return None
    
    def _parse_reminder_time(self, time_part, full_text):
        """解析提醒時間"""
        now = datetime.now()
        reminder_time = now
        
        # 如果沒有具體時間，默認設置為明天早上9點
        if not time_part:
            return (now + timedelta(days=1)).replace(hour=9, minute=0, second=0)
        
        # 提取日期部分
        day_offset = 0
        if "今天" in time_part or "今天" in full_text:
            day_offset = 0
        elif "明天" in time_part or "明天" in full_text:
            day_offset = 1
        elif "後天" in time_part or "後天" in full_text:
            day_offset = 2
        elif "大後天" in time_part or "大後天" in full_text:
            day_offset = 3
        
        # 提取星期信息
        weekday_pattern = r'(?:下週|週|星期)([一二三四五六日天])'
        weekday_match = re.search(weekday_pattern, time_part) or re.search(weekday_pattern, full_text)
        if weekday_match:
            weekday_text = weekday_match.group(1)
            weekday_mapping = {"一": 0, "二": 1, "三": 2, "四": 3, "五": 4, "六": 5, "日": 6, "天": 6}
            target_weekday = weekday_mapping.get(weekday_text, 0)
            
            current_weekday = now.weekday()
            if "下週" in time_part or "下週" in full_text:
                # 下週對應的日期
                days_to_add = 7 - current_weekday + target_weekday
                reminder_time = now + timedelta(days=days_to_add)
            else:
                # 本週對應的日期
                if target_weekday > current_weekday:
                    days_to_add = target_weekday - current_weekday
                else:
                    days_to_add = 7 + target_weekday - current_weekday
                reminder_time = now + timedelta(days=days_to_add)
        
        # 提取具體的月日
        date_pattern = r'(\d+)月(\d+)[日號]'
        date_match = re.search(date_pattern, time_part) or re.search(date_pattern, full_text)
        if date_match:
            month, day = map(int, date_match.groups())
            year = now.year
            # 如果設置的日期已經過了，默認為明年
            if (month < now.month) or (month == now.month and day < now.day):
                year += 1
            
            try:
                reminder_time = reminder_time.replace(year=year, month=month, day=day)
            except ValueError:
                # 處理無效日期，例如2月30日
                reminder_time = reminder_time.replace(year=year, month=month, day=1) + timedelta(days=day-1)
        
        # 提取時間部分
        has_time = False
        time_of_day = {"早上": 8, "上午": 10, "中午": 12, "下午": 15, "晚上": 20}
        for tod, hour in time_of_day.items():
            if tod in time_part or tod in full_text:
                reminder_time = reminder_time.replace(hour=hour, minute=0, second=0)
                has_time = True
                break
        
        # 提取具體的小時和分鐘
        hour_pattern = r'(\d+)[點:](\d+)?'
        hour_match = re.search(hour_pattern, time_part) or re.search(hour_pattern, full_text)
        if hour_match:
            hour = int(hour_match.group(1))
            minute = int(hour_match.group(2) or 0)
            
            # 處理12小時制轉24小時制
            if "下午" in time_part or "下午" in full_text or "晚上" in time_part or "晚上" in full_text:
                if hour < 12:
                    hour += 12
            
            reminder_time = reminder_time.replace(hour=hour, minute=minute, second=0)
            has_time = True
        
        # 如果只有日期沒有時間，默認設為當天早上9點
        if not has_time:
            if day_offset > 0:
                reminder_time = reminder_time + timedelta(days=day_offset)
            reminder_time = reminder_time.replace(hour=9, minute=0, second=0)
        else:
            if day_offset > 0:
                reminder_time = reminder_time + timedelta(days=day_offset)
        
        # 如果設置的時間已經過去，且是今天的提醒，則設置為明天同一時間
        if reminder_time < now and reminder_time.date() == now.date():
            reminder_time = reminder_time + timedelta(days=1)
        
        return reminder_time.strftime('%Y-%m-%d %H:%M:%S')
    
    def _parse_query(self, text):
        """解析查詢操作"""
        try:
            # 檢查是否是查詢指令
            query_keywords = ["查詢", "查看", "顯示", "統計", "報表", "多少", "花費", "花了", "記錄", "支出", "收入", "一共", "共計", "總共"]
            is_query = any(keyword in text for keyword in query_keywords)
            
            if not is_query:
                return None
            
            # 查詢類型
            query_type = "expense"  # 預設查詢支出
            if any(keyword in text for keyword in ["收入", "賺", "賺了", "獲得", "收到"]):
                query_type = "income"
            elif any(keyword in text for keyword in ["提醒", "待辦", "代辦", "行程", "活動"]):
                query_type = "reminder"
            elif any(keyword in text for keyword in ["餘額", "結餘", "剩餘", "帳戶"]):
                query_type = "balance"
            elif any(keyword in text for keyword in ["總覽", "概況", "彙總", "匯總", "所有"]):
                query_type = "overview"
            
            # 時間範圍
            time_range = "month"  # 預設查詢本月
            time_value = "current"
            
            # 特定日期模式
            specific_date_pattern = r'(\d{4})[/\-年]?(\d{1,2})[/\-月]?(\d{1,2})?[日號]?'
            specific_date_match = re.search(specific_date_pattern, text)
            
            if specific_date_match:
                year = int(specific_date_match.group(1))
                month = int(specific_date_match.group(2))
                day = int(specific_date_match.group(3)) if specific_date_match.group(3) else None
                
                if day:
                    time_range = "day"
                    time_value = f"{year}-{month:02d}-{day:02d}"
                else:
                    time_range = "month"
                    time_value = f"{year}-{month:02d}"
            else:
                # 相對日期描述
                if any(keyword in text for keyword in ["今天", "本日", "當日"]):
                    time_range = "day"
                    time_value = "current"
                elif any(keyword in text for keyword in ["昨天", "昨日", "前一天"]):
                    time_range = "day"
                    time_value = "previous"
                elif any(keyword in text for keyword in ["本週", "這週", "本周", "這周", "當週"]):
                    time_range = "week"
                    time_value = "current"
                elif any(keyword in text for keyword in ["上週", "上个週", "前一週", "上周", "前一周"]):
                    time_range = "week"
                    time_value = "previous"
                elif any(keyword in text for keyword in ["本月", "這個月", "當月", "這月"]):
                    time_range = "month"
                    time_value = "current"
                elif any(keyword in text for keyword in ["上個月", "上月", "前一月", "前月"]):
                    time_range = "month"
                    time_value = "previous"
                elif any(keyword in text for keyword in ["今年", "本年", "這一年"]):
                    time_range = "year"
                    time_value = "current"
                elif any(keyword in text for keyword in ["去年", "上一年", "前一年"]):
                    time_range = "year"
                    time_value = "previous"
            
            # 提取可能的分類
            category = None
            categories = {
                "飲食": ["飲食", "餐廳", "餐飲", "吃飯", "早餐", "午餐", "晚餐", "宵夜", "食物", "小吃"],
                "交通": ["交通", "車費", "油費", "停車費", "計程車", "高鐵", "火車", "捷運", "公車", "機票"],
                "購物": ["購物", "服飾", "衣服", "鞋子", "包包", "電子產品", "家電", "日用品"],
                "娛樂": ["娛樂", "電影", "遊戲", "音樂", "演唱會", "旅遊", "旅行", "度假"],
                "醫療": ["醫療", "醫院", "診所", "藥品", "牙醫", "看病", "健保"],
                "教育": ["教育", "學費", "書籍", "文具", "課程", "補習", "學習"],
                "居家": ["居家", "房租", "水電", "網路費", "家具", "家居", "租金", "管理費"],
                "其他": ["其他", "雜項", "雜費", "未分類"]
            }
            
            for cat, keywords in categories.items():
                if any(keyword in text for keyword in keywords):
                    category = cat
                    break
            
            # 提取可能的帳戶
            account = None
            accounts = {
                "現金": ["現金", "零用金", "錢包"],
                "銀行卡": ["銀行卡", "金融卡", "提款卡", "儲蓄卡"],
                "信用卡": ["信用卡", "卡費", "刷卡"],
                "行動支付": ["行動支付", "電子支付", "支付寶", "微信支付", "Apple Pay", "Google Pay", "街口支付", "Line Pay"]
            }
            
            for acc, keywords in accounts.items():
                if any(keyword in text for keyword in keywords):
                    account = acc
                    break
            
            # 返回結構化數據
            return {
                "type": "query",
                "data": {
                    "query_type": query_type,
                    "time_range": time_range,
                    "time_value": time_value,
                    "category": category,
                    "account": account
                }
            }
        except Exception as e:
            logger.error(f"解析查詢操作失敗: {str(e)}")
            return self._create_default_response("解析查詢信息失敗，請確保格式正確，例如：「查詢本月支出」")
    
    def _create_default_response(self, message):
        """創建預設回應"""
        return {
            "type": "conversation",
            "data": {
                "message": message,
                "keywords": []
            }
        } 
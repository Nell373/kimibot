#!/usr/bin/env python
import json
import logging
import os
from datetime import datetime, date, timedelta
# 更新LINE Bot SDK導入
from linebot.v3.messaging import (
    ApiClient, MessagingApi, Configuration,
    TextMessage, FlexMessage, FlexContainer,
    ReplyMessageRequest, RichMenuRequest, RichMenuArea, RichMenuSize, RichMenuBounds,
    URIAction, PostbackAction, FlexButton as ButtonComponent, 
    FlexComponent as BoxComponent, 
    FlexComponent as IconComponent, FlexComponent as TextComponent, FlexComponent as SeparatorComponent
)
from database.db_utils import DatabaseUtils
from parsers.text_parser import TextParser
import re

# 設置日誌
logging.basicConfig(
    level=logging.INFO if os.environ.get('LOG_LEVEL') != 'debug' else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MessageHandler:
    """LINE 訊息處理器，負責處理用戶的訊息並協調各種功能"""
    
    def __init__(self, line_bot_api=None, db=None):
        """初始化處理器"""
        self.line_bot_api = line_bot_api
        self.db = db if db else DatabaseUtils()
        self.text_parser = TextParser()
        self.is_development = os.environ.get('FLASK_ENV') == 'development'
        
        # 定義支出分類
        self.expense_categories = [
            {"name": "飲食", "icon": "🍔"},
            {"name": "交通", "icon": "🚗"},
            {"name": "購物", "icon": "🛒"},
            {"name": "娛樂", "icon": "🎬"},
            {"name": "醫療", "icon": "💊"},
            {"name": "教育", "icon": "📚"},
            {"name": "居家", "icon": "🏠"},
            {"name": "其他", "icon": "📦"}
        ]
        
        # 定義收入分類
        self.income_categories = [
            {"name": "薪資", "icon": "💰"},
            {"name": "獎金", "icon": "🎁"},
            {"name": "投資", "icon": "📈"},
            {"name": "退款", "icon": "💸"},
            {"name": "其他", "icon": "💵"}
        ]
        
        # 定義顏色
        self.colors = {
            "primary": "#4F86C6",
            "secondary": "#7FC4FD",
            "success": "#4CAF50",
            "danger": "#F44336",
            "warning": "#FF9800",
            "info": "#2196F3",
            "light": "#F5F5F5",
            "dark": "#333333",
            "expense": "#F44336",
            "income": "#4CAF50"
        }
    
    def handle_message(self, event):
        """處理用戶發送的訊息"""
        user_id = event.source.user_id
        text = event.message.text
        reply_token = event.reply_token
        
        logger.info(f"處理用戶 {user_id} 的訊息: {text}")
        
        try:
            # 解析用戶輸入
            parse_result = self.text_parser.parse_text(text)
            message_type = parse_result.get("type")
            data = parse_result.get("data", {})
            
            # 根據不同類型的訊息進行處理
            if message_type == "accounting":
                self._handle_accounting(user_id, reply_token, data)
            elif message_type == "reminder":
                self._handle_reminder(user_id, reply_token, data)
            elif message_type == "query":
                self._handle_query(user_id, reply_token, data)
            elif message_type == "account_command":
                self._handle_account_command(user_id, reply_token, data)
            else:
                # 一般對話
                self._reply_text(reply_token, data.get("message", "抱歉，我不明白您的意思。"))
        except Exception as e:
            logger.error(f"處理訊息時發生錯誤: {str(e)}")
            self._reply_text(reply_token, f"處理您的訊息時發生錯誤，請稍後再試。")
    
    def handle_postback(self, event):
        """處理用戶的選擇回調"""
        user_id = event.source.user_id
        postback_data = event.postback.data
        reply_token = event.reply_token
        
        logger.info(f"處理用戶 {user_id} 的 postback: {postback_data}")
        
        try:
            # 解析 postback 資料
            parsed_data = json.loads(postback_data)
            action = parsed_data.get("action")
            
            if action == "select_category":
                self._handle_category_selection(user_id, reply_token, parsed_data)
            elif action == "select_account":
                self._handle_account_selection(user_id, reply_token, parsed_data)
            elif action == "add_account":
                # 處理添加新帳戶的請求
                self._handle_account_selection(user_id, reply_token, parsed_data)
            elif action == "complete_reminder":
                self._handle_complete_reminder(user_id, reply_token, parsed_data)
            elif action == "delete_reminder":
                self._handle_delete_reminder(user_id, reply_token, parsed_data)
            # 處理快速選單操作
            elif action.startswith("quick_"):
                self.handle_quick_menu_action(user_id, reply_token, parsed_data)
            # 處理快速分類選擇
            elif action == "quick_category_selected":
                self._handle_quick_category_selected(user_id, reply_token, parsed_data)
            # 處理快速帳戶選擇
            elif action == "quick_account_selected":
                self._handle_quick_account_selected(user_id, reply_token, parsed_data)
            # 處理快速查詢選擇
            elif action == "quick_query_selected":
                self._handle_quick_query_selected(user_id, reply_token, parsed_data)
            else:
                self._reply_text(reply_token, "未知的操作，請重試。")
        except Exception as e:
            logger.error(f"處理 postback 時發生錯誤: {str(e)}")
            self._reply_text(reply_token, f"處理您的選擇時發生錯誤，請稍後再試。")
    
    def _handle_accounting(self, user_id, reply_token, data):
        """處理記帳操作"""
        transaction_type = data.get("transaction_type")
        item = data.get("item", "未指定項目")
        amount = data.get("amount", 0)
        category = data.get("category")
        account = data.get("account")
        trans_date = data.get("date", date.today().isoformat())
        
        # 確保用戶存在於資料庫
        user = self.db.get_user(user_id)
        if not user:
            logger.warning(f"用戶 {user_id} 不存在於資料庫中")
            # 這裡不處理用戶創建，假設 webhook.py 已經處理了
        
        # 如果沒有指定帳戶和分類，顯示帳戶選擇界面
        if not account and not category:
            # 獲取用戶的所有帳戶
            accounts = self.db.get_accounts(user_id)
            
            # 如果用戶沒有帳戶，創建默認帳戶
            if not accounts:
                account_id = self.db.add_account(user_id, "現金", 0, True)
                accounts = [{"account_id": account_id, "name": "現金", "balance": 0, "is_default": True}]
            
            # 發送帳戶選擇界面
            account_data = {
                "action": "select_account",
                "transaction_type": transaction_type,
                "item": item,
                "amount": amount,
                "date": trans_date
            }
            self._send_account_selection(reply_token, accounts, account_data)
            return
        
        # 如果已經指定了帳戶，但沒有指定分類
        if account and not category:
            # 查找或創建指定的帳戶
            accounts = self.db.get_accounts(user_id)
            account_found = False
            account_id = None
            
            for acc in accounts:
                if acc["name"] == account:
                    account_id = acc["account_id"]
                    account_found = True
                    break
            
            if not account_found:
                account_id = self.db.add_account(user_id, account, 0, False)
                logger.info(f"為用戶 {user_id} 創建新帳戶: {account}")
            
            # 發送分類選擇界面
            if transaction_type == "expense":
                categories = self.expense_categories
            else:
                categories = self.income_categories
                
            # 準備記帳資料
            account_data = {
                "action": "select_category",
                "transaction_type": transaction_type,
                "item": item,
                "amount": amount,
                "account_id": account_id,
                "date": trans_date
            }
            self._send_category_selection(reply_token, categories, account_data)
        
        # 如果已經指定了帳戶和分類，直接記帳
        elif account and category:
            # 查找或創建指定的帳戶
            accounts = self.db.get_accounts(user_id)
            account_found = False
            account_id = None
            
            for acc in accounts:
                if acc["name"] == account:
                    account_id = acc["account_id"]
                    account_found = True
                    break
            
            if not account_found:
                account_id = self.db.add_account(user_id, account, 0, False)
                logger.info(f"為用戶 {user_id} 創建新帳戶: {account}")
            
            # 查找或創建指定的分類
            categories = self.db.get_categories(user_id, transaction_type)
            category_found = False
            category_id = None
            
            for cat in categories:
                if cat["name"] == category:
                    category_id = cat["category_id"]
                    category_found = True
                    break
            
            if not category_found:
                category_id = self.db.add_category(user_id, category, transaction_type)
                logger.info(f"為用戶 {user_id} 創建新分類: {category} (類型: {transaction_type})")
            
            # 新增交易記錄
            transaction_id = self.db.add_transaction(
                user_id, account_id, category_id, 
                transaction_type, amount, item, trans_date
            )
            
            # 回覆確認訊息
            self._send_transaction_confirmation(
                reply_token, transaction_type, item, amount, 
                category, account, trans_date
            )
        
        # 如果只指定了分類，但沒有指定帳戶
        elif category and not account:
            # 使用預設帳戶
            default_account = self.db.get_default_account(user_id)
            if default_account:
                account_id = default_account["account_id"]
                account = default_account["name"]
            else:
                # 如果沒有預設帳戶，創建一個
                account_id = self.db.add_account(user_id, "現金", 0, True)
                account = "現金"
                logger.info(f"為用戶 {user_id} 創建預設現金帳戶")
            
            # 查找或創建指定的分類
            categories = self.db.get_categories(user_id, transaction_type)
            category_found = False
            category_id = None
            
            for cat in categories:
                if cat["name"] == category:
                    category_id = cat["category_id"]
                    category_found = True
                    break
            
            if not category_found:
                category_id = self.db.add_category(user_id, category, transaction_type)
                logger.info(f"為用戶 {user_id} 創建新分類: {category} (類型: {transaction_type})")
            
            # 新增交易記錄
            transaction_id = self.db.add_transaction(
                user_id, account_id, category_id, 
                transaction_type, amount, item, trans_date
            )
            
            # 回覆確認訊息
            self._send_transaction_confirmation(
                reply_token, transaction_type, item, amount, 
                category, account, trans_date
            )
    
    def _handle_reminder(self, user_id, reply_token, data):
        """處理提醒操作"""
        content = data.get("content", "未命名提醒")
        time_str = data.get("time", "09:00")
        date_str = data.get("date", datetime.now().strftime('%Y-%m-%d'))
        remind_before = data.get("remind_before", 15)
        repeat_type = data.get("repeat", "none")
        repeat_value = data.get("repeat_value")
        
        # 格式化日期時間
        due_time = f"{date_str}T{time_str}:00"
        
        # 確保用戶存在於資料庫
        user = self.db.get_user(user_id)
        if not user:
            logger.warning(f"用戶 {user_id} 不存在於資料庫中")
        
        # 新增提醒
        reminder_id = self.db.add_reminder(
            user_id, content, due_time, None, 
            remind_before, repeat_type, repeat_value
        )
        
        # 準備回覆訊息
        due_datetime = datetime.fromisoformat(due_time)
        due_str = due_datetime.strftime("%Y-%m-%d %H:%M")
        
        repeat_text = ""
        if repeat_type == "daily":
            repeat_text = "每天重複"
        elif repeat_type == "weekly":
            day_names = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
            day_idx = int(repeat_value) - 1 if repeat_value else 0
            repeat_text = f"每週{day_names[day_idx]}重複"
        elif repeat_type == "monthly":
            repeat_text = f"每月{repeat_value}日重複"
        
        # 發送提醒確認訊息
        self._send_reminder_confirmation(reply_token, content, due_datetime, remind_before, repeat_text, reminder_id)
    
    def _handle_query(self, user_id, reply_token, query_data):
        """處理查詢請求"""
        try:
            # 取得查詢類型、時間範圍和值
            query_type = query_data.get("query_type", "expense")
            time_range = query_data.get("time_range", "month")
            time_value = query_data.get("time_value", "current")
            category = query_data.get("category")
            account = query_data.get("account")
            
            logger.info(f"處理查詢請求: 類型={query_type}, 時間範圍={time_range}, 時間值={time_value}, 分類={category}, 帳戶={account}")
            
            # 呼叫查詢處理方法
            self.handle_query(reply_token, query_data)
            
        except Exception as e:
            logger.error(f"處理查詢請求時出錯: {str(e)}")
            self.line_bot_api.reply_message(
                reply_token,
                TextMessage(text=f"查詢失敗，請稍後再試。")
            )
    
    def _handle_category_selection(self, user_id, reply_token, data):
        """處理用戶選擇的分類"""
        transaction_type = data.get("transaction_type")
        item = data.get("item", "未指定項目")
        amount = data.get("amount", 0)
        category_name = data.get("category_name")
        account_id = data.get("account_id")
        trans_date = data.get("date", date.today().isoformat())
        
        # 查找或創建分類
        categories = self.db.get_categories(user_id, transaction_type)
        category_found = False
        category_id = None
        
        for cat in categories:
            if cat["name"] == category_name:
                category_id = cat["category_id"]
                category_found = True
                break
        
        if not category_found:
            category_id = self.db.add_category(user_id, category_name, transaction_type)
            logger.info(f"為用戶 {user_id} 創建新分類: {category_name} (類型: {transaction_type})")
        
        # 新增交易記錄
        transaction_id = self.db.add_transaction(
            user_id, account_id, category_id, 
            transaction_type, amount, item, trans_date
        )
        
        # 查找帳戶名稱
        account = "未知帳戶"
        accounts = self.db.get_accounts(user_id)
        for acc in accounts:
            if acc["account_id"] == account_id:
                account = acc["name"]
                break
        
        # 使用 Flex 訊息回覆交易確認
        self._send_transaction_confirmation(
            reply_token, transaction_type, item, amount, 
            category_name, account, trans_date
        )
    
    def _handle_account_selection(self, user_id, reply_token, data):
        """處理用戶選擇的帳戶"""
        transaction_type = data.get("transaction_type")
        item = data.get("item", "未指定項目")
        amount = data.get("amount", 0)
        account_id = data.get("account_id")
        trans_date = data.get("date", date.today().isoformat())
        
        # 如果是添加新帳戶的請求
        if data.get("action") == "add_account":
            # 發送添加帳戶的提示信息
            self._reply_text(reply_token, "請輸入新帳戶名稱，格式：新增帳戶 [帳戶名稱]")
            return
        
        # 發送分類選擇界面
        if transaction_type == "expense":
            categories = self.expense_categories
        else:
            categories = self.income_categories
            
        # 準備記帳資料
        account_data = {
            "action": "select_category",
            "transaction_type": transaction_type,
            "item": item,
            "amount": amount,
            "account_id": account_id,
            "date": trans_date
        }
        
        # 發送分類選擇訊息
        self._send_category_selection(reply_token, categories, account_data)
    
    def _send_account_selection(self, reply_token, accounts, account_data):
        """發送帳戶選擇的 Flex 訊息"""
        bubble = self._create_account_selection_bubble(accounts, account_data)
        flex_message = FlexMessage(alt_text="請選擇帳戶", contents=bubble)
        
        # 發送訊息
        self.line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[flex_message]
            )
        )
    
    def _create_account_selection_bubble(self, accounts, account_data):
        """創建帳戶選擇的 Bubble 容器"""
        # 根據記帳類型設置標題
        if account_data["transaction_type"] == "expense":
            title = f"支出：{account_data['item']} -{account_data['amount']}"
        else:
            title = f"收入：{account_data['item']} +{account_data['amount']}"
        
        # 帳戶圖標映射
        account_icons = {
            "現金": "💵",
            "信用卡": "💳",
            "銀行": "🏦",
            "電子支付": "📱",
            "其他": "💼"
        }
        
        # 創建按鈕
        buttons = []
        for i, account in enumerate(accounts):
            # 取得帳戶圖標
            account_name = account["name"]
            account_icon = next((icon for name, icon in account_icons.items() if name in account_name), "💼")
            
            # 準備 postback 資料
            postback_data = account_data.copy()
            postback_data["action"] = "select_category"  # 下一步選擇分類
            postback_data["account_id"] = account["account_id"]
            
            # 創建按鈕
            button = ButtonComponent(
                style="primary" if account.get("is_default", False) else "secondary",
                height="sm",
                action=PostbackAction(
                    label=f"{account_icon} {account_name}",
                    data=json.dumps(postback_data)
                )
            )
            buttons.append(button)
        
        # 添加"新增帳戶"按鈕
        new_account_data = account_data.copy()
        new_account_data["action"] = "add_account"
        
        new_account_button = ButtonComponent(
            style="link",
            height="sm",
            action=PostbackAction(
                label="➕ 新增帳戶",
                data=json.dumps(new_account_data)
            )
        )
        buttons.append(new_account_button)
        
        # 將按鈕分成兩列
        button_columns = []
        for i in range(0, len(buttons), 2):
            if i + 1 < len(buttons):
                button_columns.append(
                    BoxComponent(
                        layout="horizontal",
                        margin="md",
                        contents=[buttons[i], buttons[i+1]]
                    )
                )
            else:
                button_columns.append(
                    BoxComponent(
                        layout="horizontal",
                        margin="md",
                        contents=[buttons[i]]
                    )
                )
        
        # 創建 Bubble 容器
        bubble = FlexContainer(
            header=BoxComponent(
                layout="vertical",
                contents=[
                    BoxComponent(
                        layout="vertical",
                        contents=[
                            {
                                "type": "text",
                                "text": "請選擇帳戶",
                                "weight": "bold",
                                "size": "xl",
                                "align": "center"
                            },
                            {
                                "type": "text",
                                "text": title,
                                "size": "md",
                                "align": "center",
                                "margin": "md"
                            }
                        ]
                    )
                ]
            ),
            body=BoxComponent(
                layout="vertical",
                contents=button_columns
            )
        )
        
        return bubble
    
    def _send_category_selection(self, reply_token, categories, account_data):
        """發送分類選擇的 Flex 訊息"""
        bubble = self._create_category_selection_bubble(categories, account_data)
        flex_message = FlexMessage(alt_text="請選擇分類", contents=bubble)
        
        # 發送訊息
        self.line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[flex_message]
            )
        )
    
    def _create_category_selection_bubble(self, categories, account_data):
        """創建分類選擇的 Bubble 容器"""
        # 根據記帳類型設置標題
        if account_data["transaction_type"] == "expense":
            title = f"支出：{account_data['item']} -{account_data['amount']}"
        else:
            title = f"收入：{account_data['item']} +{account_data['amount']}"
        
        # 創建按鈕
        buttons = []
        for i, category in enumerate(categories):
            # 準備 postback 資料
            postback_data = account_data.copy()
            postback_data["category_name"] = category["name"]
            
            # 創建按鈕
            button = ButtonComponent(
                style="primary" if i % 2 == 0 else "secondary",
                height="sm",
                action=PostbackAction(
                    label=f"{category['icon']} {category['name']}",
                    data=json.dumps(postback_data)
                )
            )
            buttons.append(button)
        
        # 將按鈕分成兩列
        button_columns = []
        for i in range(0, len(buttons), 2):
            if i + 1 < len(buttons):
                button_columns.append(
                    BoxComponent(
                        layout="horizontal",
                        margin="md",
                        contents=[buttons[i], buttons[i+1]]
                    )
                )
            else:
                button_columns.append(
                    BoxComponent(
                        layout="horizontal",
                        margin="md",
                        contents=[buttons[i]]
                    )
                )
        
        # 創建 Bubble 容器
        bubble = FlexContainer(
            header=BoxComponent(
                layout="vertical",
                contents=[
                    BoxComponent(
                        layout="vertical",
                        contents=[
                            {
                                "type": "text",
                                "text": "請選擇分類",
                                "weight": "bold",
                                "size": "xl",
                                "align": "center"
                            },
                            {
                                "type": "text",
                                "text": title,
                                "size": "md",
                                "align": "center",
                                "margin": "md"
                            }
                        ]
                    )
                ]
            ),
            body=BoxComponent(
                layout="vertical",
                contents=button_columns
            )
        )
        
        return bubble
    
    def _send_transaction_confirmation(self, reply_token, transaction_type, item, amount, category, account, trans_date):
        """發送交易確認的 Flex 訊息"""
        bubble = self._create_transaction_confirmation_bubble(
            transaction_type, item, amount, category, account, trans_date
        )
        flex_message = FlexMessage(alt_text="交易已記錄", contents=bubble)
        
        # 發送訊息
        self.line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[flex_message]
            )
        )
    
    def _create_transaction_confirmation_bubble(self, transaction_type, item, amount, category, account, trans_date):
        """創建交易確認的 Bubble 容器"""
        # 設置顏色和圖標
        color = self.colors["income"] if transaction_type == "income" else self.colors["expense"]
        icon = "💰" if transaction_type == "income" else "💸"
        sign = "+" if transaction_type == "income" else "-"
        
        # 格式化日期
        try:
            date_obj = date.fromisoformat(trans_date)
            formatted_date = date_obj.strftime("%Y年%m月%d日")
        except:
            formatted_date = trans_date
        
        # 創建 Bubble 容器
        bubble = {
            "type": "bubble",
            "size": "kilo",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "text",
                                "text": "交易記錄成功",
                                "color": "#FFFFFF",
                                "weight": "bold",
                                "size": "xl"
                            },
                            {
                                "type": "text",
                                "text": icon,
                                "size": "xxl",
                                "align": "end"
                            }
                        ]
                    }
                ],
                "paddingBottom": "md",
                "backgroundColor": color
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": item,
                                "weight": "bold",
                                "size": "lg",
                                "wrap": True
                            },
                            {
                                "type": "text",
                                "text": f"{sign}{amount}",
                                "size": "xxl",
                                "color": color,
                                "weight": "bold",
                                "margin": "md"
                            }
                        ]
                    },
                    {
                        "type": "separator",
                        "margin": "lg"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "分類",
                                        "size": "sm",
                                        "color": "#555555"
                                    },
                                    {
                                        "type": "text",
                                        "text": category,
                                        "size": "sm",
                                        "align": "end"
                                    }
                                ],
                                "margin": "md"
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "帳戶",
                                        "size": "sm",
                                        "color": "#555555"
                                    },
                                    {
                                        "type": "text",
                                        "text": account,
                                        "size": "sm",
                                        "align": "end"
                                    }
                                ],
                                "margin": "md"
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "日期",
                                        "size": "sm",
                                        "color": "#555555"
                                    },
                                    {
                                        "type": "text",
                                        "text": formatted_date,
                                        "size": "sm",
                                        "align": "end"
                                    }
                                ],
                                "margin": "md"
                            }
                        ],
                        "margin": "lg"
                    }
                ],
                "paddingAll": "lg"
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "uri",
                            "label": "查看詳細記錄",
                            "uri": "https://liff.line.me/YOUR_LIFF_ID"
                        },
                        "style": "primary",
                        "color": color
                    }
                ],
                "paddingTop": "sm"
            },
            "styles": {
                "body": {
                    "separator": True
                }
            }
        }
        
        return bubble
    
    def _send_reminder_confirmation(self, reply_token, content, due_datetime, remind_before, repeat_text, reminder_id):
        """發送提醒確認的 Flex 訊息"""
        bubble = self._create_reminder_confirmation_bubble(content, due_datetime, remind_before, repeat_text, reminder_id)
        flex_message = FlexMessage(alt_text="提醒已設置", contents=bubble)
        
        # 發送訊息
        self.line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[flex_message]
            )
        )
    
    def _create_reminder_confirmation_bubble(self, content, due_datetime, remind_before, repeat_text, reminder_id):
        """創建提醒確認的 Bubble 容器"""
        # 格式化日期和時間
        due_date = due_datetime.strftime("%Y年%m月%d日")
        due_time = due_datetime.strftime("%H:%M")
        
        # 獲取星期幾
        weekday_names = ["一", "二", "三", "四", "五", "六", "日"]
        weekday = weekday_names[due_datetime.weekday()]
        
        # 計算與當前時間的差距
        now = datetime.now()
        delta = due_datetime - now
        days_diff = delta.days
        hours_diff = delta.seconds // 3600
        minutes_diff = (delta.seconds % 3600) // 60
        
        # 構建時間差文本
        time_diff_text = ""
        if days_diff > 0:
            time_diff_text = f"{days_diff}天"
            if hours_diff > 0:
                time_diff_text += f"{hours_diff}小時後"
        elif hours_diff > 0:
            time_diff_text = f"{hours_diff}小時"
            if minutes_diff > 0:
                time_diff_text += f"{minutes_diff}分鐘後"
        else:
            time_diff_text = f"{minutes_diff}分鐘後" if minutes_diff > 0 else "馬上"
        
        # 創建 Bubble 容器
        bubble = {
            "type": "bubble",
            "size": "kilo",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "text",
                                "text": "提醒已設置",
                                "color": "#FFFFFF",
                                "weight": "bold",
                                "size": "xl"
                            },
                            {
                                "type": "text",
                                "text": "⏰",
                                "size": "xxl",
                                "align": "end"
                            }
                        ]
                    }
                ],
                "paddingBottom": "md",
                "backgroundColor": self.colors["primary"]
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": content,
                                "weight": "bold",
                                "size": "lg",
                                "wrap": True
                            },
                            {
                                "type": "text",
                                "text": f"將在{time_diff_text}提醒您",
                                "size": "md",
                                "color": self.colors["warning"],
                                "margin": "md"
                            }
                        ]
                    },
                    {
                        "type": "separator",
                        "margin": "lg"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "日期",
                                        "size": "sm",
                                        "color": "#555555"
                                    },
                                    {
                                        "type": "text",
                                        "text": f"{due_date} (星期{weekday})",
                                        "size": "sm",
                                        "align": "end"
                                    }
                                ],
                                "margin": "md"
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "時間",
                                        "size": "sm",
                                        "color": "#555555"
                                    },
                                    {
                                        "type": "text",
                                        "text": due_time,
                                        "size": "sm",
                                        "align": "end"
                                    }
                                ],
                                "margin": "md"
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "提前提醒",
                                        "size": "sm",
                                        "color": "#555555"
                                    },
                                    {
                                        "type": "text",
                                        "text": f"{remind_before} 分鐘",
                                        "size": "sm",
                                        "align": "end"
                                    }
                                ],
                                "margin": "md"
                            }
                        ],
                        "margin": "lg"
                    }
                ],
                "paddingAll": "lg"
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": repeat_text,
                        "align": "center",
                        "size": "sm",
                        "color": "#888888",
                        "margin": "md"
                    }
                ],
                "paddingTop": "sm"
            },
            "styles": {
                "body": {
                    "separator": True
                }
            }
        }
        
        # 只有當有重複文字時才顯示
        if not repeat_text:
            bubble["footer"]["contents"] = []
        
        return bubble
    
    def _send_reminder_list(self, reply_token, reminders, time_range=None, time_value=None):
        """發送提醒列表"""
        if not reminders:
            self.line_bot_api.reply_message(
                reply_token,
                TextMessage(text="該時間段內沒有未完成的提醒事項。")
            )
            return
        
        # 構建標題
        title = ""
        if time_range and time_value:
            title = self._get_time_range_description(time_range, time_value)
        title += "提醒事項列表"
        
        # 創建提醒卡片
        bubbles = []
        for reminder in reminders:
            # 取得提醒時間和內容
            remind_time = datetime.strptime(reminder["remind_time"], "%Y-%m-%d %H:%M:%S")
            content = reminder["content"]
            reminder_id = reminder["reminder_id"]
            
            # 創建 Bubble 容器
            bubble = FlexContainer(
                header=BoxComponent(
                    layout="vertical",
                    contents=[
                        TextComponent(
                            text="提醒事項",
                            weight="bold",
                            size="lg",
                            align="center",
                            color="#ffffff"
                        )
                    ],
                    backgroundColor="#6699CC"
                ),
                body=BoxComponent(
                    layout="vertical",
                    contents=[
                        # 提醒時間
                        BoxComponent(
                            layout="vertical",
                            margin="md",
                            contents=[
                                TextComponent(
                                    text="提醒時間",
                                    weight="bold",
                                    size="sm",
                                    color="#888888"
                                ),
                                TextComponent(
                                    text=remind_time.strftime("%Y年%m月%d日 %H:%M"),
                                    size="md",
                                    margin="sm"
                                )
                            ]
                        ),
                        # 提醒內容
                        BoxComponent(
                            layout="vertical",
                            margin="xl",
                            contents=[
                                TextComponent(
                                    text="提醒內容",
                                    weight="bold",
                                    size="sm",
                                    color="#888888"
                                ),
                                TextComponent(
                                    text=content,
                                    wrap=True,
                                    size="md",
                                    margin="sm"
                                )
                            ]
                        )
                    ]
                ),
                footer=BoxComponent(
                    layout="horizontal",
                    spacing="md",
                    contents=[
                        ButtonComponent(
                            style="primary",
                            action=PostbackAction(
                                label="完成",
                                data=json.dumps({
                                    "action": "complete_reminder",
                                    "reminder_id": reminder_id
                                })
                            ),
                            color="#6699CC"
                        ),
                        ButtonComponent(
                            style="secondary",
                            action=PostbackAction(
                                label="刪除",
                                data=json.dumps({
                                    "action": "delete_reminder",
                                    "reminder_id": reminder_id
                                })
                            )
                        )
                    ]
                )
            )
            
            bubbles.append(bubble)
        
        # 創建 Carousel 容器
        carousel = FlexContainer(contents=bubbles)
        
        # 發送 Flex Message
        flex_message = FlexMessage(alt_text=title, contents=carousel)
        self.line_bot_api.reply_message(reply_token, flex_message)
    
    def _handle_complete_reminder(self, user_id, reply_token, data):
        """處理完成提醒的請求"""
        reminder_id = data.get("reminder_id")
        
        if not reminder_id:
            self._reply_text(reply_token, "無法找到該提醒。")
            return
        
        try:
            # 標記提醒為已完成
            self.db.update_reminder_status(reminder_id, True)
            
            # 回覆確認訊息
            self._reply_text(reply_token, "✅ 提醒已標記為完成。")
            
        except Exception as e:
            logger.error(f"完成提醒時發生錯誤: {str(e)}")
            self._reply_text(reply_token, "處理提醒時發生錯誤，請稍後再試。")
    
    def _handle_delete_reminder(self, user_id, reply_token, data):
        """處理刪除提醒的請求"""
        reminder_id = data.get("reminder_id")
        
        if not reminder_id:
            self._reply_text(reply_token, "無法找到該提醒。")
            return
        
        try:
            # 獲取提醒標題用於回覆
            reminder = self.db.get_reminder(reminder_id)
            title = reminder["title"] if reminder else "該提醒"
            
            # 刪除提醒
            self.db.delete_reminder(reminder_id)
            
            # 回覆確認訊息
            self._reply_text(reply_token, f"🗑️ 提醒「{title}」已刪除。")
            
        except Exception as e:
            logger.error(f"刪除提醒時發生錯誤: {str(e)}")
            self._reply_text(reply_token, "處理提醒時發生錯誤，請稍後再試。")
    
    def _reply_text(self, reply_token, text):
        """回覆文字訊息"""
        self.line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text=text)]
            )
        )

    def _handle_account_command(self, user_id, reply_token, data):
        """處理帳戶相關命令"""
        action = data.get("action")
        
        if action == "add_account":
            account_name = data.get("account_name")
            
            # 檢查該帳戶是否已存在
            accounts = self.db.get_accounts(user_id)
            for account in accounts:
                if account["name"] == account_name:
                    self._reply_text(reply_token, f"帳戶「{account_name}」已存在。")
                    return
            
            # 新增帳戶
            account_id = self.db.add_account(user_id, account_name, 0, False)
            logger.info(f"為用戶 {user_id} 創建新帳戶: {account_name}")
            
            # 回覆確認訊息
            self._reply_text(reply_token, f"已成功新增帳戶「{account_name}」。您可以使用「<{account_name}> 交易記錄」的格式來指定使用此帳戶。")

    def create_quick_menu(self):
        """創建並註冊快速選單"""
        try:
            # 定義記帳快速選單
            rich_menu_to_create = RichMenuRequest(
                size=RichMenuSize(width=2500, height=843),
                selected=True,
                name="記帳與提醒快速選單",
                chat_bar_text="點擊開啟功能選單",
                areas=[
                    # 支出記帳按鈕
                    RichMenuArea(
                        bounds=RichMenuBounds(x=0, y=0, width=833, height=422),
                        action=PostbackAction(
                            label='支出記帳',
                            data=json.dumps({
                                "action": "quick_expense"
                            })
                        )
                    ),
                    # 收入記帳按鈕
                    RichMenuArea(
                        bounds=RichMenuBounds(x=833, y=0, width=833, height=422),
                        action=PostbackAction(
                            label='收入記帳',
                            data=json.dumps({
                                "action": "quick_income"
                            })
                        )
                    ),
                    # 設置提醒按鈕
                    RichMenuArea(
                        bounds=RichMenuBounds(x=1666, y=0, width=834, height=422),
                        action=PostbackAction(
                            label='設置提醒',
                            data=json.dumps({
                                "action": "quick_reminder"
                            })
                        )
                    ),
                    # 常用帳戶按鈕
                    RichMenuArea(
                        bounds=RichMenuBounds(x=0, y=422, width=833, height=421),
                        action=PostbackAction(
                            label='常用帳戶',
                            data=json.dumps({
                                "action": "quick_accounts"
                            })
                        )
                    ),
                    # 查詢記錄按鈕
                    RichMenuArea(
                        bounds=RichMenuBounds(x=833, y=422, width=833, height=421),
                        action=PostbackAction(
                            label='查詢記錄',
                            data=json.dumps({
                                "action": "quick_query"
                            })
                        )
                    ),
                    # 更多功能按鈕
                    RichMenuArea(
                        bounds=RichMenuBounds(x=1666, y=422, width=834, height=421),
                        action=URIAction(
                            label='更多功能',
                            uri='https://liff.line.me/YOUR_LIFF_ID'
                        )
                    )
                ]
            )
            
            # 創建 Rich Menu
            rich_menu_id = self.line_bot_api.create_rich_menu(rich_menu_to_create)
            logger.info(f"成功創建Rich Menu: {rich_menu_id}")
            
            # 上傳 Rich Menu 的圖片
            with open("static/assets/rich_menu.png", 'rb') as f:
                self.line_bot_api.set_rich_menu_image(rich_menu_id, "image/png", f)
            logger.info("成功上傳Rich Menu圖片")
            
            # 設定為預設選單
            self.line_bot_api.set_default_rich_menu(rich_menu_id)
            logger.info("已將Rich Menu設為預設選單")
            
            return rich_menu_id
            
        except Exception as e:
            logger.error(f"創建快速選單時發生錯誤: {str(e)}")
            return None

    def handle_quick_menu_action(self, user_id, reply_token, data):
        """處理快速選單按鈕點擊"""
        action = data.get("action")
        
        if action == "quick_expense":
            # 顯示支出分類選單
            self._send_quick_category_selection(reply_token, "expense")
        
        elif action == "quick_income":
            # 顯示收入分類選單
            self._send_quick_category_selection(reply_token, "income")
        
        elif action == "quick_reminder":
            # 顯示建立提醒的引導
            self._reply_text(
                reply_token, 
                "請輸入提醒內容，例如：\n「提醒我明天早上8點去健身」\n「每週一下午3點提醒我開會」"
            )
        
        elif action == "quick_accounts":
            # 顯示帳戶快速選單
            self._send_quick_account_selection(user_id, reply_token)
        
        elif action == "quick_query":
            # 顯示查詢選項
            self._send_quick_query_options(reply_token)
    
    def _send_quick_category_selection(self, reply_token, transaction_type):
        """發送快速分類選擇介面"""
        if transaction_type == "expense":
            categories = self.expense_categories
            title = "選擇支出分類"
            color = self.colors["expense"]
        else:
            categories = self.income_categories
            title = "選擇收入分類"
            color = self.colors["income"]
        
        # 創建選擇按鈕
        buttons = []
        for category in categories:
            buttons.append(
                ButtonComponent(
                    style="primary",
                    color=color,
                    height="sm",
                    action=PostbackAction(
                        label=f"{category['icon']} {category['name']}",
                        data=json.dumps({
                            "action": "quick_category_selected",
                            "category": category['name'],
                            "transaction_type": transaction_type
                        })
                    )
                )
            )
        
        # 將按鈕分成兩列
        button_columns = []
        for i in range(0, len(buttons), 2):
            if i + 1 < len(buttons):
                button_columns.append(
                    BoxComponent(
                        layout="horizontal",
                        margin="md",
                        contents=[buttons[i], buttons[i+1]]
                    )
                )
            else:
                button_columns.append(
                    BoxComponent(
                        layout="horizontal",
                        margin="md",
                        contents=[buttons[i]]
                    )
                )
        
        # 創建 Bubble 容器
        bubble = FlexContainer(
            header=BoxComponent(
                layout="vertical",
                contents=[
                    TextComponent(
                        text=title,
                        weight="bold",
                        size="xl",
                        align="center"
                    )
                ],
                backgroundColor=color
            ),
            body=BoxComponent(
                layout="vertical",
                contents=button_columns
            )
        )
        
        # 發送 Flex 訊息
        flex_message = FlexMessage(alt_text=title, contents=bubble)
        self.line_bot_api.reply_message(reply_token, flex_message)
    
    def _send_quick_account_selection(self, user_id, reply_token):
        """發送快速帳戶選擇介面"""
        # 獲取用戶的所有帳戶
        accounts = self.db.get_accounts(user_id)
        
        # 如果用戶沒有帳戶，創建默認帳戶
        if not accounts:
            account_id = self.db.add_account(user_id, "現金", 0, True)
            accounts = [{"account_id": account_id, "name": "現金", "balance": 0, "is_default": True}]
        
        # 創建選擇按鈕
        buttons = []
        for account in accounts:
            # 決定帳戶圖標
            icon = "💵"  # 默認圖標
            if "信用卡" in account["name"]:
                icon = "💳"
            elif "銀行" in account["name"]:
                icon = "🏦"
            elif "電子" in account["name"] or "支付" in account["name"]:
                icon = "📱"
            
            buttons.append(
                ButtonComponent(
                    style="primary" if account.get("is_default") else "secondary",
                    height="sm",
                    action=PostbackAction(
                        label=f"{icon} {account['name']} (餘額: {account['balance']})",
                        data=json.dumps({
                            "action": "quick_account_selected",
                            "account_id": account['account_id'],
                            "account_name": account['name']
                        })
                    )
                )
            )
        
        # 添加"新增帳戶"按鈕
        buttons.append(
            ButtonComponent(
                style="link",
                height="sm",
                action=PostbackAction(
                    label="➕ 新增帳戶",
                    data=json.dumps({
                        "action": "add_account"
                    })
                )
            )
        )
        
        # 將按鈕分成一列一個
        button_columns = []
        for button in buttons:
            button_columns.append(
                BoxComponent(
                    layout="horizontal",
                    margin="md",
                    contents=[button]
                )
            )
        
        # 創建 Bubble 容器
        bubble = FlexContainer(
            header=BoxComponent(
                layout="vertical",
                contents=[
                    TextComponent(
                        text="選擇帳戶",
                        weight="bold",
                        size="xl",
                        align="center"
                    )
                ],
                backgroundColor=self.colors["primary"]
            ),
            body=BoxComponent(
                layout="vertical",
                contents=button_columns
            )
        )
        
        # 發送 Flex 訊息
        flex_message = FlexMessage(alt_text="選擇帳戶", contents=bubble)
        self.line_bot_api.reply_message(reply_token, flex_message)
    
    def _send_quick_query_options(self, reply_token):
        """發送快速查詢選項"""
        # 創建查詢按鈕
        buttons = [
            # 本日支出
            ButtonComponent(
                style="primary",
                color=self.colors["expense"],
                height="sm",
                action=PostbackAction(
                    label="📊 今日支出",
                    data=json.dumps({
                        "action": "quick_query_selected",
                        "query_type": "expense",
                        "time_range": "day",
                        "time_value": "current"
                    })
                )
            ),
            # 本週支出
            ButtonComponent(
                style="primary",
                color=self.colors["expense"],
                height="sm",
                action=PostbackAction(
                    label="📊 本週支出",
                    data=json.dumps({
                        "action": "quick_query_selected",
                        "query_type": "expense",
                        "time_range": "week",
                        "time_value": "current"
                    })
                )
            ),
            # 本月支出
            ButtonComponent(
                style="primary",
                color=self.colors["expense"],
                height="sm",
                action=PostbackAction(
                    label="📊 本月支出",
                    data=json.dumps({
                        "action": "quick_query_selected",
                        "query_type": "expense",
                        "time_range": "month",
                        "time_value": "current"
                    })
                )
            ),
            # 本月收入
            ButtonComponent(
                style="primary",
                color=self.colors["income"],
                height="sm",
                action=PostbackAction(
                    label="📈 本月收入",
                    data=json.dumps({
                        "action": "quick_query_selected",
                        "query_type": "income",
                        "time_range": "month",
                        "time_value": "current"
                    })
                )
            ),
            # 查看提醒
            ButtonComponent(
                style="primary",
                color=self.colors["info"],
                height="sm",
                action=PostbackAction(
                    label="🔔 查看提醒",
                    data=json.dumps({
                        "action": "quick_query_selected",
                        "query_type": "reminder"
                    })
                )
            )
        ]
        
        # 將按鈕分成一列一個
        button_columns = []
        for button in buttons:
            button_columns.append(
                BoxComponent(
                    layout="horizontal",
                    margin="md",
                    contents=[button]
                )
            )
        
        # 創建 Bubble 容器
        bubble = FlexContainer(
            header=BoxComponent(
                layout="vertical",
                contents=[
                    TextComponent(
                        text="選擇查詢",
                        weight="bold",
                        size="xl",
                        align="center"
                    )
                ],
                backgroundColor=self.colors["primary"]
            ),
            body=BoxComponent(
                layout="vertical",
                contents=button_columns
            )
        )
        
        # 發送 Flex 訊息
        flex_message = FlexMessage(alt_text="選擇查詢", contents=bubble)
        self.line_bot_api.reply_message(reply_token, flex_message)
    
    def _handle_quick_category_selected(self, user_id, reply_token, data):
        """處理快速分類選擇"""
        category = data.get("category")
        transaction_type = data.get("transaction_type")
        
        # 提示用戶輸入金額和項目名稱
        self._reply_text(
            reply_token, 
            f"請輸入{category}的{transaction_type}金額和項目名稱，例如：\n"
            f"「{category} 100 午餐」\n"
            f"或直接輸入：\n"
            f"「午餐 {100 if transaction_type == 'expense' else '+100'}」"
        )
    
    def _handle_quick_account_selected(self, user_id, reply_token, data):
        """處理快速帳戶選擇"""
        account_id = data.get("account_id")
        account_name = data.get("account_name")
        
        # 獲取帳戶信息
        accounts = self.db.get_accounts(user_id)
        account = None
        for acc in accounts:
            if acc["account_id"] == account_id:
                account = acc
                break
        
        if not account:
            self._reply_text(reply_token, "找不到指定帳戶，請重試。")
            return
        
        # 顯示帳戶詳情
        response_text = (
            f"帳戶：{account_name}\n"
            f"目前餘額：{account['balance']} 元\n\n"
            f"記帳時可以使用「{account_name}」指定此帳戶，例如：\n"
            f"「{account_name} 午餐 -100」"
        )
        
        self._reply_text(reply_token, response_text)
    
    def _handle_quick_query_selected(self, user_id, reply_token, data):
        """處理快速查詢選擇"""
        query_type = data.get("query_type")
        time_range = data.get("time_range")
        time_value = data.get("time_value")
        
        # 構建查詢數據
        query_data = {
            "query_type": query_type,
        }
        
        # 如果是日期相關查詢，計算日期範圍
        if time_range and time_value:
            today = date.today()
            
            if time_range == "day":
                if time_value == "current":
                    # 今天
                    query_data["start_date"] = today.isoformat()
                    query_data["end_date"] = today.isoformat()
                elif time_value == "previous":
                    # 昨天
                    yesterday = today - timedelta(days=1)
                    query_data["start_date"] = yesterday.isoformat()
                    query_data["end_date"] = yesterday.isoformat()
            
            elif time_range == "week":
                # 計算本週的開始日期（星期一）和結束日期（星期日）
                weekday = today.weekday()  # 0 是星期一，6 是星期日
                
                if time_value == "current":
                    # 本週
                    week_start = today - timedelta(days=weekday)
                    week_end = week_start + timedelta(days=6)
                    query_data["start_date"] = week_start.isoformat()
                    query_data["end_date"] = week_end.isoformat()
                elif time_value == "previous":
                    # 上週
                    week_start = today - timedelta(days=weekday + 7)
                    week_end = week_start + timedelta(days=6)
                    query_data["start_date"] = week_start.isoformat()
                    query_data["end_date"] = week_end.isoformat()
            
            elif time_range == "month":
                if time_value == "current":
                    # 本月
                    month_start = date(today.year, today.month, 1)
                    # 計算月末
                    if today.month == 12:
                        next_month = date(today.year + 1, 1, 1)
                    else:
                        next_month = date(today.year, today.month + 1, 1)
                    month_end = next_month - timedelta(days=1)
                    query_data["start_date"] = month_start.isoformat()
                    query_data["end_date"] = month_end.isoformat()
                elif time_value == "previous":
                    # 上月
                    if today.month == 1:
                        month_start = date(today.year - 1, 12, 1)
                        month_end = date(today.year, 1, 1) - timedelta(days=1)
                    else:
                        month_start = date(today.year, today.month - 1, 1)
                        month_end = date(today.year, today.month, 1) - timedelta(days=1)
                    query_data["start_date"] = month_start.isoformat()
                    query_data["end_date"] = month_end.isoformat()
        
        # 處理查詢
        self._handle_query(user_id, reply_token, query_data)

    def handle_query(self, reply_token, query_data):
        """處理查詢請求，回傳相應的報表或統計資訊"""
        try:
            query_type = query_data.get("query_type", "expense")
            time_range = query_data.get("time_range", "month")
            time_value = query_data.get("time_value", "current")
            category = query_data.get("category")
            account = query_data.get("account")
            
            # 根據時間範圍計算查詢的起止日期
            start_date, end_date = self._calculate_query_date_range(time_range, time_value)
            
            if query_type == "expense":
                # 查詢支出
                results = self._query_transactions("expense", start_date, end_date, category, account)
                self._send_expense_report(reply_token, results, time_range, time_value, category, account)
            
            elif query_type == "income":
                # 查詢收入
                results = self._query_transactions("income", start_date, end_date, category, account)
                self._send_income_report(reply_token, results, time_range, time_value, category, account)
            
            elif query_type == "reminder":
                # 查詢提醒
                results = self._query_reminders(start_date, end_date)
                self._send_reminder_list(reply_token, results, time_range, time_value)
            
            elif query_type == "balance":
                # 查詢餘額
                expense_results = self._query_transactions("expense", start_date, end_date, category, account)
                income_results = self._query_transactions("income", start_date, end_date, category, account)
                self._send_balance_report(reply_token, expense_results, income_results, time_range, time_value, account)
            
            elif query_type == "overview":
                # 查詢總覽
                expense_results = self._query_transactions("expense", start_date, end_date, category, account)
                income_results = self._query_transactions("income", start_date, end_date, category, account)
                self._send_overview_report(reply_token, expense_results, income_results, time_range, time_value)
            
            else:
                # 未知查詢類型
                self.line_bot_api.reply_message(
                    reply_token,
                    TextMessage(text="抱歉，暫不支持該類型的查詢。請嘗試查詢支出、收入或提醒。")
                )
        
        except Exception as e:
            logger.error(f"處理查詢請求時出錯: {str(e)}")
            self.line_bot_api.reply_message(
                reply_token,
                TextMessage(text=f"查詢失敗，請稍後再試。錯誤信息: {str(e)}")
            )
    
    def _calculate_query_date_range(self, time_range, time_value):
        """根據時間範圍和值計算查詢的起止日期"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        if time_range == "day":
            if time_value == "current":
                # 今天
                start_date = today
                end_date = today.replace(hour=23, minute=59, second=59)
            elif time_value == "previous":
                # 昨天
                start_date = today - timedelta(days=1)
                end_date = start_date.replace(hour=23, minute=59, second=59)
            else:
                # 特定日期
                try:
                    specific_date = datetime.strptime(time_value, "%Y-%m-%d")
                    start_date = specific_date
                    end_date = specific_date.replace(hour=23, minute=59, second=59)
                except ValueError:
                    # 如果日期格式錯誤，使用今天
                    start_date = today
                    end_date = today.replace(hour=23, minute=59, second=59)
        
        elif time_range == "week":
            # 計算本週的星期一和星期日
            weekday = today.weekday()
            if time_value == "current":
                # 本週
                start_date = today - timedelta(days=weekday)
                end_date = start_date + timedelta(days=6, hours=23, minutes=59, seconds=59)
            elif time_value == "previous":
                # 上週
                start_date = today - timedelta(days=weekday + 7)
                end_date = start_date + timedelta(days=6, hours=23, minutes=59, seconds=59)
            else:
                # 特定週
                # 暫不支援，使用本週
                start_date = today - timedelta(days=weekday)
                end_date = start_date + timedelta(days=6, hours=23, minutes=59, seconds=59)
        
        elif time_range == "month":
            if time_value == "current":
                # 本月
                start_date = today.replace(day=1)
                # 計算月末
                if today.month == 12:
                    end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
                end_date = end_date.replace(hour=23, minute=59, second=59)
            elif time_value == "previous":
                # 上月
                if today.month == 1:
                    start_date = today.replace(year=today.year - 1, month=12, day=1)
                else:
                    start_date = today.replace(month=today.month - 1, day=1)
                end_date = today.replace(day=1) - timedelta(days=1)
                end_date = end_date.replace(hour=23, minute=59, second=59)
            else:
                # 特定月
                try:
                    year, month = map(int, time_value.split("-"))
                    start_date = datetime(year, month, 1)
                    if month == 12:
                        end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
                    else:
                        end_date = datetime(year, month + 1, 1) - timedelta(days=1)
                    end_date = end_date.replace(hour=23, minute=59, second=59)
                except ValueError:
                    # 如果日期格式錯誤，使用本月
                    start_date = today.replace(day=1)
                    if today.month == 12:
                        end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
                    else:
                        end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
                    end_date = end_date.replace(hour=23, minute=59, second=59)
        
        elif time_range == "year":
            if time_value == "current":
                # 今年
                start_date = today.replace(month=1, day=1)
                end_date = today.replace(month=12, day=31, hour=23, minute=59, second=59)
            elif time_value == "previous":
                # 去年
                start_date = today.replace(year=today.year - 1, month=1, day=1)
                end_date = today.replace(year=today.year - 1, month=12, day=31, hour=23, minute=59, second=59)
            else:
                # 特定年 - 暫不支援
                start_date = today.replace(month=1, day=1)
                end_date = today.replace(month=12, day=31, hour=23, minute=59, second=59)
        
        else:
            # 默認使用本月
            start_date = today.replace(day=1)
            if today.month == 12:
                end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
            end_date = end_date.replace(hour=23, minute=59, second=59)
        
        return start_date, end_date
    
    def _query_transactions(self, transaction_type, start_date, end_date, category=None, account=None):
        """查詢交易記錄"""
        # 轉換日期格式
        start_date_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
        end_date_str = end_date.strftime("%Y-%m-%d %H:%M:%S")
        
        # 準備查詢條件
        conditions = [
            f"type = '{transaction_type}'",
            f"date BETWEEN '{start_date_str}' AND '{end_date_str}'"
        ]
        
        if category:
            conditions.append(f"category LIKE '%{category}%'")
        
        if account:
            conditions.append(f"account LIKE '%{account}%'")
        
        # 構建 SQL 查詢
        where_clause = " AND ".join(conditions)
        
        # 從資料庫查詢
        results = self.db_utils.execute_query(
            f"SELECT * FROM transactions WHERE {where_clause} ORDER BY date DESC"
        )
        
        return results
    
    def _query_reminders(self, start_date, end_date):
        """查詢提醒事項"""
        # 轉換日期格式
        start_date_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
        end_date_str = end_date.strftime("%Y-%m-%d %H:%M:%S")
        
        # 從資料庫查詢
        results = self.db_utils.execute_query(
            f"SELECT * FROM reminders WHERE remind_time BETWEEN '{start_date_str}' AND '{end_date_str}' AND completed = 0 ORDER BY remind_time ASC"
        )
        
        return results
    
    def _send_expense_report(self, reply_token, results, time_range, time_value, category=None, account=None):
        """發送支出報表"""
        if not results:
            self.line_bot_api.reply_message(
                reply_token,
                TextMessage(text="該時間段內沒有支出記錄。")
            )
            return
        
        # 計算總支出
        total_amount = sum(float(record['amount']) for record in results)
        
        # 按分類統計支出
        category_stats = {}
        for record in results:
            cat = record['category']
            if cat not in category_stats:
                category_stats[cat] = 0
            category_stats[cat] += float(record['amount'])
        
        # 構建標題
        title = self._get_time_range_description(time_range, time_value)
        if category:
            title += f"「{category}」類別"
        if account:
            title += f"「{account}」帳戶"
        title += "支出統計"
        
        # 構建 Flex Message 內容
        bubble = FlexContainer(
            header=BoxComponent(
                layout="vertical",
                contents=[
                    TextComponent(
                        text=title,
                        weight="bold",
                        size="xl",
                        align="center"
                    )
                ]
            ),
            body=BoxComponent(
                layout="vertical",
                contents=[
                    # 總支出
                    BoxComponent(
                        layout="horizontal",
                        margin="md",
                        contents=[
                            TextComponent(
                                text="總支出",
                                size="md",
                                color="#555555",
                                flex=1
                            ),
                            TextComponent(
                                text=f"${total_amount:.2f}",
                                size="md",
                                color="#ff0000",
                                weight="bold",
                                align="end",
                                flex=1
                            )
                        ]
                    ),
                    # 分隔線
                    SeparatorComponent(
                        margin="xl"
                    ),
                    # 分類統計標題
                    TextComponent(
                        text="分類統計",
                        weight="bold",
                        size="md",
                        margin="xl"
                    )
                ]
            )
        )
        
        # 添加分類統計數據
        for cat, amount in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
            percentage = (amount / total_amount) * 100
            
            # 根據分類取得對應圖標
            icon = self.expense_categories.get(cat, "🔹")
            
            # 添加分類條目
            bubble.body.contents.append(
                BoxComponent(
                    layout="horizontal",
                    margin="md",
                    contents=[
                        TextComponent(
                            text=f"{icon} {cat}",
                            size="sm",
                            color="#555555",
                            flex=2
                        ),
                        TextComponent(
                            text=f"${amount:.2f}",
                            size="sm",
                            align="end",
                            flex=1
                        ),
                        TextComponent(
                            text=f"{percentage:.1f}%",
                            size="xs",
                            color="#888888",
                            align="end",
                            flex=1
                        )
                    ]
                )
            )
        
        # 添加查看明細按鈕
        bubble.footer = BoxComponent(
            layout="vertical",
            contents=[
                ButtonComponent(
                    style="primary",
                    action=PostbackAction(
                        label="查看明細",
                        data=json.dumps({
                            "action": "view_details",
                            "type": "expense",
                            "time_range": time_range,
                            "time_value": time_value,
                            "category": category,
                            "account": account
                        })
                    )
                )
            ]
        )
        
        # 發送 Flex Message
        flex_message = FlexMessage(alt_text=title, contents=bubble)
        self.line_bot_api.reply_message(reply_token, flex_message)
    
    def _send_income_report(self, reply_token, results, time_range, time_value, category=None, account=None):
        """發送收入報表"""
        if not results:
            self.line_bot_api.reply_message(
                reply_token,
                TextMessage(text="該時間段內沒有收入記錄。")
            )
            return
        
        # 計算總收入
        total_amount = sum(float(record['amount']) for record in results)
        
        # 按分類統計收入
        category_stats = {}
        for record in results:
            cat = record['category']
            if cat not in category_stats:
                category_stats[cat] = 0
            category_stats[cat] += float(record['amount'])
        
        # 構建標題
        title = self._get_time_range_description(time_range, time_value)
        if category:
            title += f"「{category}」類別"
        if account:
            title += f"「{account}」帳戶"
        title += "收入統計"
        
        # 構建 Flex Message 內容
        bubble = FlexContainer(
            header=BoxComponent(
                layout="vertical",
                contents=[
                    TextComponent(
                        text=title,
                        weight="bold",
                        size="xl",
                        align="center"
                    )
                ]
            ),
            body=BoxComponent(
                layout="vertical",
                contents=[
                    # 總收入
                    BoxComponent(
                        layout="horizontal",
                        margin="md",
                        contents=[
                            TextComponent(
                                text="總收入",
                                size="md",
                                color="#555555",
                                flex=1
                            ),
                            TextComponent(
                                text=f"${total_amount:.2f}",
                                size="md",
                                color="#00aa00",
                                weight="bold",
                                align="end",
                                flex=1
                            )
                        ]
                    ),
                    # 分隔線
                    SeparatorComponent(
                        margin="xl"
                    ),
                    # 分類統計標題
                    TextComponent(
                        text="分類統計",
                        weight="bold",
                        size="md",
                        margin="xl"
                    )
                ]
            )
        )
        
        # 添加分類統計數據
        for cat, amount in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
            percentage = (amount / total_amount) * 100
            
            # 根據分類取得對應圖標
            icon = self.income_categories.get(cat, "🔹")
            
            # 添加分類條目
            bubble.body.contents.append(
                BoxComponent(
                    layout="horizontal",
                    margin="md",
                    contents=[
                        TextComponent(
                            text=f"{icon} {cat}",
                            size="sm",
                            color="#555555",
                            flex=2
                        ),
                        TextComponent(
                            text=f"${amount:.2f}",
                            size="sm",
                            align="end",
                            flex=1
                        ),
                        TextComponent(
                            text=f"{percentage:.1f}%",
                            size="xs",
                            color="#888888",
                            align="end",
                            flex=1
                        )
                    ]
                )
            )
        
        # 添加查看明細按鈕
        bubble.footer = BoxComponent(
            layout="vertical",
            contents=[
                ButtonComponent(
                    style="primary",
                    action=PostbackAction(
                        label="查看明細",
                        data=json.dumps({
                            "action": "view_details",
                            "type": "income",
                            "time_range": time_range,
                            "time_value": time_value,
                            "category": category,
                            "account": account
                        })
                    )
                )
            ]
        )
        
        # 發送 Flex Message
        flex_message = FlexMessage(alt_text=title, contents=bubble)
        self.line_bot_api.reply_message(reply_token, flex_message)
    
    def _get_time_range_description(self, time_range, time_value):
        """獲取時間範圍的描述文字"""
        if time_range == "day":
            if time_value == "current":
                return "今日"
            elif time_value == "previous":
                return "昨日"
            else:
                # 轉換日期格式
                try:
                    date_obj = datetime.strptime(time_value, "%Y-%m-%d")
                    return date_obj.strftime("%Y年%m月%d日")
                except ValueError:
                    return time_value
        
        elif time_range == "week":
            if time_value == "current":
                return "本週"
            elif time_value == "previous":
                return "上週"
            else:
                return time_value
        
        elif time_range == "month":
            if time_value == "current":
                return "本月"
            elif time_value == "previous":
                return "上月"
            else:
                # 轉換日期格式
                try:
                    year, month = time_value.split("-")
                    return f"{year}年{month}月"
                except ValueError:
                    return time_value
        
        elif time_range == "year":
            if time_value == "current":
                return "今年"
            elif time_value == "previous":
                return "去年"
            else:
                return f"{time_value}年"
        
        else:
            return ""

    def _send_balance_report(self, reply_token, expense_results, income_results, time_range, time_value, account):
        """發送餘額報表"""
        # 計算總餘額
        total_balance = sum(float(record['amount']) for record in expense_results) + sum(float(record['amount']) for record in income_results)
        
        # 構建標題
        title = self._get_time_range_description(time_range, time_value)
        if account:
            title += f"「{account}」帳戶"
        title += "餘額報表"
        
        # 構建 Flex Message 內容
        bubble = FlexContainer(
            header=BoxComponent(
                layout="vertical",
                contents=[
                    TextComponent(
                        text=title,
                        weight="bold",
                        size="xl",
                        align="center"
                    )
                ]
            ),
            body=BoxComponent(
                layout="vertical",
                contents=[
                    # 總餘額
                    BoxComponent(
                        layout="horizontal",
                        margin="md",
                        contents=[
                            TextComponent(
                                text="總餘額",
                                size="md",
                                color="#555555",
                                flex=1
                            ),
                            TextComponent(
                                text=f"${total_balance:.2f}",
                                size="md",
                                color="#ff0000",
                                weight="bold",
                                align="end",
                                flex=1
                            )
                        ]
                    ),
                    # 分隔線
                    SeparatorComponent(
                        margin="xl"
                    )
                ]
            )
        )
        
        # 發送 Flex Message
        flex_message = FlexMessage(alt_text=title, contents=bubble)
        self.line_bot_api.reply_message(reply_token, flex_message)

    def _send_overview_report(self, reply_token, expense_results, income_results, time_range, time_value):
        """發送總覽報表"""
        # 計算總支出和收入
        total_expense = sum(float(record['amount']) for record in expense_results)
        total_income = sum(float(record['amount']) for record in income_results)
        
        # 計算總餘額
        total_balance = total_income - total_expense
        
        # 構建標題
        title = self._get_time_range_description(time_range, time_value)
        title += "總覽報表"
        
        # 構建 Flex Message 內容
        bubble = FlexContainer(
            header=BoxComponent(
                layout="vertical",
                contents=[
                    TextComponent(
                        text=title,
                        weight="bold",
                        size="xl",
                        align="center"
                    )
                ]
            ),
            body=BoxComponent(
                layout="vertical",
                contents=[
                    # 總支出
                    BoxComponent(
                        layout="horizontal",
                        margin="md",
                        contents=[
                            TextComponent(
                                text="總支出",
                                size="md",
                                color="#555555",
                                flex=1
                            ),
                            TextComponent(
                                text=f"${total_expense:.2f}",
                                size="md",
                                color="#ff0000",
                                weight="bold",
                                align="end",
                                flex=1
                            )
                        ]
                    ),
                    # 總收入
                    BoxComponent(
                        layout="horizontal",
                        margin="md",
                        contents=[
                            TextComponent(
                                text="總收入",
                                size="md",
                                color="#555555",
                                flex=1
                            ),
                            TextComponent(
                                text=f"${total_income:.2f}",
                                size="md",
                                color="#00aa00",
                                weight="bold",
                                align="end",
                                flex=1
                            )
                        ]
                    ),
                    # 總餘額
                    BoxComponent(
                        layout="horizontal",
                        margin="md",
                        contents=[
                            TextComponent(
                                text="總餘額",
                                size="md",
                                color="#555555",
                                flex=1
                            ),
                            TextComponent(
                                text=f"${total_balance:.2f}",
                                size="md",
                                color="#ff0000",
                                weight="bold",
                                align="end",
                                flex=1
                            )
                        ]
                    )
                ]
            )
        )
        
        # 發送 Flex Message
        flex_message = FlexMessage(alt_text=title, contents=bubble)
        self.line_bot_api.reply_message(reply_token, flex_message) 
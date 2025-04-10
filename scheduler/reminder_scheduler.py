#!/usr/bin/env python
import os
import logging
import time
from datetime import datetime, timedelta
import threading
import schedule

# 更新LINE Bot SDK導入
from linebot.v3.messaging import (
    ApiClient, MessagingApi, Configuration,
    TextMessage, FlexMessage, PushMessageRequest
)
from database.db_utils import DatabaseUtils

# 設置日誌
logging.basicConfig(
    level=logging.INFO if os.environ.get('LOG_LEVEL') != 'debug' else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ReminderScheduler:
    """提醒排程器，負責檢查並發送即將到期的提醒"""
    
    def __init__(self, line_bot_api=None, db=None):
        """初始化排程器"""
        if line_bot_api is None:
            # 創建API客戶端
            configuration = Configuration(
                access_token=os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
            )
            with ApiClient(configuration) as api_client:
                self.line_bot_api = MessagingApi(api_client)
        else:
            self.line_bot_api = line_bot_api
            
        self.db = db or DatabaseUtils()
        self.is_running = False
        self.scheduler_thread = None
        
        # 定義顏色
        self.colors = {
            "primary": "#4F86C6",
            "secondary": "#7FC4FD",
            "success": "#4CAF50",
            "danger": "#F44336",
            "warning": "#FF9800",
            "info": "#2196F3"
        }
    
    def start(self):
        """啟動排程器"""
        if self.is_running:
            logger.warning("排程器已經在運行中")
            return
        
        logger.info("正在啟動提醒排程器...")
        self.is_running = True
        
        # 設置排程任務
        schedule.every(5).minutes.do(self.check_reminders)
        
        # 創建並啟動排程線程
        self.scheduler_thread = threading.Thread(target=self._run_scheduler)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        
        logger.info("提醒排程器已啟動")
    
    def stop(self):
        """停止排程器"""
        if not self.is_running:
            return
        
        logger.info("正在停止提醒排程器...")
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=10)
        
        logger.info("提醒排程器已停止")
    
    def _run_scheduler(self):
        """運行排程器線程"""
        while self.is_running:
            schedule.run_pending()
            time.sleep(1)
    
    def check_reminders(self):
        """檢查即將到期的提醒並發送通知"""
        logger.info("正在檢查即將到期的提醒...")
        
        try:
            # 獲取未來1小時內即將到期的提醒
            upcoming_reminders = self.db.get_upcoming_reminders(hours_ahead=1)
            
            # 按用戶ID分組提醒
            reminders_by_user = {}
            for reminder in upcoming_reminders:
                user_id = reminder["user_id"]
                if user_id not in reminders_by_user:
                    reminders_by_user[user_id] = []
                reminders_by_user[user_id].append(reminder)
            
            # 為每個用戶發送提醒
            for user_id, reminders in reminders_by_user.items():
                self._send_reminders_to_user(user_id, reminders)
                
            if upcoming_reminders:
                logger.info(f"成功處理 {len(upcoming_reminders)} 個提醒")
            else:
                logger.info("沒有找到即將到期的提醒")
                
        except Exception as e:
            logger.error(f"檢查提醒時發生錯誤: {str(e)}")
    
    def _send_reminders_to_user(self, user_id, reminders):
        """向用戶發送提醒通知"""
        try:
            if len(reminders) == 1:
                # 單個提醒，發送詳細訊息
                reminder = reminders[0]
                self._send_single_reminder(user_id, reminder)
            else:
                # 多個提醒，發送列表
                self._send_reminder_list(user_id, reminders)
                
        except Exception as e:
            logger.error(f"向用戶 {user_id} 發送提醒時發生錯誤: {str(e)}")
    
    def _send_single_reminder(self, user_id, reminder):
        """發送單個提醒通知"""
        title = reminder["title"]
        due_datetime = datetime.fromisoformat(reminder["due_date"])
        now = datetime.now()
        delta = due_datetime - now
        minutes_left = int(delta.total_seconds() / 60)
        
        # 構建時間差文本
        if minutes_left > 60:
            time_left = f"{int(minutes_left / 60)}小時{minutes_left % 60}分鐘後"
        else:
            time_left = f"{minutes_left}分鐘後"
        
        # 創建提醒氣泡
        bubble = {
            "type": "bubble",
            "size": "kilo",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "提醒通知",
                        "weight": "bold",
                        "color": "#FFFFFF",
                        "size": "lg"
                    }
                ],
                "backgroundColor": self.colors["warning"],
                "paddingBottom": "md"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": title,
                        "weight": "bold",
                        "size": "lg",
                        "wrap": True
                    },
                    {
                        "type": "text",
                        "text": f"將在{time_left}開始",
                        "color": self.colors["warning"],
                        "size": "md",
                        "margin": "md"
                    },
                    {
                        "type": "text",
                        "text": due_datetime.strftime("%Y年%m月%d日 %H:%M"),
                        "color": "#888888",
                        "size": "sm",
                        "margin": "md"
                    }
                ],
                "paddingAll": "lg"
            },
            "footer": {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "postback",
                            "label": "完成",
                            "data": f'{{"action":"complete_reminder","reminder_id":"{reminder["reminder_id"]}"}}'
                        },
                        "style": "primary",
                        "color": self.colors["success"]
                    },
                    {
                        "type": "button",
                        "action": {
                            "type": "postback",
                            "label": "延後",
                            "data": f'{{"action":"snooze_reminder","reminder_id":"{reminder["reminder_id"]}"}}'
                        },
                        "style": "primary",
                        "color": self.colors["info"],
                        "margin": "md"
                    }
                ]
            }
        }
        
        # 多個提醒情況下發送Flex訊息
        flex_message = FlexMessage(alt_text="提醒通知", contents=bubble)
        
        # 使用新版SDK的方式發送推送訊息
        self.line_bot_api.push_message_with_http_info(
            PushMessageRequest(
                to=user_id,
                messages=[flex_message]
            )
        )
        logger.info(f"向用戶 {user_id} 發送提醒：{title}")
        
        # 如果是重複提醒，自動創建下一次提醒
        self._handle_repeating_reminder(reminder)
    
    def _send_reminder_list(self, user_id, reminders):
        """發送提醒列表"""
        # 創建提醒列表訊息
        reminders_text = "您有以下提醒：\n\n"
        for i, reminder in enumerate(reminders, 1):
            title = reminder["title"]
            due_datetime = datetime.fromisoformat(reminder["due_date"])
            reminders_text += f"{i}. {title} - {due_datetime.strftime('%H:%M')}\n"
        
        reminders_text += "\n請點擊提醒查看詳情並設置完成。"
        
        # 使用新版SDK的方式發送推送訊息
        self.line_bot_api.push_message_with_http_info(
            PushMessageRequest(
                to=user_id,
                messages=[TextMessage(text=reminders_text)]
            )
        )
        logger.info(f"向用戶 {user_id} 發送 {len(reminders)} 個提醒")
    
    def _handle_repeating_reminder(self, reminder):
        """處理重複提醒，創建下一次提醒"""
        repeat_type = reminder.get("repeat_type")
        if not repeat_type or repeat_type == "none":
            return
        
        try:
            due_datetime = datetime.fromisoformat(reminder["due_date"])
            repeat_value = reminder.get("repeat_value")
            title = reminder["title"]
            description = reminder.get("description")
            remind_before = reminder.get("remind_before", 15)
            user_id = reminder["user_id"]
            
            next_due_date = None
            
            # 根據重複類型計算下一次提醒時間
            if repeat_type == "daily":
                next_due_date = due_datetime + timedelta(days=1)
            elif repeat_type == "weekly":
                next_due_date = due_datetime + timedelta(days=7)
            elif repeat_type == "monthly":
                # 處理月份跨度
                new_month = due_datetime.month + 1
                new_year = due_datetime.year
                if new_month > 12:
                    new_month = 1
                    new_year += 1
                    
                # 處理無效日期（例如2月30日）
                try:
                    next_due_date = due_datetime.replace(year=new_year, month=new_month)
                except ValueError:
                    # 如果日期無效，使用下個月的最後一天
                    if new_month == 12:
                        next_month_first_day = datetime(new_year + 1, 1, 1)
                    else:
                        next_month_first_day = datetime(new_year, new_month + 1, 1)
                    next_due_date = next_month_first_day - timedelta(days=1)
                    next_due_date = next_due_date.replace(
                        hour=due_datetime.hour,
                        minute=due_datetime.minute,
                        second=due_datetime.second
                    )
            
            if next_due_date:
                # 添加下一次重複提醒
                self.db.add_reminder(
                    user_id, title, next_due_date.isoformat(),
                    description, remind_before, repeat_type, repeat_value
                )
                logger.info(f"為用戶 {user_id} 創建下一次重複提醒：{title} - {next_due_date}")
                
        except Exception as e:
            logger.error(f"處理重複提醒時發生錯誤: {str(e)}")

# 如果直接執行此文件，啟動排程器
if __name__ == "__main__":
    # 檢查環境變量
    if not os.environ.get('LINE_CHANNEL_ACCESS_TOKEN'):
        logger.error("未設置 LINE_CHANNEL_ACCESS_TOKEN 環境變量")
        exit(1)
    
    scheduler = ReminderScheduler()
    scheduler.start()
    
    try:
        # 保持程序運行
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        # 捕獲 Ctrl+C
        logger.info("收到中斷信號，正在停止服務...")
        scheduler.stop() 
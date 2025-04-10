#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
LINE 智能記帳與提醒助手 - 數據同步模擬器
模擬LINE端和Web端的數據同步功能
"""

import logging
import json
import time
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

logger = logging.getLogger(__name__)

class DataSync:
    """數據同步類"""
    
    def __init__(self):
        """初始化數據同步器"""
        # 記錄上次同步時間
        self.last_sync_time = 0
        # 模擬的同步狀態
        self.sync_status = {
            "transactions": 0,
            "categories": 0,
            "reminders": 0,
            "accounts": 0
        }
        logger.info("數據同步器初始化完成")
    
    def sync(self, operation, data=None):
        """
        執行同步操作
        
        Args:
            operation (str): 同步操作類型，可以是 'status', 'sync', 'push', 'pull'
            data (dict): 同步數據
            
        Returns:
            dict: 同步結果
        """
        try:
            logger.info(f"執行同步操作: {operation}")
            
            if operation == 'status':
                return self._get_sync_status()
            elif operation == 'sync':
                return self._perform_sync()
            elif operation == 'push':
                return self._push_data(data)
            elif operation == 'pull':
                return self._pull_data(data)
            else:
                logger.error(f"不支持的同步操作: {operation}")
                return {
                    "success": False,
                    "error": f"不支持的同步操作: {operation}"
                }
                
        except Exception as e:
            logger.error(f"同步操作時出錯: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_sync_status(self):
        """獲取同步狀態"""
        current_time = time.time()
        last_sync = self.last_sync_time
        
        # 計算自上次同步以來的時間
        time_since_last_sync = "從未同步" if last_sync == 0 else self._format_time_ago(current_time - last_sync)
        
        # 判斷是否需要同步 (如果超過1小時)
        needs_sync = last_sync == 0 or (current_time - last_sync) > 3600
        
        return {
            "success": True,
            "lastSync": last_sync,
            "timeSinceLastSync": time_since_last_sync,
            "needsSync": needs_sync,
            "syncStatus": self.sync_status
        }
    
    def _perform_sync(self):
        """執行完整同步"""
        # 更新同步時間
        self.last_sync_time = time.time()
        
        # 模擬同步過程
        # 增加各類型數據的同步計數
        self.sync_status["transactions"] += 1
        self.sync_status["categories"] += 1
        self.sync_status["reminders"] += 1
        self.sync_status["accounts"] += 1
        
        # 返回同步結果
        return {
            "success": True,
            "syncTime": self.last_sync_time,
            "syncResults": {
                "transactions": {
                    "added": 5,
                    "updated": 3,
                    "deleted": 1
                },
                "categories": {
                    "added": 2,
                    "updated": 0,
                    "deleted": 0
                },
                "reminders": {
                    "added": 3,
                    "updated": 1,
                    "deleted": 2
                },
                "accounts": {
                    "added": 0,
                    "updated": 1,
                    "deleted": 0
                }
            }
        }
    
    def _push_data(self, data):
        """推送數據到服務器"""
        if not data:
            return {
                "success": False,
                "error": "未提供推送數據"
            }
        
        # 更新同步時間
        self.last_sync_time = time.time()
        
        # 返回推送結果
        return {
            "success": True,
            "pushTime": self.last_sync_time,
            "pushResults": {
                "itemsPushed": len(data.get("items", [])),
                "itemsFailed": 0
            }
        }
    
    def _pull_data(self, data):
        """從服務器拉取數據"""
        # 更新同步時間
        self.last_sync_time = time.time()
        
        # 返回拉取結果
        return {
            "success": True,
            "pullTime": self.last_sync_time,
            "pullResults": {
                "transactions": {
                    "count": 10,
                    "lastUpdate": self.last_sync_time
                },
                "categories": {
                    "count": 8,
                    "lastUpdate": self.last_sync_time
                },
                "reminders": {
                    "count": 5,
                    "lastUpdate": self.last_sync_time
                },
                "accounts": {
                    "count": 3,
                    "lastUpdate": self.last_sync_time
                }
            }
        }
    
    def _format_time_ago(self, seconds):
        """格式化時間間隔"""
        if seconds < 60:
            return "剛剛"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes}分鐘前"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours}小時前"
        else:
            days = int(seconds / 86400)
            return f"{days}天前"

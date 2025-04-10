#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Kimibot 應用程序主入口點

該模塊是應用程序的主要入口點，負責初始化所有組件，
設置服務器配置，加載環境變量，並啟動 Flask 應用。
"""

import os
import sys
import logging
import argparse
from dotenv import load_dotenv

# 添加當前目錄到 Python 路徑，確保可以導入本地模塊
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 配置日誌系統
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("Kimibot")

def init_app():
    """初始化應用程序並返回 Flask 應用實例"""
    try:
        # 加載環境變量
        load_dotenv()
        logger.info("環境變量已加載")
        
        # 導入 Flask 應用
        try:
            from webhook import app
            logger.info("Flask 應用已成功導入")
            return app
        except ImportError as e:
            logger.error(f"無法導入 Flask 應用: {e}")
            raise
            
    except Exception as e:
        logger.critical(f"應用程序初始化失敗: {e}")
        raise

def main():
    """應用程序主函數"""
    # 解析命令行參數
    parser = argparse.ArgumentParser(description='啟動 Kimibot 應用程序')
    parser.add_argument('--host', default=os.environ.get('HOST', '0.0.0.0'), 
                        help='伺服器主機地址 (默認: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=int(os.environ.get('PORT', 8080)), 
                        help='伺服器端口 (默認: 8080)')
    parser.add_argument('--debug', action='store_true', 
                        help='啟用調試模式')
    args = parser.parse_args()
    
    # 輸出啟動信息
    logger.info(f"正在啟動 Kimibot 於 {args.host}:{args.port}")
    
    try:
        # 獲取 Flask 應用實例
        app = init_app()
        
        # 檢測環境類型並相應設置 debug 模式
        is_development = os.environ.get('FLASK_ENV', '').lower() == 'development'
        debug_mode = args.debug or is_development
        
        if debug_mode:
            logger.setLevel(logging.DEBUG)
            logger.debug("調試模式已啟用")
        
        # 打印關鍵配置信息
        logger.info(f"LINE 頻道密鑰長度: {len(os.environ.get('LINE_CHANNEL_SECRET', ''))}")
        logger.info(f"LINE 訪問令牌長度: {len(os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', ''))}")
        logger.info(f"Webhook URL: {os.environ.get('WEBHOOK_URL', '未設置')}")
        
        # 啟動 Flask 應用
        app.run(host=args.host, port=args.port, debug=debug_mode)
        
    except Exception as e:
        logger.critical(f"啟動失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
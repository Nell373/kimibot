#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
LINE 智能記帳與提醒助手 - 模擬環境啟動腳本
這個腳本啟動模擬環境服務，用於測試 LINE Bot 和 PWA 功能。
"""

import os
import sys
import logging
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# 添加當前目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 載入環境變數
load_dotenv()

# 初始化 Flask 應用
app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 導入核心模擬邏輯
from core.line_simulator import LineSimulator
from core.flex_renderer import FlexRenderer
from core.message_handler import MessageHandler
from core.data_sync import DataSync

# 初始化模擬器元件
line_simulator = LineSimulator()
flex_renderer = FlexRenderer()
message_handler = MessageHandler()
data_sync = DataSync()

# 主頁路由
@app.route('/')
def index():
    """渲染模擬環境主頁"""
    return render_template('index.html')

# LINE 模擬器路由
@app.route('/line')
def line_simulator_page():
    """渲染 LINE 模擬界面"""
    return render_template('line_simulator.html')

# PWA 預覽路由
@app.route('/pwa')
def pwa_preview():
    """渲染 PWA 預覽界面"""
    return render_template('pwa_preview.html')

# LINE 訊息發送 API
@app.route('/api/line/send', methods=['POST'])
def line_send_message():
    """處理從模擬器發送到 LINE Bot 的訊息"""
    try:
        data = request.json
        user_id = data.get('user_id', 'test_user_id')
        message_text = data.get('message', '')
        
        # 記錄收到的訊息
        logger.info(f"收到訊息: {message_text} (from: {user_id})")
        
        # 處理訊息並獲取回覆
        response = message_handler.handle_message(user_id, message_text)
        
        # 返回處理結果
        return jsonify({
            'success': True,
            'response': response
        })
    except Exception as e:
        logger.error(f"處理訊息時出錯: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 渲染 Flex Message API
@app.route('/api/flex/render', methods=['POST'])
def render_flex_message():
    """渲染 Flex Message 預覽"""
    try:
        data = request.json
        flex_content = data.get('content', {})
        
        # 渲染 Flex Message
        rendered_html = flex_renderer.render(flex_content)
        
        return jsonify({
            'success': True,
            'html': rendered_html
        })
    except Exception as e:
        logger.error(f"渲染 Flex Message 時出錯: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 數據同步 API
@app.route('/api/sync', methods=['POST'])
def sync_data():
    """同步 LINE 和 Web 端數據"""
    try:
        data = request.json
        operation = data.get('operation', '')
        
        # 執行同步操作
        result = data_sync.sync(operation, data)
        
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        logger.error(f"同步數據時出錯: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 健康檢查 API
@app.route('/health')
def health_check():
    """健康檢查端點"""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0'
    })

# 錯誤處理
@app.errorhandler(404)
def page_not_found(e):
    """處理 404 錯誤"""
    return render_template('error.html', error="找不到頁面"), 404

@app.errorhandler(500)
def server_error(e):
    """處理 500 錯誤"""
    return render_template('error.html', error="伺服器內部錯誤"), 500

if __name__ == '__main__':
    # 獲取端口，默認為 8000
    port = int(os.environ.get('SIMULATOR_PORT', 8000))
    
    # 獲取主機，默認為 localhost
    host = os.environ.get('SIMULATOR_HOST', 'localhost')
    
    # 獲取調試模式，默認為開啟
    debug = os.environ.get('SIMULATOR_DEBUG', 'true').lower() == 'true'
    
    logger.info(f"啟動模擬環境於 http://{host}:{port}")
    
    # 啟動 Flask 應用
    app.run(host=host, port=port, debug=debug)

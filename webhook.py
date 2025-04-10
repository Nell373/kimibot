#!/usr/bin/env python
import os
import sys
import json
import logging
from datetime import datetime, timedelta, date
from functools import wraps
from flask import Flask, request, abort, jsonify, render_template, send_from_directory, redirect, url_for, session

# 將當前目錄加入sys.path，確保可以導入當前目錄下的模塊
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 輸出Python路徑以便調試
print("Python路徑：")
print(sys.path)

# 更新LINE Bot SDK導入
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import (
    MessageEvent, PostbackEvent, 
    TextMessageContent, UserSource, GroupSource, RoomSource
)
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi,
    TextMessage, FlexMessage, FlexContainer,
    ReplyMessageRequest
)

from dotenv import load_dotenv
import requests
import sqlite3

# 手動導入 database 包
from database.db_utils import DatabaseUtils
from handlers.message_handler import MessageHandler
from scheduler.reminder_scheduler import ReminderScheduler
from parsers.text_parser import TextParser
import calendar
import traceback

# 載入環境變數
load_dotenv()

# 設定日誌
logging.basicConfig(
    level=logging.INFO if os.environ.get('LOG_LEVEL') != 'debug' else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 判斷是否為開發環境
is_development = os.environ.get('FLASK_ENV') == 'development'

# 初始化 Flask 應用
app = Flask(__name__, 
           static_url_path='/static',
           static_folder='static',
           template_folder='static/templates')

# 設置 session 密鑰
app.secret_key = os.environ.get('SESSION_SECRET', os.urandom(24).hex())

# 初始化 LINE API
try:
    # 記錄環境變量狀態（不包含完整的敏感信息）
    channel_secret = os.environ.get('LINE_CHANNEL_SECRET', '')
    channel_token = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '')
    logger.info(f"LINE_CHANNEL_SECRET 長度: {len(channel_secret)}")
    logger.info(f"LINE_CHANNEL_ACCESS_TOKEN 長度: {len(channel_token)}")
    logger.info(f"WEBHOOK_URL: {os.environ.get('WEBHOOK_URL', '未設置')}")
    
    # 使用新版SDK初始化
    logger.info("開始初始化LINE Bot API...")
    configuration = Configuration(
        access_token=channel_token
    )
    handler = WebhookHandler(channel_secret)
    
    # 創建API客戶端
    logger.info("創建LINE API客戶端...")
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
    
    # 檢查憑證是否有效
    if not is_development:
        try:
            # 測試連接 (在v3中，不同的方式測試連接)
            logger.info("測試LINE Bot API連接...")
            with ApiClient(configuration) as api_client:
                from linebot.v3.messaging import MessagingApiBlob
                bot_info_api = MessagingApiBlob(api_client)
                # 獲取機器人資訊
                bot_info = bot_info_api.get_bot_info()
                logger.info(f"已成功連接到 LINE 平台，機器人名稱: {bot_info.display_name if hasattr(bot_info, 'display_name') else '未知'}")
        except Exception as connection_error:
            logger.error(f"LINE Bot API連接測試失敗: {str(connection_error)}")
            logger.error(f"錯誤詳情: {traceback.format_exc()}")
            raise
    else:
        logger.warning("開發環境模式啟動，部分功能將被模擬")

except Exception as e:
    logger.error(f"連接 LINE 平台失敗: {str(e)}")
    logger.error(f"錯誤詳情: {traceback.format_exc()}")
    if is_development:
        logger.warning("在開發環境中繼續運行，使用模擬物件")
        # 在開發環境中，如果 LINE 憑證無效，我們可以繼續使用模擬物件
        from unittest.mock import MagicMock
        line_bot_api = MagicMock()
        handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET', 'test_secret'))
    else:
        # 在生產環境，如果憑證無效則終止應用
        logger.critical("在生產環境中無法連接LINE平台，應用將終止")
        raise

# 初始化資料庫工具
db = DatabaseUtils()

# 初始化訊息處理器
message_handler = MessageHandler(line_bot_api, db)

# 初始化提醒排程器
reminder_scheduler = ReminderScheduler(line_bot_api, db)

# 定義啟動時的初始化函數(替代 @app.before_first_request 裝飾器)
def start_scheduler_and_setup():
    """服務啟動後，啟動提醒排程器"""
    logger.info("啟動提醒排程器...")
    reminder_scheduler.start()
    
    # 創建並註冊快速選單
    if not is_development:
        try:
            logger.info("開始創建快速選單...")
            rich_menu_id = message_handler.create_quick_menu()
            if rich_menu_id:
                logger.info(f"快速選單創建成功，ID: {rich_menu_id}")
            else:
                logger.warning("快速選單創建失敗")
        except Exception as e:
            logger.error(f"創建快速選單時發生錯誤: {str(e)}")
    else:
        logger.info("開發環境中跳過創建快速選單")

# 在應用啟動時執行初始化
with app.app_context():
    start_scheduler_and_setup()

# 登入保護裝飾器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查 session 是否包含 user_id
        if 'user_id' not in session:
            # 檢查 cookie 或本地存儲是否有令牌（從前端傳來）
            auth_token = request.cookies.get('auth_token')
            if not auth_token:
                return redirect(url_for('login_page'))
            
            # 驗證令牌（這裡應該有更嚴格的驗證）
            try:
                # 簡單驗證，真實情況應更嚴格
                user_id = verify_token(auth_token)
                if not user_id:
                    return redirect(url_for('login_page'))
                
                # 存入 session
                session['user_id'] = user_id
            except:
                return redirect(url_for('login_page'))
        
        return f(*args, **kwargs)
    return decorated_function

# 驗證令牌的函數
def verify_token(token):
    try:
        # 目前的token格式是base64編碼的 "user_id:timestamp"
        # 簡單解碼檢查，實際應用應使用JWT或其他安全方法
        import base64
        decoded = base64.b64decode(token).decode('utf-8')
        parts = decoded.split(':')
        
        if len(parts) != 2:
            return None
        
        user_id, timestamp = parts
        
        # 檢查是否過期（24小時）
        token_time = int(timestamp)
        current_time = int(datetime.now().timestamp() * 1000)
        
        if current_time - token_time > 24 * 60 * 60 * 1000:  # 24小時
            return None
            
        return user_id
    except:
        return None

# 主頁路由
@app.route('/')
def index():
    """主頁"""
    return render_template('index.html')

# 登入頁面
@app.route('/login')
def login_page():
    """登入頁面"""
    # 如果已經登入，重定向到儀表板
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

# 儀表板頁面
@app.route('/dashboard')
@login_required
def dashboard():
    """儀表板頁面 - 需登入保護"""
    return render_template('dashboard.html')

# 離線頁面
@app.route('/offline')
def offline():
    """離線頁面"""
    return render_template('offline.html')

# 靜態文件路由
@app.route('/static/manifest.json')
def manifest():
    """PWA manifest 文件"""
    return send_from_directory('static', 'manifest.json')

@app.route('/static/sw.js')
def service_worker():
    """PWA Service Worker"""
    return send_from_directory('static', 'sw.js')

# 健康檢查端點 (用於 Fly.io 監控)
@app.route('/health', methods=['GET'])
def health_check():
    """健康檢查端點"""
    is_line_initialized = True
    line_status = "ok"
    
    try:
        # 簡單的連接測試
        if not is_development and 'line_bot_api' in globals():
            with ApiClient(configuration) as api_client:
                bot_info_api = MessagingApiBlob(api_client)
                bot_info_api.get_bot_info()
    except Exception as e:
        is_line_initialized = False
        line_status = str(e)[:100]  # 截斷錯誤信息以避免過長
    
    app_info = {
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'environment': os.environ.get('FLASK_ENV', 'unknown'),
        'line_bot': {
            'initialized': is_line_initialized,
            'status': line_status,
            'secret_length': len(os.environ.get('LINE_CHANNEL_SECRET', '')),
            'token_length': len(os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '')),
            'webhook_url': os.environ.get('WEBHOOK_URL', 'not set')
        },
        'message': 'Kimibot is running!'
    }
    
    return jsonify(app_info), 200

# LINE Webhook 入口
@app.route('/api/webhook', methods=['POST'])
def webhook():
    """LINE Webhook 入口點"""
    # 取得 X-Line-Signature 標頭
    signature = request.headers.get('X-Line-Signature')
    
    # 取得請求主體
    body = request.get_data(as_text=True)
    
    logger.info('Request body: %s', body)
    
    # 處理開發環境的測試請求
    if is_development:
        # 檢查是否為測試請求
        try:
            data = json.loads(body)
            is_test_request = any(
                event.get('source', {}).get('userId') == 'test_user_id' 
                for event in data.get('events', [])
            )
            
            if is_test_request:
                logger.warning("開發環境檢測到測試請求")
                
                # 如果提供了有效的簽名，嘗試正常處理
                if signature:
                    try:
                        handler.handle(body, signature)
                        return 'OK (Development Mode - Verified)'
                    except InvalidSignatureError:
                        logger.warning("測試請求的簽名無效，將手動處理事件")
                else:
                    logger.warning("測試請求未提供簽名，將手動處理事件")
                
                # 手動處理事件
                for event in data.get('events', []):
                    # 確保測試用戶存在於資料庫
                    ensure_user_exists('test_user_id')
                    
                    if event.get('type') == 'message' and event.get('message', {}).get('type') == 'text':
                        # 模擬文字消息事件
                        from linebot.v3.webhooks import MessageEvent, TextMessageContent, UserSource
                        
                        message_event = MessageEvent(
                            message=TextMessageContent(id=event['message']['id'], text=event['message']['text']),
                            reply_token=event['replyToken'],
                            source=UserSource(user_id=event['source']['userId']),
                            timestamp=event.get('timestamp', int(datetime.now().timestamp() * 1000))
                        )
                        
                        # 處理文字消息
                        handle_text_message(message_event)
                        
                    elif event.get('type') == 'postback':
                        # 模擬 Postback 事件
                        from linebot.v3.webhooks import PostbackEvent, UserSource, Postback
                        
                        postback_event = PostbackEvent(
                            reply_token=event['replyToken'],
                            source=UserSource(user_id=event['source']['userId']),
                            postback=Postback(data=event['postback'].get('data')),
                            timestamp=event.get('timestamp', int(datetime.now().timestamp() * 1000))
                        )
                        
                        # 處理 Postback
                        handle_postback(postback_event)
                
                return 'OK (Development Mode - Test User)'
        except Exception as e:
            logger.error(f"處理開發環境測試請求時出錯: {str(e)}")
    
    # 正常環境處理 (或開發環境非測試請求)
    try:
        # 驗證簽名
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error('Invalid signature')
        abort(400)
    
    return 'OK'

# 處理文字訊息
@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    """處理文字訊息"""
    try:
        user_id = event.source.user_id
        reply_token = event.reply_token
        text = event.message.text
        
        # 確保用戶存在
        user = ensure_user_exists(user_id)
        
        # 使用 MessageHandler 處理文字訊息
        message_handler = MessageHandler(line_bot_api, db)
        
        # 解析文字訊息
        parser = TextParser()
        result = parser.parse_text(text)
        
        if result:
            result_type = result.get("type")
            
            if result_type == "accounting":
                # 處理記帳
                message_handler.handle_accounting(user_id, reply_token, result.get("data"))
            elif result_type == "reminder":
                # 處理提醒
                message_handler.handle_reminder(user_id, reply_token, result.get("data"))
            elif result_type == "query":
                # 處理查詢
                message_handler.handle_query(reply_token, result.get("data"))
            elif result_type == "account":
                # 處理帳戶操作
                message_handler.handle_account(user_id, reply_token, result.get("data"))
            else:
                # 其他類型或無法識別的指令
                message_handler.handle_conversation(reply_token, result.get("data", {}).get("message", "我不太明白您的意思，請嘗試使用更明確的指令。"))
        else:
            # 若無法解析，顯示錯誤訊息
            message_handler.handle_conversation(reply_token, "抱歉，我沒有理解您的指令，請嘗試使用更明確的表達方式。")
    
    except Exception as e:
        logger.error(f"處理文字訊息時發生錯誤: {str(e)}")
        if reply_token:
            try:
                # 使用新版SDK的方式發送回覆
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=reply_token,
                        messages=[TextMessage(text="抱歉，處理您的訊息時出現了問題，請稍後再試。")]
                    )
                )
            except Exception as reply_error:
                logger.error(f"發送錯誤訊息失敗: {str(reply_error)}")

# 處理 Postback 事件
@handler.add(PostbackEvent)
def handle_postback(event):
    """處理用戶的 Postback 事件（選擇按鈕等）"""
    user_id = event.source.user_id
    
    # 確保用戶存在於資料庫
    ensure_user_exists(user_id)
    
    try:
        # 使用訊息處理器處理 postback
        message_handler.handle_postback(event)
        
        logger.info(f"已處理用戶 {user_id} 的 postback")
    except Exception as e:
        logger.error('Error processing postback: %s', str(e))
        
        # 在生產環境才嘗試發送錯誤訊息
        if not is_development:
            try:
                # 使用新版SDK的方式發送回覆
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=f"抱歉，處理您的選擇時發生錯誤：{str(e)}")]
                    )
                )
            except Exception as reply_error:
                logger.error('Error sending error message: %s', str(reply_error))

def ensure_user_exists(user_id):
    """確保用戶存在於資料庫中"""
    user = db.get_user(user_id)
    
    if not user:
        try:
            # 從 LINE 獲取用戶資料
            if user_id == 'test_user_id' and is_development:
                # 測試用戶
                db.create_user(user_id, "測試用戶")
                logger.info(f"測試用戶已創建: 測試用戶 ({user_id})")
            else:
                # 正常用戶
                profile = line_bot_api.get_profile(user_id)
                db.create_user(user_id, profile.display_name)
                logger.info(f"新用戶已創建: {profile.display_name} ({user_id})")
        except Exception as e:
            logger.error('Error getting user profile: %s', str(e))
            # 創建一個默認用戶名稱
            db.create_user(user_id, f"User_{user_id[:8]}")
            logger.info(f"新用戶已創建 (使用預設名稱): User_{user_id[:8]}")

# 錯誤處理
@app.errorhandler(404)
def page_not_found(e):
    """404 頁面"""
    return render_template('offline.html'), 404

@app.errorhandler(500)
def server_error(e):
    """500 錯誤頁面"""
    logger.error(f"伺服器錯誤: {str(e)}")
    return jsonify({"error": "伺服器內部錯誤"}), 500

# Fly.io 部署設置
if __name__ == "__main__":
    import argparse
    import ssl
    import sys
    
    # 配置詳細的日誌信息
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout  # 確保日誌輸出到標準輸出
    )
    
    # 禁用SSL證書驗證（僅用於調試）
    try:
        _create_unverified_https_context = ssl._create_unverified_context
        ssl._create_default_https_context = _create_unverified_https_context
        logger.info("已禁用SSL證書驗證，僅用於調試")
    except Exception as e:
        logger.warning(f"無法禁用SSL證書驗證: {str(e)}")
    
    # 解析命令行參數
    parser = argparse.ArgumentParser(description='啟動LINE機器人webhook服務')
    parser.add_argument('--port', type=int, default=8080, help='服務端口號')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='服務主機地址')
    args = parser.parse_args()
    
    # 記錄環境變數情況
    logger.info(f"環境變數: FLASK_ENV={os.environ.get('FLASK_ENV', '未設置')}")
    logger.info(f"環境變數: LINE_CHANNEL_SECRET={os.environ.get('LINE_CHANNEL_SECRET', '未設置')[0:5]}...")
    logger.info(f"環境變數: LINE_CHANNEL_ACCESS_TOKEN={os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '未設置')[0:5]}...")
    logger.info(f"環境變數: PORT={os.environ.get('PORT', '未設置')}")
    
    # 獲取環境變數設置的端口或使用參數設置的端口
    port = int(os.environ.get("PORT", args.port))
    host = os.environ.get("HOST", args.host)
    
    logger.info(f"啟動應用，監聽 {host}:{port}")
    
    try:
        # 確保應用程序在0.0.0.0:8080上監聽
        app.run(host=host, port=port, debug=False, threaded=True)
    except Exception as e:
        logger.error(f"啟動應用時發生錯誤: {str(e)}")

# 登入API
@app.route('/api/login', methods=['POST'])
def api_login():
    """用戶登入API"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "無效的請求數據"}), 400
    
    login_type = data.get('type')
    
    if login_type == 'line':
        # LINE登入
        user_id = data.get('userId')
        display_name = data.get('displayName')
        
        if not user_id:
            return jsonify({"error": "缺少用戶ID"}), 400
            
        # 確保用戶存在於數據庫
        user = ensure_user_exists(user_id)
        
        # 生成令牌
        token = generate_token(user_id)
        
        # 設置會話
        session['user_id'] = user_id
        session['user_name'] = display_name
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "display_name": display_name,
            "token": token
        })
    
    elif login_type == 'form':
        # 表單登入
        user_id = data.get('userId')
        password = data.get('password')
        
        if not user_id or not password:
            return jsonify({"error": "缺少用戶ID或密碼"}), 400
        
        # 這裡應該有真實的密碼驗證
        # 目前簡單模擬：任何有效LINE ID格式和6位以上密碼
        if not user_id.startswith('U') or len(password) < 6:
            return jsonify({"error": "用戶ID或密碼不正確"}), 401
            
        # 確保用戶存在於數據庫
        user = ensure_user_exists(user_id)
        
        # 生成令牌
        token = generate_token(user_id)
        
        # 設置會話
        session['user_id'] = user_id
        session['user_name'] = "Web使用者"  # 可從資料庫取得真實名稱
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "display_name": "Web使用者",  # 可從資料庫取得真實名稱
            "token": token
        })
    
    else:
        return jsonify({"error": "不支持的登入類型"}), 400

# 登出API
@app.route('/api/logout', methods=['POST'])
def api_logout():
    """用戶登出API"""
    # 清除會話
    session.pop('user_id', None)
    session.pop('user_name', None)
    
    return jsonify({"success": True})

# 檢查登入狀態API
@app.route('/api/check-auth', methods=['GET'])
def api_check_auth():
    """檢查用戶登入狀態"""
    if 'user_id' in session:
        return jsonify({
            "authenticated": True,
            "user_id": session['user_id'],
            "user_name": session.get('user_name', '使用者')
        })
    
    # 檢查請求頭中的令牌
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        user_id = verify_token(token)
        
        if user_id:
            # 取得用戶信息（這裡應該從資料庫獲取）
            # 簡單起見，假設Web使用者
            user_name = "Web使用者"
            
            # 更新會話
            session['user_id'] = user_id
            session['user_name'] = user_name
            
            return jsonify({
                "authenticated": True,
                "user_id": user_id,
                "user_name": user_name
            })
    
    return jsonify({"authenticated": False})

# 獲取交易記錄API
@app.route('/api/transactions', methods=['GET'])
@login_required
def api_get_transactions():
    """獲取用戶交易記錄"""
    # 從會話中獲取用戶ID
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "未授權訪問"}), 401
    
    # 獲取查詢參數
    transaction_type = request.args.get('type')  # expense, income, all
    date_range = request.args.get('date_range', 'this-month')  # this-month, last-month, this-week, last-week, custom
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    category_id = request.args.get('category_id')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    
    # 根據date_range計算日期範圍
    today = date.today()
    
    if not start_date or not end_date:
        if date_range == 'this-month':
            start_date = date(today.year, today.month, 1).isoformat()
            # 下個月的第一天減一天
            end_date = (date(today.year, today.month + 1 if today.month < 12 else 1, 1) - timedelta(days=1)).isoformat()
        elif date_range == 'last-month':
            last_month = today.month - 1 if today.month > 1 else 12
            last_month_year = today.year if today.month > 1 else today.year - 1
            start_date = date(last_month_year, last_month, 1).isoformat()
            end_date = (date(today.year, today.month, 1) - timedelta(days=1)).isoformat()
        elif date_range == 'this-week':
            # 計算本週一
            start_date = (today - timedelta(days=today.weekday())).isoformat()
            end_date = today.isoformat()
        elif date_range == 'last-week':
            # 計算上週一和上週日
            last_week_monday = today - timedelta(days=today.weekday() + 7)
            last_week_sunday = today - timedelta(days=today.weekday() + 1)
            start_date = last_week_monday.isoformat()
            end_date = last_week_sunday.isoformat()
        else:
            # 默認查詢本月
            start_date = date(today.year, today.month, 1).isoformat()
            end_date = today.isoformat()
    
    # 計算分頁
    offset = (page - 1) * limit
    
    # 創建資料庫查詢
    db = DatabaseUtils()
    
    # 構建查詢條件
    conditions = ["user_id = ?"]
    params = [user_id]
    
    if transaction_type and transaction_type != 'all':
        conditions.append("type = ?")
        params.append(transaction_type)
    
    conditions.append("date BETWEEN ? AND ?")
    params.extend([start_date, end_date])
    
    if category_id:
        conditions.append("category_id = ?")
        params.append(category_id)
    
    # 構建SQL查詢
    query = f"""
        SELECT t.*, c.name as category_name, c.icon as category_icon, a.name as account_name
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.category_id
        LEFT JOIN accounts a ON t.account_id = a.account_id
        WHERE {" AND ".join(conditions)}
        ORDER BY t.date DESC, t.transaction_id DESC
        LIMIT ? OFFSET ?
    """
    
    # 添加分頁參數
    params.extend([limit, offset])
    
    # 計算總記錄數
    count_query = f"""
        SELECT COUNT(*) as total
        FROM transactions
        WHERE {" AND ".join(conditions)}
    """
    
    # 執行查詢
    transactions = db.execute_query(query, tuple(params))
    count_result = db.execute_query(count_query, tuple(params[:-2]), fetchall=False)
    
    total_records = count_result['total'] if count_result else 0
    total_pages = (total_records + limit - 1) // limit
    
    # 格式化日期和金額
    for transaction in transactions:
        if 'date' in transaction:
            # 轉換日期格式為前端可用的格式
            try:
                transaction_date = datetime.strptime(transaction['date'], '%Y-%m-%d').date()
                transaction['date_formatted'] = transaction_date.strftime('%Y年%m月%d日')
            except:
                transaction['date_formatted'] = transaction['date']
    
    # 返回結果
    return jsonify({
        "transactions": transactions,
        "pagination": {
            "current_page": page,
            "total_pages": total_pages,
            "total_records": total_records,
            "has_next": page < total_pages,
            "has_prev": page > 1
        },
        "filters": {
            "type": transaction_type,
            "date_range": date_range,
            "start_date": start_date,
            "end_date": end_date,
            "category_id": category_id
        }
    })

# 刪除交易記錄API
@app.route('/api/transactions/<int:transaction_id>', methods=['DELETE'])
@login_required
def api_delete_transaction(transaction_id):
    """刪除交易記錄"""
    # 從會話中獲取用戶ID
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "未授權訪問"}), 401
    
    # 檢查該交易是否屬於該用戶
    db = DatabaseUtils()
    transaction = db.execute_query(
        "SELECT * FROM transactions WHERE transaction_id = ? AND user_id = ?", 
        (transaction_id, user_id),
        fetchall=False
    )
    
    if not transaction:
        return jsonify({"error": "交易記錄不存在或無權刪除"}), 404
    
    # 先記錄交易信息，以便更新帳戶餘額
    account_id = transaction.get('account_id')
    amount = transaction.get('amount', 0)
    transaction_type = transaction.get('type')
    
    # 刪除交易記錄
    db.execute_update("DELETE FROM transactions WHERE transaction_id = ?", (transaction_id,))
    
    # 更新帳戶餘額
    if account_id and amount and transaction_type:
        # 如果是收入，則減少餘額；如果是支出，則增加餘額
        amount_change = -amount if transaction_type == 'income' else amount
        db.update_account_balance(account_id, amount_change)
    
    return jsonify({"success": True, "message": "交易記錄已刪除"})

# 生成令牌
def generate_token(user_id):
    """生成簡單的驗證令牌"""
    # 實際環境應使用 JWT 或其他安全方式
    import base64
    timestamp = int(datetime.now().timestamp() * 1000)
    token_data = f"{user_id}:{timestamp}"
    return base64.b64encode(token_data.encode('utf-8')).decode('utf-8')

# 獲取單個交易記錄的API
@app.route('/api/transactions/<int:transaction_id>', methods=['GET'])
@login_required
def api_get_transaction(transaction_id):
    """獲取單個交易記錄詳情"""
    # 從會話中獲取用戶ID
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "未授權訪問"}), 401
    
    # 查詢交易記錄
    db = DatabaseUtils()
    transaction = db.execute_query(
        """
        SELECT t.*, c.name as category_name, c.icon as category_icon, a.name as account_name
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.category_id
        LEFT JOIN accounts a ON t.account_id = a.account_id
        WHERE t.transaction_id = ? AND t.user_id = ?
        """, 
        (transaction_id, user_id),
        fetchall=False
    )
    
    if not transaction:
        return jsonify({"error": "交易記錄不存在或無權查看"}), 404
    
    # 格式化日期
    if 'date' in transaction:
        try:
            transaction_date = datetime.strptime(transaction['date'], '%Y-%m-%d').date()
            transaction['date_formatted'] = transaction_date.strftime('%Y年%m月%d日')
        except:
            transaction['date_formatted'] = transaction['date']
    
    return jsonify(transaction)

# 新增交易記錄API
@app.route('/api/transactions', methods=['POST'])
@login_required
def api_add_transaction():
    """新增交易記錄"""
    # 從會話中獲取用戶ID
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "未授權訪問"}), 401
    
    # 獲取請求數據
    data = request.json
    
    # 驗證必要字段
    if not data:
        return jsonify({"error": "無效的請求數據"}), 400
    
    # 獲取數據字段
    transaction_type = data.get('type')
    amount = data.get('amount')
    date_str = data.get('date')
    category_id = data.get('category_id')
    account_id = data.get('account_id')
    memo = data.get('memo', '')
    
    # 驗證必填字段
    if not transaction_type or not amount or not date_str:
        return jsonify({"error": "缺少必要參數"}), 400
    
    if transaction_type not in ['expense', 'income']:
        return jsonify({"error": "無效的交易類型"}), 400
    
    # 創建資料庫連接
    db = DatabaseUtils()
    
    # 新增交易記錄
    try:
        transaction_id = db.add_transaction(
            user_id, account_id, category_id, 
            transaction_type, amount, memo, date_str
        )
        
        # 獲取新增後的交易記錄詳情
        transaction = db.execute_query(
            """
            SELECT t.*, c.name as category_name, c.icon as category_icon, a.name as account_name
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.category_id
            LEFT JOIN accounts a ON t.account_id = a.account_id
            WHERE t.transaction_id = ?
            """, 
            (transaction_id,),
            fetchall=False
        )
        
        return jsonify({
            "success": True,
            "message": "交易記錄已新增",
            "transaction": transaction
        })
    
    except Exception as e:
        return jsonify({"error": f"新增交易記錄失敗: {str(e)}"}), 500

# 更新交易記錄API
@app.route('/api/transactions/<int:transaction_id>', methods=['PUT'])
@login_required
def api_update_transaction(transaction_id):
    """更新交易記錄"""
    # 從會話中獲取用戶ID
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "未授權訪問"}), 401
    
    # 獲取請求數據
    data = request.json
    
    # 驗證必要字段
    if not data:
        return jsonify({"error": "無效的請求數據"}), 400
    
    # 檢查交易記錄是否存在且屬於該用戶
    db = DatabaseUtils()
    original_transaction = db.execute_query(
        "SELECT * FROM transactions WHERE transaction_id = ? AND user_id = ?", 
        (transaction_id, user_id),
        fetchall=False
    )
    
    if not original_transaction:
        return jsonify({"error": "交易記錄不存在或無權修改"}), 404
    
    # 獲取數據字段
    transaction_type = data.get('type')
    amount = data.get('amount')
    date_str = data.get('date')
    category_id = data.get('category_id')
    account_id = data.get('account_id')
    memo = data.get('memo', '')
    
    # 驗證必填字段
    if not transaction_type or amount is None or not date_str:
        return jsonify({"error": "缺少必要參數"}), 400
    
    if transaction_type not in ['expense', 'income']:
        return jsonify({"error": "無效的交易類型"}), 400
    
    # 調整原帳戶餘額 (還原交易前的狀態)
    original_account_id = original_transaction.get('account_id')
    original_amount = original_transaction.get('amount', 0)
    original_type = original_transaction.get('type')
    
    if original_account_id and original_amount and original_type:
        # 如果原交易是支出，還原時增加餘額；如果是收入，還原時減少餘額
        amount_change = original_amount if original_type == 'expense' else -original_amount
        db.update_account_balance(original_account_id, amount_change)
    
    # 更新交易記錄
    try:
        update_query = """
            UPDATE transactions 
            SET type = ?, amount = ?, date = ?, category_id = ?, account_id = ?, description = ?
            WHERE transaction_id = ? AND user_id = ?
        """
        
        db.execute_update(
            update_query, 
            (transaction_type, amount, date_str, category_id, account_id, memo, transaction_id, user_id)
        )
        
        # 更新新帳戶餘額
        if account_id and amount:
            # 如果是收入增加餘額，如果是支出減少餘額
            amount_change = amount if transaction_type == 'income' else -amount
            db.update_account_balance(account_id, amount_change)
        
        # 獲取更新後的交易記錄詳情
        updated_transaction = db.execute_query(
            """
            SELECT t.*, c.name as category_name, c.icon as category_icon, a.name as account_name
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.category_id
            LEFT JOIN accounts a ON t.account_id = a.account_id
            WHERE t.transaction_id = ?
            """, 
            (transaction_id,),
            fetchall=False
        )
        
        return jsonify({
            "success": True,
            "message": "交易記錄已更新",
            "transaction": updated_transaction
        })
    
    except Exception as e:
        return jsonify({"error": f"更新交易記錄失敗: {str(e)}"}), 500

# 獲取分類列表API
@app.route('/api/categories', methods=['GET'])
@login_required
def api_get_categories():
    """獲取分類列表"""
    # 從會話中獲取用戶ID
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "未授權訪問"}), 401
    
    # 獲取查詢參數
    type_name = request.args.get('type')  # expense, income
    
    # 創建資料庫連接
    db = DatabaseUtils()
    
    # 獲取分類列表
    categories = db.get_categories(user_id, type_name)
    
    return jsonify(categories)

# 獲取帳戶列表API
@app.route('/api/accounts', methods=['GET'])
@login_required
def api_get_accounts():
    """獲取帳戶列表"""
    # 從會話中獲取用戶ID
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "未授權訪問"}), 401
    
    # 創建資料庫連接
    db = DatabaseUtils()
    
    # 獲取帳戶列表
    accounts = db.get_accounts(user_id)
    
    return jsonify(accounts)

# 新增分類API
@app.route('/api/categories', methods=['POST'])
@login_required
def api_add_category():
    """新增分類"""
    # 從會話中獲取用戶ID
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "未授權訪問"}), 401
    
    # 獲取請求數據
    data = request.json
    
    # 驗證必要字段
    if not data:
        return jsonify({"error": "無效的請求數據"}), 400
    
    # 獲取數據字段
    name = data.get('name')
    type_name = data.get('type')
    icon = data.get('icon', '')
    
    # 驗證必填字段
    if not name or not type_name:
        return jsonify({"error": "缺少必要參數"}), 400
    
    if type_name not in ['expense', 'income']:
        return jsonify({"error": "無效的分類類型"}), 400
    
    # 創建資料庫連接
    db = DatabaseUtils()
    
    # 檢查分類是否已存在
    existing = db.execute_query(
        "SELECT * FROM categories WHERE name = ? AND type = ? AND (user_id = ? OR user_id IS NULL)",
        (name, type_name, user_id),
        fetchall=False
    )
    
    if existing:
        return jsonify({"error": "分類名稱已存在"}), 400
    
    # 新增分類
    try:
        category_id = db.add_category(user_id, name, type_name, icon)
        
        # 獲取新增後的分類詳情
        category = db.execute_query(
            "SELECT * FROM categories WHERE category_id = ?", 
            (category_id,),
            fetchall=False
        )
        
        return jsonify({
            "success": True,
            "message": "分類已新增",
            "category": category
        })
    
    except Exception as e:
        return jsonify({"error": f"新增分類失敗: {str(e)}"}), 500

# 更新分類API
@app.route('/api/categories/<int:category_id>', methods=['PUT'])
@login_required
def api_update_category(category_id):
    """更新分類"""
    # 從會話中獲取用戶ID
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "未授權訪問"}), 401
    
    # 獲取請求數據
    data = request.json
    
    # 驗證必要字段
    if not data:
        return jsonify({"error": "無效的請求數據"}), 400
    
    # 檢查該分類是否屬於該用戶
    db = DatabaseUtils()
    category = db.execute_query(
        "SELECT * FROM categories WHERE category_id = ? AND user_id = ?", 
        (category_id, user_id),
        fetchall=False
    )
    
    if not category:
        return jsonify({"error": "分類不存在或無權修改"}), 404
    
    # 系統預設分類不允許修改
    if category.get('is_default', 0) == 1:
        return jsonify({"error": "系統預設分類不可修改"}), 403
    
    # 獲取數據字段
    name = data.get('name')
    icon = data.get('icon')
    
    # 驗證必填字段
    if not name:
        return jsonify({"error": "缺少分類名稱"}), 400
    
    # 檢查分類名稱是否已存在（排除當前分類）
    existing = db.execute_query(
        """
        SELECT * FROM categories 
        WHERE name = ? AND type = ? AND (user_id = ? OR user_id IS NULL)
        AND category_id != ?
        """,
        (name, category.get('type'), user_id, category_id),
        fetchall=False
    )
    
    if existing:
        return jsonify({"error": "分類名稱已存在"}), 400
    
    # 更新分類
    try:
        db.execute_update(
            "UPDATE categories SET name = ?, icon = ? WHERE category_id = ?",
            (name, icon, category_id)
        )
        
        # 獲取更新後的分類詳情
        updated_category = db.execute_query(
            "SELECT * FROM categories WHERE category_id = ?", 
            (category_id,),
            fetchall=False
        )
        
        return jsonify({
            "success": True,
            "message": "分類已更新",
            "category": updated_category
        })
    
    except Exception as e:
        return jsonify({"error": f"更新分類失敗: {str(e)}"}), 500

# 刪除分類API
@app.route('/api/categories/<int:category_id>', methods=['DELETE'])
@login_required
def api_delete_category(category_id):
    """刪除分類"""
    # 從會話中獲取用戶ID
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "未授權訪問"}), 401
    
    # 檢查該分類是否屬於該用戶
    db = DatabaseUtils()
    category = db.execute_query(
        "SELECT * FROM categories WHERE category_id = ? AND user_id = ?", 
        (category_id, user_id),
        fetchall=False
    )
    
    if not category:
        return jsonify({"error": "分類不存在或無權刪除"}), 404
    
    # 系統預設分類不允許刪除
    if category.get('is_default', 0) == 1:
        return jsonify({"error": "系統預設分類不可刪除"}), 403
    
    # 檢查該分類是否有關聯的交易記錄
    associated_transactions = db.execute_query(
        "SELECT COUNT(*) as count FROM transactions WHERE category_id = ?",
        (category_id,),
        fetchall=False
    )
    
    if associated_transactions and associated_transactions.get('count', 0) > 0:
        return jsonify({"error": "該分類已有關聯的交易記錄，不可刪除"}), 400
    
    # 刪除分類
    try:
        db.execute_update("DELETE FROM categories WHERE category_id = ?", (category_id,))
        
        return jsonify({
            "success": True,
            "message": "分類已刪除"
        })
    
    except Exception as e:
        return jsonify({"error": f"刪除分類失敗: {str(e)}"}), 500

# 獲取提醒列表API
@app.route('/api/reminders', methods=['GET'])
@login_required
def api_get_reminders():
    """獲取提醒列表"""
    # 從會話中獲取用戶ID
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "未授權訪問"}), 401
    
    # 獲取查詢參數
    status = request.args.get('status', 'pending')  # 默認獲取未完成的提醒
    
    # 創建資料庫連接
    db = DatabaseUtils()
    
    # 構建查詢條件
    query_conditions = ["user_id = ?"]
    query_params = [user_id]
    
    if status != 'all':
        query_conditions.append("status = ?")
        query_params.append(status)
    
    # 構建完整查詢
    query = f"""
        SELECT * FROM reminders 
        WHERE {' AND '.join(query_conditions)}
        ORDER BY datetime ASC
    """
    
    # 執行查詢
    reminders = db.execute_query(query, tuple(query_params), fetchall=True)
    
    return jsonify(reminders)

# 新增提醒API
@app.route('/api/reminders', methods=['POST'])
@login_required
def api_add_reminder():
    """新增提醒"""
    # 從會話中獲取用戶ID
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "未授權訪問"}), 401
    
    # 獲取請求數據
    data = request.json
    
    # 驗證必要字段
    if not data:
        return jsonify({"error": "無效的請求數據"}), 400
    
    # 獲取數據字段
    content = data.get('content')
    datetime_str = data.get('datetime')
    repeat_type = data.get('repeat_type', 'none')
    notify_before = data.get('notify_before', 0)
    
    # 驗證必填字段
    if not content or not datetime_str:
        return jsonify({"error": "缺少必要參數"}), 400
    
    # 創建資料庫連接
    db = DatabaseUtils()
    
    # 新增提醒
    try:
        # 構建提醒數據
        reminder_data = {
            'user_id': user_id,
            'content': content,
            'datetime': datetime_str,
            'repeat_type': repeat_type,
            'notify_before': notify_before,
            'status': 'pending',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 插入資料庫
        reminder_id = db.execute_update(
            """
            INSERT INTO reminders 
            (user_id, content, datetime, repeat_type, notify_before, status, created_at) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                reminder_data['user_id'],
                reminder_data['content'],
                reminder_data['datetime'],
                reminder_data['repeat_type'],
                reminder_data['notify_before'],
                reminder_data['status'],
                reminder_data['created_at']
            )
        )
        
        # 設置提醒ID
        reminder_data['reminder_id'] = reminder_id
        
        return jsonify({
            "success": True,
            "message": "提醒已新增",
            "reminder": reminder_data
        })
    
    except Exception as e:
        return jsonify({"error": f"新增提醒失敗: {str(e)}"}), 500

# 更新提醒API
@app.route('/api/reminders/<int:reminder_id>', methods=['PUT'])
@login_required
def api_update_reminder(reminder_id):
    """更新提醒"""
    # 從會話中獲取用戶ID
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "未授權訪問"}), 401
    
    # 獲取請求數據
    data = request.json
    
    # 驗證必要字段
    if not data:
        return jsonify({"error": "無效的請求數據"}), 400
    
    # 檢查該提醒是否屬於該用戶
    db = DatabaseUtils()
    reminder = db.execute_query(
        "SELECT * FROM reminders WHERE reminder_id = ? AND user_id = ?", 
        (reminder_id, user_id),
        fetchall=False
    )
    
    if not reminder:
        return jsonify({"error": "提醒不存在或無權修改"}), 404
    
    # 獲取需要更新的字段
    updates = {}
    if 'content' in data:
        updates['content'] = data['content']
    if 'datetime' in data:
        updates['datetime'] = data['datetime']
    if 'repeat_type' in data:
        updates['repeat_type'] = data['repeat_type']
    if 'notify_before' in data:
        updates['notify_before'] = data['notify_before']
    if 'status' in data:
        updates['status'] = data['status']
    
    # 如果沒有需要更新的字段，返回錯誤
    if not updates:
        return jsonify({"error": "沒有需要更新的字段"}), 400
    
    # 更新提醒
    try:
        # 構建更新SQL
        update_fields = ', '.join([f"{field} = ?" for field in updates.keys()])
        update_values = list(updates.values())
        
        # 更新資料庫
        db.execute_update(
            f"UPDATE reminders SET {update_fields} WHERE reminder_id = ?",
            update_values + [reminder_id]
        )
        
        # 獲取更新後的提醒詳情
        updated_reminder = db.execute_query(
            "SELECT * FROM reminders WHERE reminder_id = ?", 
            (reminder_id,),
            fetchall=False
        )
        
        return jsonify({
            "success": True,
            "message": "提醒已更新",
            "reminder": updated_reminder
        })
    
    except Exception as e:
        return jsonify({"error": f"更新提醒失敗: {str(e)}"}), 500

# 刪除提醒API
@app.route('/api/reminders/<int:reminder_id>', methods=['DELETE'])
@login_required
def api_delete_reminder(reminder_id):
    """刪除提醒"""
    # 從會話中獲取用戶ID
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "未授權訪問"}), 401
    
    # 檢查該提醒是否屬於該用戶
    db = DatabaseUtils()
    reminder = db.execute_query(
        "SELECT * FROM reminders WHERE reminder_id = ? AND user_id = ?", 
        (reminder_id, user_id),
        fetchall=False
    )
    
    if not reminder:
        return jsonify({"error": "提醒不存在或無權刪除"}), 404
    
    # 刪除提醒
    try:
        db.execute_update("DELETE FROM reminders WHERE reminder_id = ?", (reminder_id,))
        
        return jsonify({
            "success": True,
            "message": "提醒已刪除"
        })
    
    except Exception as e:
        return jsonify({"error": f"刪除提醒失敗: {str(e)}"}), 500

# 完成提醒API
@app.route('/api/reminders/<int:reminder_id>/complete', methods=['POST'])
@login_required
def api_complete_reminder(reminder_id):
    """將提醒標記為已完成"""
    # 從會話中獲取用戶ID
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "未授權訪問"}), 401
    
    # 檢查該提醒是否屬於該用戶
    db = DatabaseUtils()
    reminder = db.execute_query(
        "SELECT * FROM reminders WHERE reminder_id = ? AND user_id = ?", 
        (reminder_id, user_id),
        fetchall=False
    )
    
    if not reminder:
        return jsonify({"error": "提醒不存在或無權修改"}), 404
    
    # 標記提醒為已完成
    try:
        db.execute_update(
            "UPDATE reminders SET status = 'completed', completed_at = ? WHERE reminder_id = ?",
            (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), reminder_id)
        )
        
        # 獲取更新後的提醒詳情
        updated_reminder = db.execute_query(
            "SELECT * FROM reminders WHERE reminder_id = ?", 
            (reminder_id,),
            fetchall=False
        )
        
        return jsonify({
            "success": True,
            "message": "提醒已標記為完成",
            "reminder": updated_reminder
        })
    
    except Exception as e:
        return jsonify({"error": f"標記提醒失敗: {str(e)}"}), 500

# 獲取月度收支摘要API
@app.route('/api/reports/monthly-summary', methods=['GET'])
@login_required
def api_get_monthly_summary():
    """獲取月度收支摘要"""
    # 從會話中獲取用戶ID
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "未授權訪問"}), 401
    
    # 獲取參數
    year = request.args.get('year', datetime.now().year)
    
    # 創建資料庫連接
    db = DatabaseUtils()
    
    # 獲取月度收支摘要
    monthly_summary = db.get_monthly_summary(user_id, year)
    
    return jsonify(monthly_summary)

# 獲取支出分類摘要API
@app.route('/api/reports/expense-summary', methods=['GET'])
@login_required
def api_get_expense_summary():
    """獲取支出分類摘要"""
    # 從會話中獲取用戶ID
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "未授權訪問"}), 401
    
    # 獲取參數
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # 如果沒有提供日期，默認使用本月
    if not start_date or not end_date:
        today = datetime.now()
        start_date = datetime(today.year, today.month, 1).strftime('%Y-%m-%d')
        last_day = calendar.monthrange(today.year, today.month)[1]
        end_date = datetime(today.year, today.month, last_day).strftime('%Y-%m-%d')
    
    # 創建資料庫連接
    db = DatabaseUtils()
    
    # 獲取支出分類摘要
    expense_summary = db.get_expense_summary_by_category(user_id, start_date, end_date)
    
    return jsonify(expense_summary)

# 獲取收入分類摘要API
@app.route('/api/reports/income-summary', methods=['GET'])
@login_required
def api_get_income_summary():
    """獲取收入分類摘要"""
    # 從會話中獲取用戶ID
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "未授權訪問"}), 401
    
    # 獲取參數
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # 如果沒有提供日期，默認使用本月
    if not start_date or not end_date:
        today = datetime.now()
        start_date = datetime(today.year, today.month, 1).strftime('%Y-%m-%d')
        last_day = calendar.monthrange(today.year, today.month)[1]
        end_date = datetime(today.year, today.month, last_day).strftime('%Y-%m-%d')
    
    # 創建資料庫連接
    db = DatabaseUtils()
    
    # 獲取收入分類摘要
    income_summary = db.get_income_summary_by_category(user_id, start_date, end_date)
    
    return jsonify(income_summary)

# 獲取每日收支摘要API
@app.route('/api/reports/daily-summary', methods=['GET'])
@login_required
def api_get_daily_summary():
    """獲取每日收支摘要"""
    # 從會話中獲取用戶ID
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "未授權訪問"}), 401
    
    # 獲取參數
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # 如果沒有提供日期，默認使用本月
    if not start_date or not end_date:
        today = datetime.now()
        start_date = datetime(today.year, today.month, 1).strftime('%Y-%m-%d')
        last_day = calendar.monthrange(today.year, today.month)[1]
        end_date = datetime(today.year, today.month, last_day).strftime('%Y-%m-%d')
    
    # 創建資料庫連接
    db = DatabaseUtils()
    
    # 獲取每日收支摘要
    daily_summary = db.get_daily_summary(user_id, start_date, end_date)
    
    return jsonify(daily_summary)

@app.route('/api/sync', methods=['POST'])
@login_required
def api_sync_data():
    """
    同步LINE和Web端數據的API端點
    
    這個API允許用戶在使用PWA時，將LINE和Web端的數據進行同步，
    確保用戶在兩個平台上看到的數據保持一致。
    
    Returns:
        json: 包含同步結果的JSON響應
    """
    try:
        # 獲取當前用戶ID
        user_id = session.get('user_id')
        
        # 執行數據同步
        db_utils = DatabaseUtils()
        sync_result = db_utils.sync_line_web_data(user_id)
        
        if not sync_result.get('success'):
            return jsonify({
                'success': False,
                'error': sync_result.get('error', '同步失敗，請稍後再試')
            }), 400
        
        # 返回同步結果
        return jsonify({
            'success': True,
            'message': '數據同步成功',
            'lastSyncTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'syncResults': {
                'accounts': sync_result.get('accounts', {}).get('message', ''),
                'categories': sync_result.get('categories', {}).get('message', ''),
                'transactions': sync_result.get('transactions', {}).get('message', ''),
                'reminders': sync_result.get('reminders', {}).get('message', '')
            }
        })
    except Exception as e:
        logger.error(f"Data sync failed: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'數據同步失敗: {str(e)}'
        }), 500

@app.route('/api/sync/status', methods=['GET'])
@login_required
def api_sync_status():
    """
    獲取數據同步狀態的API端點
    
    這個API允許用戶查詢最後一次數據同步的時間和狀態。
    
    Returns:
        json: 包含同步狀態的JSON響應
    """
    try:
        # 獲取當前用戶ID
        user_id = session.get('user_id')
        
        # 獲取用戶信息
        db_utils = DatabaseUtils()
        user = db_utils.get_user(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': '用戶不存在'
            }), 404
        
        # 獲取最後同步時間
        last_sync = user.get('last_sync')
        
        # 計算距離上次同步的時間
        time_since_last_sync = None
        if last_sync:
            try:
                last_sync_time = datetime.strptime(last_sync, '%Y-%m-%d %H:%M:%S')
                time_diff = datetime.now() - last_sync_time
                
                # 轉換為易讀格式
                if time_diff.days > 0:
                    time_since_last_sync = f"{time_diff.days}天前"
                elif time_diff.seconds // 3600 > 0:
                    time_since_last_sync = f"{time_diff.seconds // 3600}小時前"
                elif time_diff.seconds // 60 > 0:
                    time_since_last_sync = f"{time_diff.seconds // 60}分鐘前"
                else:
                    time_since_last_sync = "剛剛"
            except Exception as e:
                logger.error(f"Error parsing last sync time: {str(e)}")
                time_since_last_sync = "未知"
        
        return jsonify({
            'success': True,
            'lastSync': last_sync,
            'timeSinceLastSync': time_since_last_sync,
            'needsSync': not last_sync or (datetime.now() - datetime.strptime(last_sync, '%Y-%m-%d %H:%M:%S')).days >= 1
        })
    except Exception as e:
        logger.error(f"Get sync status failed: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'獲取同步狀態失敗: {str(e)}'
        }), 500 
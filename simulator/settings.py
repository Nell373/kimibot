import os
from dotenv import load_dotenv
import sys
from pathlib import Path

# 加載 .env 文件中的環境變數
load_dotenv()

# 項目根目錄
BASE_DIR = Path(__file__).resolve().parent.parent

# 基本設置
STATIC_DIR = os.path.join(BASE_DIR, 'static')
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')

# 服務器設置
HOST = os.environ.get('SIMULATOR_HOST', '127.0.0.1')
PORT = int(os.environ.get('SIMULATOR_PORT', 8000))
DEBUG = os.environ.get('SIMULATOR_DEBUG', 'True').lower() in ('true', '1', 't')

# LINE Bot 設置
CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', '')
CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', 'http://localhost:5000/api/webhook')

# 數據庫設置 - 使用應用的實際數據庫
DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///../database/bot.db')
TEST_DATABASE_URI = os.environ.get('TEST_DATABASE_URI', 'sqlite:///:memory:')

# PWA 設置
PWA_URL = os.environ.get('PWA_URL', 'http://localhost:5000')

# Flex Message 設定
MAX_FLEX_COLUMNS = 12
FLEX_PREVIEW_WIDTHS = {
    'mobile': 375,  # 手機寬度
    'tablet': 768,  # 平板寬度
    'desktop': 1024 # 桌面寬度
}

# 日誌設置
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
LOG_FILE = os.path.join(BASE_DIR, 'simulator.log')

# 性能分析設置
ENABLE_PROFILING = os.environ.get('ENABLE_PROFILING', 'False').lower() in ('true', '1', 't')
PROFILING_DIR = os.path.join(BASE_DIR, 'profiling')

# 用戶模擬設置
DEFAULT_USER_ID = 'simulator_user_001'  # 用於模擬用戶 ID
DEFAULT_USER_NAME = '測試用戶'           # 用於顯示的用戶名稱
DEFAULT_USER_PICTURE = os.path.join(STATIC_DIR, 'img', 'default_user.png')

# Flex Message 樣式 - 基於 LINE 實際樣式
FLEX_STYLES = {
    "primary_color": "#06c755",  # LINE 官方綠色
    "secondary_color": "#f5f5f5",
    "accent_color": "#2196F3",
    "text_color": "#333333",
    "link_color": "#06c755",
    "background_color": "#ffffff"
}

# 模擬器特殊功能配置
FEATURES = {
    'real_time_response': True,   # 是否啟用實時響應時間顯示
    'network_logging': True,      # 是否啟用網絡請求日誌
    'error_simulation': False,    # 是否啟用錯誤模擬功能
    'message_history': True,      # 是否保存消息歷史
    'flex_editor': True,          # 是否啟用 Flex Message 編輯器
    'responsive_preview': True,   # 是否啟用響應式預覽
    'data_explorer': True,        # 是否啟用數據瀏覽器
}

# 預設測試消息
DEFAULT_TEST_MESSAGES = [
    "你好",
    "午餐 -150",
    "今天晚上8點提醒我去健身",
    "查詢本月支出",
    "新增帳戶：現金",
    "收入 2000 薪資",
    "幫我查一下我的提醒事項"
]

# 模擬器相關設置
SIMULATOR_PORT = 5001
SIMULATOR_HOST = "127.0.0.1"

# LINE Bot 相關設置
LINE_BOT_API_URL = "http://localhost:5000/v2/bot"

# 用戶數據保存路徑
USER_DATA_DIR = os.path.join(BASE_DIR, "data", "users")

# 確保目錄存在
os.makedirs(USER_DATA_DIR, exist_ok=True) 
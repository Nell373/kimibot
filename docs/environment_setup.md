# LINE 智能記帳與提醒助手 - 環境建置指南

本指南將幫助你設置完整的開發環境，以便你能夠開發、測試和部署 LINE 智能記帳與提醒助手。

## 系統需求

- Python 3.8 或更高版本
- pip (Python 包管理器)
- Git
- 可選：Docker (用於容器化開發和測試)

## 開發環境設置

### 1. 複製代碼庫

```bash
# 複製代碼庫
git clone https://github.com/yourusername/linebot-assistant.git

# 進入項目目錄
cd linebot-assistant
```

### 2. 創建虛擬環境

```bash
# 創建虛擬環境
python -m venv venv

# 啟動虛擬環境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. 安裝依賴

```bash
# 安裝所有必要的依賴
pip install -r requirements.txt

# 安裝開發依賴 (可選)
pip install pytest pytest-cov flake8 black isort
```

### 4. 設置環境變數

```bash
# 複製環境變數範例文件
cp .env.example .env

# 使用你喜歡的編輯器修改 .env 文件
# 例如：
nano .env
```

在 `.env` 文件中，你需要填寫以下重要信息：

- `LINE_CHANNEL_SECRET`: 從 LINE Developers 控制台獲取
- `LINE_CHANNEL_ACCESS_TOKEN`: 從 LINE Developers 控制台獲取
- `WEBHOOK_URL`: 你的 Webhook URL (本地開發可使用 ngrok)
- `DATABASE_PATH`: 資料庫路徑 (預設: database/linebot.db)
- `CURSOR_API_KEY`: 若使用 Cursor API 進行增強語義分析

### 5. 初始化資料庫

```bash
# 初始化 SQLite 資料庫
python init_db.py
```

### 6. 啟動開發伺服器

```bash
# 設置為開發模式
export FLASK_ENV=development  # Linux/macOS
set FLASK_ENV=development     # Windows

# 啟動 Flask 伺服器
python webhook.py
```

## 測試

### 本地測試

項目包含兩種測試腳本：

1. 簡易測試 (無簽名驗證):

```bash
python test_webhook.py
```

2. 完整測試 (包含簽名驗證):

```bash
python test_webhook_with_signature.py
```

### 單元測試

```bash
# 運行所有測試
pytest

# 帶有覆蓋率報告
pytest --cov=./ --cov-report=term
```

## 外部服務設置

### LINE Developers 設置

1. 前往 [LINE Developers 控制台](https://developers.line.biz/)
2. 創建一個新的 Provider (如果沒有)
3. 創建一個新的 Messaging API Channel
4. 獲取 Channel Secret 和 Channel Access Token
5. 設置 Webhook URL (在部署後)

### 使用 ngrok 進行本地開發

對於本地開發，你可以使用 ngrok 創建一個臨時的公共 URL：

```bash
# 安裝 ngrok (如果沒有)
# 通過 https://ngrok.com/ 下載

# 啟動 ngrok
ngrok http 5000
```

然後更新你的 `.env` 文件和 LINE Developers 控制台中的 Webhook URL 為 ngrok 提供的 URL (例如 `https://your-ngrok-id.ngrok.io/api/webhook`).

## 部署

### 部署到 Fly.io

本項目配置了通過 GitHub Actions 自動部署到 Fly.io 的工作流程。

#### 手動部署

如果你想手動部署，請按照以下步驟操作：

1. 安裝 Fly CLI:

```bash
# 安裝 Fly CLI
curl -L https://fly.io/install.sh | sh

# 或者使用 Homebrew (macOS)
brew install flyctl
```

2. 登入到 Fly.io:

```bash
fly auth login
```

3. 初始化應用 (如果是第一次部署):

```bash
fly launch
```

4. 創建持久化卷 (如果是第一次部署):

```bash
fly volumes create line_bot_data --size 1
```

5. 部署應用:

```bash
fly deploy
```

## Docker 開發環境 (可選)

如果你喜歡使用 Docker 進行開發，可以使用以下命令：

### 構建 Docker 映像

```bash
docker build -t linebot-assistant .
```

### 運行 Docker 容器

```bash
docker run -p 5000:8080 \
  --env-file .env \
  -v $(pwd)/database:/app/database \
  linebot-assistant
```

## 常見問題

### LINE Webhook 驗證失敗

- 確保 Channel Secret 設置正確
- 確保 Webhook URL 設置正確，並以 `/api/webhook` 結尾
- 檢查你的伺服器是否正確回應 HTTP 200 OK

### 資料庫錯誤

- 確保 `database` 目錄存在且可寫
- 如果資料庫架構有更改，嘗試重新初始化：`python init_db.py`

### 部署問題

- 確保 GitHub Actions 的 Secrets 已正確設置 (`FLY_API_TOKEN`)
- 檢查 Fly.io 的日誌：`fly logs`

## 其他資源

- [LINE Messaging API 文檔](https://developers.line.biz/en/docs/messaging-api/)
- [Flask 文檔](https://flask.palletsprojects.com/)
- [Fly.io 文檔](https://fly.io/docs/)
- [Python SQLite 文檔](https://docs.python.org/3/library/sqlite3.html)

## 聯繫幫助

如有任何環境建置問題，請通過 GitHub Issues 提出，或者聯繫項目維護者尋求協助。 
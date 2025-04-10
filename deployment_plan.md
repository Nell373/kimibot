# LINE 智能記帳與提醒助手 - Fly.io 部署計劃

## 選擇 Fly.io 的優勢

1. **全球分佈式部署**：Fly.io 提供全球邊緣網絡，可在離用戶最近的數據中心部署應用
2. **容器化部署**：基於 Docker 的簡易部署流程
3. **自動 HTTPS**：免費自動配置和管理 SSL 證書
4. **簡單擴展**：可根據流量快速擴展
5. **便宜的入門價格**：提供免費額度和合理的付費方案

## 部署準備工作

### 1. Fly.io 帳號設置

- [ ] 註冊 Fly.io 帳號
- [ ] 設置計費信息（即使使用免費額度也需要）
- [ ] 安裝 Flyctl CLI 工具
  ```bash
  curl -L https://fly.io/install.sh | sh
  ```
- [ ] 登入 Fly.io
  ```bash
  flyctl auth login
  ```

### 2. 專案適配

- [ ] 確保專案結構符合 Fly.io 要求
- [ ] 建立 Dockerfile
- [ ] 建立 fly.toml 配置文件
- [ ] 配置環境變數

### 3. 資料庫規劃

- [ ] 評估是否使用 Fly Postgres 或外部數據庫
- [ ] 設置資料庫備份策略
- [ ] 設定持久化存儲卷

## 部署配置文件

### Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴文件
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案文件
COPY . .

# 確保資料庫目錄存在
RUN mkdir -p database

# 初始化資料庫
RUN python init_db.py

# 暴露端口
EXPOSE 8080

# 設置啟動命令
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "webhook:app"]
```

### fly.toml

```toml
app = "line-finance-assistant"
primary_region = "nrt"  # Tokyo region
kill_signal = "SIGINT"
kill_timeout = 5

[env]
  PORT = "8080"
  PYTHONUNBUFFERED = "1"

[experimental]
  allowed_public_ports = []
  auto_rollback = true

[mounts]
  source = "line_bot_data"
  destination = "/app/database"

[[services]]
  http_checks = []
  internal_port = 8080
  protocol = "tcp"
  script_checks = []
  
  [services.concurrency]
    hard_limit = 25
    soft_limit = 20
    type = "connections"

  [[services.ports]]
    force_https = true
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443

  [[services.tcp_checks]]
    grace_period = "1s"
    interval = "15s"
    restart_limit = 0
    timeout = "2s"
```

## 部署流程

### 1. 初始部署

```bash
# 在專案目錄下初始化 Fly 應用
flyctl launch --name line-finance-assistant

# 建立持久化存儲卷
flyctl volumes create line_bot_data --size 1 --region nrt

# 設置環境變數
flyctl secrets set LINE_CHANNEL_SECRET=你的密鑰
flyctl secrets set LINE_CHANNEL_ACCESS_TOKEN=你的訪問令牌
flyctl secrets set CURSOR_API_KEY=你的Cursor_API金鑰

# 部署應用
flyctl deploy
```

### 2. 配置自定義域名 (選擇性)

```bash
# 添加自定義域名
flyctl certs create your-domain.com

# 在你的 DNS 提供商處設置相應的 CNAME 記錄
```

### 3. 擴展與監控

```bash
# 查看應用日誌
flyctl logs

# 擴展應用資源
flyctl scale vm dedicated-cpu-1x

# 擴展應用實例數量
flyctl scale count 2
```

### 4. 後續更新部署

```bash
# 準備應用更新
git pull  # 如果從遠程倉庫拉取更新

# 編輯已存在的 fly.toml 或 Dockerfile（如需要）

# 重新部署應用
flyctl deploy
```

### 5. 回滾部署（如果有問題）

```bash
# 查看部署歷史
flyctl releases

# 回滾到指定版本
flyctl deploy --release v123
```

## 備份策略

### 自動資料庫備份

```bash
# 設置每日備份 cron 任務
flyctl ssh console -C "echo '0 0 * * * sqlite3 /app/database/linebot.db .dump > /app/database/backup-\$(date +\%Y\%m\%d).sql' | crontab -"
```

### 備份檔案同步到 S3 或其他存儲

```bash
# 安裝 AWS CLI
flyctl ssh console -C "apt-get update && apt-get install -y awscli"

# 設置定期同步備份到 S3
flyctl ssh console -C "echo '0 1 * * * aws s3 cp /app/database/backup-\$(date +\%Y\%m\%d).sql s3://your-bucket/backups/' | crontab -"
```

## 監控與警報

### 設置 Uptime 監控

```bash
# 安裝 uptimerobot-cli
npm install -g uptimerobot-cli

# 添加監控
uptimerobot-cli add-monitor --name "LINE Bot API" --url "https://your-domain.com/api/webhook"
```

### 設置 Slack 通知

```bash
# 配置 Slack Webhook URL
flyctl secrets set SLACK_WEBHOOK_URL=你的Slack_Webhook_URL
```

## 災難恢復計劃

1. **資料庫損壞恢復**
   ```bash
   # 從最新備份恢復資料庫
   flyctl ssh console -C "sqlite3 /app/database/linebot.db < /app/database/backup-最新日期.sql"
   ```

2. **應用程式回滾**
   ```bash
   # 回滾到上一個成功版本
   flyctl deploy --image registry.fly.io/line-finance-assistant:上一個版本
   ```

3. **完全重建**
   ```bash
   # 在新區域重建應用
   flyctl regions add hkg  # 添加香港區域作為備份
   ```

## 部署檢查清單

- [ ] 確保所有環境變數已設置
- [ ] 確保資料庫初始化腳本無錯誤
- [ ] 測試 LINE Webhook 連通性
- [ ] 檢查 HTTPS 證書有效性
- [ ] 驗證持久化存儲正常工作
- [ ] 檢查備份功能運行正常
- [ ] 監控系統檢查
- [ ] 負載測試檢查 
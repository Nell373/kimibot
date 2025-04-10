# LINE 智能記帳與提醒助手 - 專案架構說明

## 📂 目錄結構

```
linebot-assistant/
├── webhook.py                # LINE Webhook 處理程式
├── test_webhook.py           # 簡易測試腳本
├── test_webhook_with_signature.py # 完整測試腳本（含簽名驗證）
├── .env.example              # 環境變數範例
├── init_db.py                # 資料庫初始化腳本
├── Dockerfile                # Docker 容器配置
├── fly.toml                  # Fly.io 部署設定
├── requirements.txt          # Python 依賴
├── handlers/                 # 訊息處理器
│   ├── __init__.py
│   └── message_handler.py    # LINE 訊息處理器
├── parsers/                  # 文本解析器
│   ├── __init__.py
│   └── text_parser.py        # 基於規則的簡單文本解析器
├── database/                 # 資料庫相關
│   ├── db_utils.py           # 資料庫工具類
│   └── schema.sql            # 資料庫結構
├── static/                   # PWA 前端頁面
│   ├── assets/               # 靜態資源
│   ├── css/                  # 樣式文件
│   ├── js/                   # JavaScript 文件
│   ├── templates/            # HTML 模板
│   ├── manifest.json         # PWA 配置
│   └── sw.js                 # Service Worker
├── project_roadmap.md        # 專案進度規劃
├── project_architecture.md   # 專案架構說明
└── README.md                 # 專案說明文件
```

## 🏗️ 模塊設計

專案採用模塊化設計，將不同功能拆分為獨立的模塊，便於開發、測試和維護：

### 1. 核心模塊 (webhook.py)

核心模塊是整個應用的入口點，負責：
- 初始化 Flask 應用和 LINE Bot API
- 提供 webhook 端點接收 LINE 平台的事件
- 處理簽名驗證和安全檢查
- 協調其他模塊提供具體功能

### 2. 訊息處理模塊 (handlers/)

訊息處理模塊負責處理從 LINE 平台接收的各種事件和訊息：
- `message_handler.py`：處理用戶發送的文字訊息和選擇回調
- 根據訊息類型分發到相應的處理函數
- 生成並發送回覆訊息（純文字或 Flex Message）

### 3. 文本解析模塊 (parsers/)

文本解析模塊負責理解用戶輸入的簡單命令，並轉換為結構化數據：
- `text_parser.py`：基於規則的解析器，支援記帳、提醒和查詢操作的基本解析
- 採用簡單明確的規則，不使用複雜的AI算法

### 4. 資料庫模塊 (database/)

資料庫模塊負責資料的持久化儲存和檢索：
- `db_utils.py`：提供資料庫操作的便捷方法，如用戶管理、記帳、提醒等
- `schema.sql`：定義資料庫結構，包括表和索引

### 5. 前端模塊 (static/)

前端模塊提供 PWA 網頁應用，用於查看報表和管理數據：
- HTML模板：用於渲染頁面
- CSS樣式：定義頁面外觀
- JavaScript：提供頁面互動功能
- Service Worker：支援離線訪問和快取

## 🔄 流程說明

1. **訊息接收流程**：
   - 用戶發送訊息到 LINE Bot
   - LINE 平台將訊息轉發到我們的 webhook 端點
   - webhook.py 驗證簽名並確認用戶存在
   - 調用 MessageHandler 處理訊息

2. **訊息處理流程**：
   - MessageHandler 接收訊息
   - 使用 TextParser 解析文本內容
   - 根據解析結果決定操作類型（記帳/提醒/查詢）
   - 執行相應的處理邏輯
   - 使用 DatabaseUtils 操作資料庫
   - 生成回覆訊息並發送給用戶

3. **記帳操作流程**：
   - 解析用戶輸入的基本信息（如金額、項目）
   - 發送 Flex Message 讓用戶選擇分類和帳戶
   - 用戶選擇後，接收 Postback 事件
   - 將記帳資訊儲存到資料庫
   - 發送確認訊息

4. **提醒操作流程**：
   - 解析提醒基本信息（時間和內容）
   - 發送 Flex Message 讓用戶設置提醒細節（如重複方式）
   - 將提醒資訊儲存到資料庫
   - 發送確認訊息
   - 到達指定時間時，發送提醒通知

5. **查詢操作流程**：
   - 提供預設查詢選項的 Flex Message
   - 用戶選擇查詢類型和時間範圍
   - 從資料庫檢索相關數據
   - 生成報表訊息
   - 發送給用戶

## 🛠️ 技術選型

### 後端技術

- **Python 3.x**：主要開發語言
- **Flask**：輕量級 Web 框架，用於提供 API 端點
- **LINE Messaging API**：與 LINE 平台交互
- **SQLite**：輕量級關聯式資料庫
- **正則表達式**：用於基本文本解析

### 前端技術

- **HTML5 / CSS3 / JavaScript**：基本前端技術
- **PWA (Progressive Web App)**：提供類原生應用體驗
- **Chart.js**：用於生成視覺化圖表
- **Service Worker**：支援離線功能

### 部署技術

- **Docker**：容器化應用
- **Fly.io**：雲端部署平台
- **環境變數**：用於配置管理

## 📊 資料庫設計

資料庫採用 SQLite，包含以下主要表：

### 1. users 表
- 用戶基本資訊
- 主鍵：user_id (來自 LINE)

### 2. accounts 表
- 儲存用戶的帳戶資訊
- 外鍵關聯到 users 表

### 3. categories 表
- 儲存支出和收入的分類
- 包括預設分類和用戶自定義分類

### 4. transactions 表
- 儲存交易記錄（支出和收入）
- 外鍵關聯到 users, accounts, categories

### 5. reminders 表
- 儲存提醒事項
- 支援重複提醒設置

## 🔒 安全性設計

- **簽名驗證**：使用 X-Line-Signature 驗證請求來源
- **環境變數**：敏感資訊如 API 密鑰存放在環境變數中
- **錯誤處理**：所有操作包含適當的錯誤處理和日誌記錄
- **資料驗證**：輸入數據進行檢查，防止注入攻擊

## 🧪 測試策略

- **單元測試**：測試各個模塊的功能
- **整合測試**：測試模塊間的交互
- **本地測試腳本**：
  - `test_webhook.py`：開發環境中簡單測試
  - `test_webhook_with_signature.py`：包含簽名驗證的完整測試 
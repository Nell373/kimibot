# LINE 智能記帳與提醒助手 - 模擬環境

這個模擬環境提供了一個完整的開發和測試平台，讓開發者可以在本地環境中模擬用戶與 LINE Bot 和 PWA 應用的互動。通過這個環境，您可以預覽和測試所有功能，而無需部署到實際的 LINE 平台。

## 特點

- **LINE 聊天模擬器**：模擬 LINE 應用程式界面，可發送消息並顯示回覆
- **Flex Message 預覽**：實時展示 Flex Message 的渲染效果
- **PWA 整合**：可同時測試 PWA 網頁應用的功能
- **數據同步測試**：測試 LINE 和 Web 端的數據同步功能
- **響應速度分析**：提供 Bot 響應時間的分析工具
- **錯誤日誌**：詳細記錄交互過程中的錯誤

## 使用方法

### 安裝依賴

```bash
pip install -r simulator/requirements.txt
```

### 啟動模擬環境

```bash
python simulator/run.py
```

啟動後，模擬環境將在本地運行一個網頁服務，默認地址為 `http://localhost:8000`。

### 可用功能

1. **LINE 聊天模擬**
   - 發送文本消息
   - 查看 Bot 回覆
   - 與 Flex Message 互動

2. **PWA 測試**
   - 無縫切換到 PWA 界面
   - 測試 PWA 功能
   - 檢查數據同步

3. **開發工具**
   - 網絡請求查看器
   - 響應時間分析
   - 錯誤診斷
   - 數據庫狀態檢查

## 目錄結構

```
simulator/
├── README.md                # 本文檔
├── requirements.txt         # 依賴列表
├── run.py                   # 主啟動腳本
├── settings.py              # 配置文件
├── static/                  # 靜態資源
│   ├── css/                 # 樣式文件
│   ├── js/                  # JavaScript 文件
│   └── img/                 # 圖像資源
├── templates/               # HTML 模板
│   ├── index.html           # 主頁
│   ├── line_simulator.html  # LINE 模擬器
│   └── pwa_preview.html     # PWA 預覽
└── core/                    # 核心模擬邏輯
    ├── line_simulator.py    # LINE 模擬器實現
    ├── message_handler.py   # 消息處理
    ├── flex_renderer.py     # Flex Message 渲染
    └── data_sync.py         # 數據同步模擬
```

## 開發筆記

### LINE 模擬器實現原理

LINE 模擬器通過模擬 LINE Messaging API 的請求和響應，實現對 Bot 功能的測試。當用戶在模擬器中發送消息時，系統會：

1. 構建符合 LINE Messaging API 格式的請求
2. 生成有效的請求簽名
3. 發送請求到 Bot 的 Webhook 端點
4. 接收 Bot 的響應
5. 解析並在界面上顯示響應內容

### Flex Message 渲染

Flex Message 渲染使用與 LINE 應用相同的渲染規則，確保在模擬環境中看到的效果與實際 LINE 應用中一致。

### 數據同步測試

模擬環境提供了一個專門的界面，用於測試 LINE 和 Web 端之間的數據同步功能。可以在此界面中檢查同步狀態、觸發同步操作，並查看同步結果。

## 注意事項

1. 模擬環境僅用於開發和測試，不應在生產環境中使用
2. 模擬環境中的部分功能可能與實際 LINE 平台有細微差異
3. 使用之前請確保 `.env` 文件中的配置正確
4. 使用模擬環境發送的消息不會影響真實用戶數據 
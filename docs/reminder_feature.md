# 提醒功能說明文件

## 功能概述

提醒功能是 LINE 智能記帳與提醒助手的核心功能之一，允許用戶通過簡單的自然語言指令創建、查看、完成和刪除提醒。系統支持一次性提醒和定期重複提醒，還提供提前通知功能。

## 使用說明

### 創建提醒

用戶可以使用多種格式創建提醒：

1. **簡單格式**：`提醒 [內容] [時間]`
   - 例如：`提醒 明天早上9點開會`
   - 例如：`提醒我 3/15 下午3點看牙醫`

2. **詳細格式**：`# [日期] [時間] [內容] [提前提醒時間] [重複頻率]`
   - 例如：`# 明天 早上9點 開會 提前15分鐘提醒`
   - 例如：`# 每週一 下午2點 團隊會議 提前30分鐘提醒`

### 支持的時間格式

系統可識別多種時間格式：

- **相對時間**：`今天`、`明天`、`後天`、`3天後`、`下週一`等
- **絕對日期**：`3/15`、`2023-03-15`等
- **時間點**：`早上9點`、`下午3:30`、`19:00`等
- **快速時間**：`30分鐘後`、`2小時後`等

### 重複提醒

可以設置多種重複頻率：

- **每天重複**：`每天早上8點跑步`
- **每週重複**：`每週一下午2點開會`
- **每月重複**：`每月1號查看月報`

### 提前提醒

可以指定提前多久發送提醒通知：

- `提前15分鐘提醒`
- `提前1小時提醒`
- `提前1天提醒`

預設為提前15分鐘提醒。

## 提醒管理

### 查看提醒列表

輸入 `查看提醒` 或 `我的提醒` 可獲取當前所有未完成的提醒列表。

### 完成提醒

在提醒列表中，點擊 `完成` 按鈕可標記提醒為已完成。

### 刪除提醒

在提醒列表中，點擊 `刪除` 按鈕可移除不需要的提醒。

## 技術實現

提醒功能的實現由以下組件構成：

1. **文本解析器**：`parsers/text_parser.py` 解析用戶輸入，提取提醒內容、時間和其他屬性。

2. **提醒處理器**：`handlers/message_handler.py` 接收解析結果，處理提醒的創建、查看、完成和刪除。

3. **數據庫組件**：`database/db_utils.py` 提供提醒的存儲和檢索功能。

4. **提醒排程器**：`scheduler/reminder_scheduler.py` 定期檢查並發送即將到期的提醒通知。

### 數據模型

提醒在數據庫中的存儲結構：

```sql
CREATE TABLE reminders (
    reminder_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(50),                    -- 所屬用戶 ID
    title VARCHAR(100) NOT NULL,            -- 提醒標題
    description TEXT,                       -- 提醒描述
    due_date TIMESTAMP NOT NULL,            -- 到期時間
    remind_before INTEGER DEFAULT 30,       -- 提前提醒時間（分鐘）
    repeat_type VARCHAR(20),                -- 重複類型：daily/weekly/monthly/yearly
    repeat_value VARCHAR(50),               -- 重複值（如：每週一）
    is_completed BOOLEAN DEFAULT FALSE,     -- 是否完成
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

## 提醒流程

1. 用戶發送提醒命令
2. 文本解析器識別命令並提取關鍵信息
3. 提醒處理器創建提醒並存儲到數據庫
4. 系統確認提醒已創建，並顯示提醒詳情
5. 提醒排程器定期檢查即將到期的提醒
6. 到達提醒時間時，系統發送通知給用戶
7. 用戶可以選擇完成或延後提醒

## 未來計劃

計劃中的提醒功能改進：

1. 地點提醒：結合位置信息的提醒（例如：`到超市時提醒我買牛奶`）
2. 智能提醒：基於用戶習慣的自動提醒建議
3. 提醒分類：按類型組織不同的提醒
4. 提醒優先級：支持高、中、低不同優先級
5. 分享提醒：將提醒分享給其他用戶 
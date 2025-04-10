-- 用戶資料表
CREATE TABLE users (
    user_id VARCHAR(50) PRIMARY KEY,        -- LINE 用戶 ID
    display_name VARCHAR(100),              -- 用戶顯示名稱
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 分類資料表
CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(50),                    -- 所屬用戶 ID
    name VARCHAR(50) NOT NULL,              -- 分類名稱
    type VARCHAR(10) NOT NULL,              -- 類型：expense/income
    icon VARCHAR(20),                       -- 分類圖示
    is_default BOOLEAN DEFAULT FALSE,       -- 是否為預設分類
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 帳戶資料表
CREATE TABLE accounts (
    account_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(50),                    -- 所屬用戶 ID
    name VARCHAR(50) NOT NULL,              -- 帳戶名稱
    balance DECIMAL(10,2) DEFAULT 0.00,     -- 帳戶餘額
    is_default BOOLEAN DEFAULT FALSE,       -- 是否為預設帳戶
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 記帳資料表
CREATE TABLE transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(50),                    -- 所屬用戶 ID
    account_id INTEGER,                     -- 帳戶 ID
    category_id INTEGER,                    -- 分類 ID
    type VARCHAR(10) NOT NULL,              -- 類型：expense/income
    amount DECIMAL(10,2) NOT NULL,          -- 金額
    description TEXT,                       -- 描述
    date DATE NOT NULL,                     -- 交易日期
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
);

-- 提醒資料表
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

-- 建立索引
CREATE INDEX idx_transactions_user_date ON transactions(user_id, date);
CREATE INDEX idx_reminders_user_due ON reminders(user_id, due_date);
CREATE INDEX idx_categories_user_type ON categories(user_id, type);
CREATE INDEX idx_accounts_user ON accounts(user_id);

-- 建立觸發器（更新時間戳）
CREATE TRIGGER update_users_timestamp 
AFTER UPDATE ON users
BEGIN
    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE user_id = NEW.user_id;
END;

CREATE TRIGGER update_categories_timestamp 
AFTER UPDATE ON categories
BEGIN
    UPDATE categories SET updated_at = CURRENT_TIMESTAMP WHERE category_id = NEW.category_id;
END;

CREATE TRIGGER update_accounts_timestamp 
AFTER UPDATE ON accounts
BEGIN
    UPDATE accounts SET updated_at = CURRENT_TIMESTAMP WHERE account_id = NEW.account_id;
END;

CREATE TRIGGER update_transactions_timestamp 
AFTER UPDATE ON transactions
BEGIN
    UPDATE transactions SET updated_at = CURRENT_TIMESTAMP WHERE transaction_id = NEW.transaction_id;
END;

CREATE TRIGGER update_reminders_timestamp 
AFTER UPDATE ON reminders
BEGIN
    UPDATE reminders SET updated_at = CURRENT_TIMESTAMP WHERE reminder_id = NEW.reminder_id;
END; 
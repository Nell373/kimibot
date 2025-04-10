import sqlite3
import os
import datetime

# 確保資料庫目錄存在
if not os.path.exists('database'):
    os.makedirs('database')

# 資料庫檔案路徑
DB_PATH = 'database/linebot.db'

# 初始化資料庫
def init_db():
    # 檢查資料庫是否已存在
    is_new_db = not os.path.exists(DB_PATH)
    
    # 連接資料庫
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 讀取 schema.sql 檔案
    with open('database/schema.sql', 'r') as f:
        schema = f.read()
    
    # 建立資料表
    cursor.executescript(schema)
    
    # 如果是新資料庫，插入預設資料
    if is_new_db:
        insert_default_data(cursor)
    
    # 提交變更
    conn.commit()
    conn.close()
    
    print(f"資料庫初始化完成。路徑：{DB_PATH}")

# 插入預設資料
def insert_default_data(cursor):
    # 預設支出分類
    expense_categories = [
        ('飲食', 'expense', '🍱'),
        ('交通', 'expense', '🚗'),
        ('購物', 'expense', '🛒'),
        ('娛樂', 'expense', '🎮'),
        ('醫療', 'expense', '🏥'),
        ('住宿', 'expense', '🏠'),
        ('教育', 'expense', '📚'),
        ('其他支出', 'expense', '💸')
    ]
    
    # 預設收入分類
    income_categories = [
        ('薪資', 'income', '💰'),
        ('獎金', 'income', '🎁'),
        ('投資', 'income', '📈'),
        ('其他收入', 'income', '💵')
    ]
    
    # 插入預設支出分類
    for name, type_name, icon in expense_categories:
        cursor.execute(
            'INSERT INTO categories (name, type, icon, is_default) VALUES (?, ?, ?, ?)',
            (name, type_name, icon, True)
        )
    
    # 插入預設收入分類
    for name, type_name, icon in income_categories:
        cursor.execute(
            'INSERT INTO categories (name, type, icon, is_default) VALUES (?, ?, ?, ?)',
            (name, type_name, icon, True)
        )
    
    # 插入預設帳戶
    cursor.execute(
        'INSERT INTO accounts (name, is_default) VALUES (?, ?)',
        ('現金', True)
    )
    
    print("已插入預設分類與帳戶資料")

# 主程式
if __name__ == "__main__":
    init_db() 
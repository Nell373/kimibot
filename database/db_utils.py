import sqlite3
import os
from datetime import datetime, date, timedelta

class DatabaseUtils:
    """資料庫操作工具類"""
    
    def __init__(self, db_path='database/linebot.db'):
        """初始化資料庫連接"""
        self.db_path = db_path
        
    def get_connection(self):
        """獲取資料庫連接"""
        conn = sqlite3.connect(self.db_path)
        # 設定 row_factory 讓查詢結果以字典形式返回
        conn.row_factory = sqlite3.Row
        return conn
    
    def execute_query(self, query, params=(), fetchall=True):
        """執行查詢"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            if fetchall:
                result = [dict(row) for row in cursor.fetchall()]
            else:
                result = dict(cursor.fetchone()) if cursor.fetchone() else None
            return result
        finally:
            conn.close()
    
    def execute_update(self, query, params=()):
        """執行更新操作"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()
    
    def execute_many(self, query, params_list):
        """執行批量操作"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()
    
    # 用戶相關方法
    def get_user(self, user_id):
        """獲取用戶資訊"""
        query = "SELECT * FROM users WHERE user_id = ?"
        return self.execute_query(query, (user_id,), fetchall=False)
    
    def create_user(self, user_id, display_name):
        """創建新用戶"""
        query = "INSERT INTO users (user_id, display_name) VALUES (?, ?)"
        return self.execute_update(query, (user_id, display_name))
    
    def update_user(self, user_id, display_name):
        """更新用戶資訊"""
        query = "UPDATE users SET display_name = ? WHERE user_id = ?"
        return self.execute_update(query, (display_name, user_id))
    
    # 記帳相關方法
    def add_transaction(self, user_id, account_id, category_id, type_name, amount, description, trans_date=None):
        """新增交易記錄"""
        if trans_date is None:
            trans_date = date.today().isoformat()
        
        query = """
            INSERT INTO transactions 
            (user_id, account_id, category_id, type, amount, description, date) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        transaction_id = self.execute_update(
            query, 
            (user_id, account_id, category_id, type_name, amount, description, trans_date)
        )
        
        # 更新帳戶餘額
        if type_name == 'income':
            self.update_account_balance(account_id, amount)
        else:
            self.update_account_balance(account_id, -amount)
            
        return transaction_id
    
    def get_transactions(self, user_id, start_date=None, end_date=None, type_name=None, category_id=None, limit=50):
        """獲取交易記錄"""
        query = """
            SELECT t.*, c.name as category_name, c.icon as category_icon, a.name as account_name
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.category_id
            LEFT JOIN accounts a ON t.account_id = a.account_id
            WHERE t.user_id = ?
        """
        
        params = [user_id]
        
        if start_date:
            query += " AND t.date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND t.date <= ?"
            params.append(end_date)
        
        if type_name:
            query += " AND t.type = ?"
            params.append(type_name)
        
        if category_id:
            query += " AND t.category_id = ?"
            params.append(category_id)
        
        query += " ORDER BY t.date DESC, t.created_at DESC LIMIT ?"
        params.append(limit)
        
        return self.execute_query(query, tuple(params))
    
    # 分類相關方法
    def get_categories(self, user_id, type_name=None):
        """獲取分類列表"""
        query = """
            SELECT * FROM categories 
            WHERE (user_id IS NULL OR user_id = ?)
        """
        
        params = [user_id]
        
        if type_name:
            query += " AND type = ?"
            params.append(type_name)
        
        query += " ORDER BY is_default DESC, name ASC"
        
        return self.execute_query(query, tuple(params))
    
    def get_category_by_name(self, user_id, name, type_name=None):
        """根據名稱獲取分類"""
        query = """
            SELECT * FROM categories 
            WHERE (user_id IS NULL OR user_id = ?) AND name = ?
        """
        
        params = [user_id, name]
        
        if type_name:
            query += " AND type = ?"
            params.append(type_name)
        
        return self.execute_query(query, tuple(params), fetchall=False)
    
    def add_category(self, user_id, name, type_name, icon=''):
        """新增分類"""
        query = """
            INSERT INTO categories 
            (user_id, name, type, icon, is_default) 
            VALUES (?, ?, ?, ?, 0)
        """
        return self.execute_update(query, (user_id, name, type_name, icon))
    
    # 帳戶相關方法
    def get_accounts(self, user_id):
        """獲取帳戶列表"""
        query = """
            SELECT * FROM accounts 
            WHERE (user_id IS NULL OR user_id = ?)
            ORDER BY is_default DESC, name ASC
        """
        return self.execute_query(query, (user_id,))
    
    def get_default_account(self, user_id):
        """獲取預設帳戶"""
        query = """
            SELECT * FROM accounts 
            WHERE (user_id IS NULL OR user_id = ?) AND is_default = 1
            LIMIT 1
        """
        return self.execute_query(query, (user_id,), fetchall=False)
    
    def add_account(self, user_id, name, balance=0.0, is_default=False):
        """新增帳戶"""
        query = """
            INSERT INTO accounts (user_id, name, balance, is_default) 
            VALUES (?, ?, ?, ?)
        """
        return self.execute_update(query, (user_id, name, balance, is_default))
    
    def update_account_balance(self, account_id, amount_change):
        """更新帳戶餘額
        
        Args:
            account_id: 帳戶ID
            amount_change: 金額變化（正數為增加，負數為減少）
        """
        if not account_id:
            return
        
        # 先獲取當前餘額
        account = self.execute_query(
            "SELECT balance FROM accounts WHERE account_id = ?",
            (account_id,),
            fetchall=False
        )
        
        if not account:
            return
        
        current_balance = account.get('balance', 0)
        new_balance = current_balance + amount_change
        
        # 更新餘額
        self.execute_update(
            "UPDATE accounts SET balance = ? WHERE account_id = ?",
            (new_balance, account_id)
        )
        
        return new_balance
    
    # 提醒相關方法
    def add_reminder(self, user_id, title, due_date, description=None, remind_before=30, repeat_type=None, repeat_value=None):
        """新增提醒"""
        query = """
            INSERT INTO reminders 
            (user_id, title, description, due_date, remind_before, repeat_type, repeat_value) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        return self.execute_update(
            query, 
            (user_id, title, description, due_date, remind_before, repeat_type, repeat_value)
        )
    
    def get_reminders(self, user_id, is_completed=False, limit=50):
        """獲取提醒列表"""
        query = """
            SELECT * FROM reminders 
            WHERE user_id = ? AND is_completed = ?
            ORDER BY due_date ASC
            LIMIT ?
        """
        return self.execute_query(query, (user_id, is_completed, limit))
    
    def get_reminder(self, reminder_id):
        """獲取單個提醒詳細信息"""
        query = """
            SELECT * FROM reminders 
            WHERE reminder_id = ?
            LIMIT 1
        """
        return self.execute_query(query, (reminder_id,), fetchall=False)
    
    def get_upcoming_reminders(self, user_id, hours_ahead=24):
        """獲取即將到期的提醒"""
        query = """
            SELECT * FROM reminders 
            WHERE user_id = ? 
              AND is_completed = 0
              AND due_date <= datetime('now', '+' || ? || ' hours')
            ORDER BY due_date ASC
        """
        return self.execute_query(query, (user_id, hours_ahead))
    
    def complete_reminder(self, reminder_id, user_id):
        """完成提醒"""
        query = """
            UPDATE reminders 
            SET is_completed = 1 
            WHERE reminder_id = ? AND user_id = ?
        """
        return self.execute_update(query, (reminder_id, user_id))
    
    def update_reminder_status(self, reminder_id, is_completed):
        """更新提醒狀態"""
        query = """
            UPDATE reminders 
            SET is_completed = ? 
            WHERE reminder_id = ?
        """
        return self.execute_update(query, (is_completed, reminder_id))
        
    def delete_reminder(self, reminder_id):
        """刪除提醒"""
        query = """
            DELETE FROM reminders 
            WHERE reminder_id = ?
        """
        return self.execute_update(query, (reminder_id,))
    
    # 統計報表相關方法
    def get_expense_summary_by_category(self, user_id, start_date, end_date):
        """
        獲取指定日期範圍內的支出分類摘要
        
        Args:
            user_id: 用戶ID
            start_date: 開始日期
            end_date: 結束日期
            
        Returns:
            list: 支出分類摘要列表
        """
        query = """
        SELECT 
            c.category_id,
            c.name as category_name,
            c.icon as category_icon,
            SUM(t.amount) as total_amount,
            COUNT(t.transaction_id) as transaction_count
        FROM transactions t
        JOIN categories c ON t.category_id = c.category_id
        WHERE t.user_id = ? 
          AND t.type = 'expense'
          AND t.date BETWEEN ? AND ?
        GROUP BY t.category_id
        ORDER BY total_amount DESC
        """
        
        results = self.execute_query(query, (user_id, start_date, end_date), fetchall=True)
        return results
    
    def get_income_summary_by_category(self, user_id, start_date, end_date):
        """
        獲取指定日期範圍內的收入分類摘要
        
        Args:
            user_id: 用戶ID
            start_date: 開始日期
            end_date: 結束日期
            
        Returns:
            list: 收入分類摘要列表
        """
        query = """
        SELECT 
            c.category_id,
            c.name as category_name,
            c.icon as category_icon,
            SUM(t.amount) as total_amount,
            COUNT(t.transaction_id) as transaction_count
        FROM transactions t
        JOIN categories c ON t.category_id = c.category_id
        WHERE t.user_id = ? 
          AND t.type = 'income'
          AND t.date BETWEEN ? AND ?
        GROUP BY t.category_id
        ORDER BY total_amount DESC
        """
        
        results = self.execute_query(query, (user_id, start_date, end_date), fetchall=True)
        return results
    
    def get_daily_summary(self, user_id, start_date, end_date):
        """
        獲取指定日期範圍內的每日收支摘要
        
        Args:
            user_id: 用戶ID
            start_date: 開始日期
            end_date: 結束日期
            
        Returns:
            list: 每日收支摘要列表
        """
        query = """
        SELECT 
            date,
            SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as total_income,
            SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as total_expense,
            SUM(CASE WHEN type = 'income' THEN amount ELSE -amount END) as balance
        FROM transactions
        WHERE user_id = ? AND date BETWEEN ? AND ?
        GROUP BY date
        ORDER BY date
        """
        
        results = self.execute_query(query, (user_id, start_date, end_date), fetchall=True)
        return results
    
    def get_monthly_summary(self, user_id, year):
        """
        獲取指定年份的月度收支摘要
        
        Args:
            user_id: 用戶ID
            year: 年份
            
        Returns:
            list: 月度收支摘要列表
        """
        query = """
        SELECT 
            strftime('%m', date) as month,
            SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as total_income,
            SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as total_expense,
            SUM(CASE WHEN type = 'income' THEN amount ELSE -amount END) as balance
        FROM transactions
        WHERE user_id = ? AND strftime('%Y', date) = ?
        GROUP BY strftime('%m', date)
        ORDER BY month
        """
        
        results = self.execute_query(query, (user_id, str(year)), fetchall=True)
        return results
    
    def sync_line_web_data(self, user_id):
        """
        同步LINE和Web端的數據
        1. 確保用戶在兩端的數據一致性
        2. 解決衝突並更新最新的數據
        
        Args:
            user_id: 用戶ID
            
        Returns:
            dict: 包含同步結果的字典
        """
        try:
            # 獲取用戶基本資料
            user = self.get_user(user_id)
            if not user:
                return {"success": False, "error": "用戶不存在"}
            
            # 獲取用戶的LINE數據
            line_data = self._get_user_line_data(user_id)
            
            # 獲取用戶的Web數據
            web_data = self._get_user_web_data(user_id)
            
            # 同步帳戶數據
            sync_result_accounts = self._sync_accounts(user_id, line_data.get('accounts', []), web_data.get('accounts', []))
            
            # 同步分類數據
            sync_result_categories = self._sync_categories(user_id, line_data.get('categories', []), web_data.get('categories', []))
            
            # 同步交易記錄
            sync_result_transactions = self._sync_transactions(user_id, line_data.get('transactions', []), web_data.get('transactions', []))
            
            # 同步提醒
            sync_result_reminders = self._sync_reminders(user_id, line_data.get('reminders', []), web_data.get('reminders', []))
            
            # 更新用戶的最後同步時間
            self.execute_update(
                "UPDATE users SET last_sync = ? WHERE user_id = ?", 
                (self._get_current_timestamp(), user_id)
            )
            
            return {
                "success": True,
                "accounts": sync_result_accounts,
                "categories": sync_result_categories,
                "transactions": sync_result_transactions,
                "reminders": sync_result_reminders
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _get_user_line_data(self, user_id):
        """
        獲取用戶在LINE端的數據
        
        Args:
            user_id: 用戶ID
            
        Returns:
            dict: 包含用戶LINE端數據的字典
        """
        # 獲取帳戶
        accounts = self.get_accounts(user_id)
        
        # 獲取分類（包括系統默認和用戶自定義）
        categories = self.get_categories(user_id)
        
        # 獲取最近30天的交易記錄
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        today = datetime.now().strftime('%Y-%m-%d')
        
        transactions_query = """
        SELECT t.*, c.name as category_name, c.icon as category_icon, a.name as account_name
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.category_id
        LEFT JOIN accounts a ON t.account_id = a.account_id
        WHERE t.user_id = ? AND t.date BETWEEN ? AND ?
        ORDER BY t.date DESC, t.transaction_id DESC
        """
        transactions = self.execute_query(transactions_query, (user_id, thirty_days_ago, today), fetchall=True)
        
        # 獲取未完成的提醒
        reminders_query = """
        SELECT * FROM reminders 
        WHERE user_id = ? AND status = 'pending'
        ORDER BY datetime ASC
        """
        reminders = self.execute_query(reminders_query, (user_id,), fetchall=True)
        
        return {
            "accounts": accounts,
            "categories": categories,
            "transactions": transactions,
            "reminders": reminders
        }
    
    def _get_user_web_data(self, user_id):
        """
        獲取用戶在Web端的數據
        
        Args:
            user_id: 用戶ID
            
        Returns:
            dict: 包含用戶Web端數據的字典
        """
        # Web端數據與LINE端相同，因為我們使用同一個數據庫
        # 這裡可以根據需要添加特定邏輯以區分Web端數據
        return self._get_user_line_data(user_id)
    
    def _sync_accounts(self, user_id, line_accounts, web_accounts):
        """
        同步帳戶數據
        
        Args:
            user_id: 用戶ID
            line_accounts: LINE端帳戶列表
            web_accounts: Web端帳戶列表
            
        Returns:
            dict: 包含同步結果的字典
        """
        try:
            # 由於我們使用同一個數據庫，帳戶數據應該是一致的
            # 這裡我們只需要返回當前帳戶列表即可
            return {
                "success": True,
                "message": "帳戶數據同步成功",
                "accounts": line_accounts
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"帳戶數據同步失敗: {str(e)}"
            }
    
    def _sync_categories(self, user_id, line_categories, web_categories):
        """
        同步分類數據
        
        Args:
            user_id: 用戶ID
            line_categories: LINE端分類列表
            web_categories: Web端分類列表
            
        Returns:
            dict: 包含同步結果的字典
        """
        try:
            # 由於我們使用同一個數據庫，分類數據應該是一致的
            # 這裡我們只需要返回當前分類列表即可
            return {
                "success": True,
                "message": "分類數據同步成功",
                "categories": line_categories
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"分類數據同步失敗: {str(e)}"
            }
    
    def _sync_transactions(self, user_id, line_transactions, web_transactions):
        """
        同步交易記錄
        
        Args:
            user_id: 用戶ID
            line_transactions: LINE端交易記錄列表
            web_transactions: Web端交易記錄列表
            
        Returns:
            dict: 包含同步結果的字典
        """
        try:
            # 由於我們使用同一個數據庫，交易記錄應該是一致的
            # 這裡我們只需要返回當前交易記錄列表即可
            return {
                "success": True,
                "message": "交易記錄同步成功",
                "transactions": line_transactions
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"交易記錄同步失敗: {str(e)}"
            }
    
    def _sync_reminders(self, user_id, line_reminders, web_reminders):
        """
        同步提醒數據
        
        Args:
            user_id: 用戶ID
            line_reminders: LINE端提醒列表
            web_reminders: Web端提醒列表
            
        Returns:
            dict: 包含同步結果的字典
        """
        try:
            # 由於我們使用同一個數據庫，提醒數據應該是一致的
            # 這裡我們只需要返回當前提醒列表即可
            return {
                "success": True,
                "message": "提醒數據同步成功",
                "reminders": line_reminders
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"提醒數據同步失敗: {str(e)}"
            }
    
    def _get_current_timestamp(self):
        """獲取當前時間戳"""
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S') 
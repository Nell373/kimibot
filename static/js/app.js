/**
 * LINE 智能記帳與提醒助手 - 前端應用邏輯
 */

// 等待DOM完全加載
document.addEventListener('DOMContentLoaded', () => {
    // 登入按鈕事件
    const loginBtn = document.getElementById('loginBtn');
    if (loginBtn) {
        loginBtn.addEventListener('click', handleLogin);
    }

    // 檢查用戶登入狀態
    checkLoginStatus();
});

/**
 * 處理用戶登入
 */
function handleLogin(e) {
    e.preventDefault();
    
    // 透過 LINE LIFF 實現登入
    // 注意：實際實現時需要整合 LINE LIFF SDK
    console.log('用戶點擊登入按鈕');
    
    // 模擬登入流程，實際應用中應整合LIFF
    alert('此功能尚在開發中，請先透過 LINE 使用基本功能！');
}

/**
 * 檢查用戶登入狀態
 */
function checkLoginStatus() {
    // 檢查本地存儲的登入令牌
    const token = localStorage.getItem('auth_token');
    
    // 測試階段只是簡單的模擬
    if (token) {
        console.log('用戶已登入');
        // 可以在這裡自動切換到用戶儀表板
    } else {
        console.log('用戶未登入');
    }
}

/**
 * 格式化貨幣
 * @param {number} amount - 金額
 * @param {string} currency - 貨幣符號
 * @returns {string} 格式化後的金額
 */
function formatCurrency(amount, currency = 'NT$') {
    return `${currency} ${amount.toLocaleString('zh-TW')}`;
}

/**
 * 格式化日期
 * @param {Date|string} date - 日期對象或ISO字符串
 * @returns {string} 格式化後的日期
 */
function formatDate(date) {
    if (typeof date === 'string') {
        date = new Date(date);
    }
    
    return date.toLocaleDateString('zh-TW', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// 全局錯誤處理
window.addEventListener('error', (e) => {
    console.error('全局錯誤:', e.message);
    // 可以在這裡實現錯誤報告機制
}); 
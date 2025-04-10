/**
 * LINE 智能記帳與提醒助手 - 登入功能
 */

// LIFF應用ID - 改為實際的LIFF ID
const LIFF_ID = '1234567890-abcdefgh';

// 頁面載入時初始化
document.addEventListener('DOMContentLoaded', () => {
    // 初始化LIFF
    initializeLIFF();
    
    // 表單提交事件
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', handleFormLogin);
    }
    
    // LINE登入按鈕事件
    const lineLoginBtn = document.getElementById('line-login-btn');
    if (lineLoginBtn) {
        lineLoginBtn.addEventListener('click', handleLineLogin);
    }
    
    // 檢查是否已經登入
    checkLoginStatus();
});

/**
 * 初始化LIFF
 */
function initializeLIFF() {
    // 初始化 LIFF SDK
    liff.init({
        liffId: LIFF_ID
    }).then(() => {
        console.log('LIFF初始化成功');
        
        // 如果已經在LIFF環境中並已經登入，自動處理登入
        if (liff.isLoggedIn() && liff.isInClient()) {
            handleLIFFLogin();
        }
    }).catch((error) => {
        console.error('LIFF初始化失敗', error);
        showError('LINE登入服務暫時無法使用，請稍後再試或使用ID登入。');
    });
}

/**
 * 處理LINE登入
 */
function handleLineLogin() {
    // 檢查LIFF是否可用
    if (!liff || !liff.isApiAvailable('login')) {
        showError('LINE登入功能暫時無法使用，請稍後再試。');
        return;
    }
    
    // 如果已登入，直接處理
    if (liff.isLoggedIn()) {
        handleLIFFLogin();
        return;
    }
    
    // 未登入則進行登入
    liff.login();
}

/**
 * LIFF登入成功後的處理
 */
function handleLIFFLogin() {
    // 獲取用戶資料
    liff.getProfile()
        .then(profile => {
            const userId = profile.userId;
            const displayName = profile.displayName;
            
            // 發送登入請求到後端
            fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    type: 'line',
                    userId: userId,
                    displayName: displayName
                }),
                credentials: 'same-origin'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // 儲存Token到cookie
                    document.cookie = `auth_token=${data.token}; path=/; max-age=${60*60*24}`;
                    
                    // 儲存用戶資訊到本地以便快速訪問
                    localStorage.setItem('user_id', userId);
                    localStorage.setItem('user_name', displayName);
                    
                    // 重定向到儀表板
                    redirectToDashboard();
                } else {
                    showError(data.error || '登入失敗，請稍後再試。');
                }
            })
            .catch(error => {
                console.error('登入請求失敗', error);
                showError('登入過程中發生錯誤，請稍後再試。');
            });
        })
        .catch(error => {
            console.error('獲取用戶資料失敗', error);
            showError('無法獲取您的LINE資料，請稍後再試。');
        });
}

/**
 * 處理表單登入
 */
function handleFormLogin(e) {
    e.preventDefault();
    
    const userId = document.getElementById('user-id').value;
    const password = document.getElementById('password').value;
    
    // 簡單驗證
    if (!userId || !password) {
        showError('請輸入用戶ID和密碼');
        return;
    }
    
    // 顯示載入中
    showLoading(true);
    
    // 發送登入請求到後端
    fetch('/api/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            type: 'form',
            userId: userId,
            password: password
        }),
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 儲存Token到cookie
            document.cookie = `auth_token=${data.token}; path=/; max-age=${60*60*24}`;
            
            // 儲存用戶資訊到本地以便快速訪問
            localStorage.setItem('user_id', data.user_id);
            localStorage.setItem('user_name', data.display_name);
            
            // 重定向到儀表板
            redirectToDashboard();
        } else {
            showError(data.error || '用戶ID或密碼不正確');
        }
        showLoading(false);
    })
    .catch(error => {
        console.error('登入請求失敗', error);
        showError('登入過程中發生錯誤，請稍後再試。');
        showLoading(false);
    });
}

/**
 * 檢查用戶登入狀態
 */
function checkLoginStatus() {
    // 檢查後端session狀態
    fetch('/api/check-auth', {
        method: 'GET',
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.authenticated) {
            // 登入有效，更新本地存儲
            localStorage.setItem('user_id', data.user_id);
            localStorage.setItem('user_name', data.user_name);
            
            // 轉到儀表板
            redirectToDashboard();
        } else {
            // 檢查本地令牌
            const authToken = getCookie('auth_token');
            if (authToken) {
                // 嘗試用令牌重新驗證
                fetch('/api/check-auth', {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${authToken}`
                    },
                    credentials: 'same-origin'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.authenticated) {
                        redirectToDashboard();
                    } else {
                        // 清除無效令牌
                        document.cookie = 'auth_token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT';
                        clearLoginData();
                    }
                }).catch(() => {
                    clearLoginData();
                });
            }
        }
    })
    .catch(error => {
        console.error('檢查登入狀態失敗', error);
    });
}

/**
 * 從Cookie獲取特定值
 */
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

/**
 * 清除登入數據
 */
function clearLoginData() {
    localStorage.removeItem('user_id');
    localStorage.removeItem('user_name');
    document.cookie = 'auth_token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT';
}

/**
 * 重定向到儀表板
 */
function redirectToDashboard() {
    window.location.href = '/dashboard';
}

/**
 * 顯示錯誤訊息
 */
function showError(message) {
    // 檢查是否已有錯誤提示
    let errorElement = document.querySelector('.error-message');
    
    if (!errorElement) {
        // 創建錯誤提示元素
        errorElement = document.createElement('div');
        errorElement.className = 'error-message';
        
        // 插入到表單前
        const form = document.getElementById('login-form');
        if (form) {
            form.parentNode.insertBefore(errorElement, form);
        } else {
            document.querySelector('.login-methods').appendChild(errorElement);
        }
    }
    
    // 設置錯誤訊息並顯示
    errorElement.textContent = message;
    errorElement.style.display = 'block';
    
    // 5秒後自動隱藏
    setTimeout(() => {
        errorElement.style.display = 'none';
    }, 5000);
}

/**
 * 顯示/隱藏載入中
 */
function showLoading(show) {
    const loginBtn = document.querySelector('.login-form button[type="submit"]');
    
    if (loginBtn) {
        if (show) {
            loginBtn.textContent = '登入中...';
            loginBtn.disabled = true;
        } else {
            loginBtn.textContent = '登入';
            loginBtn.disabled = false;
        }
    }
} 
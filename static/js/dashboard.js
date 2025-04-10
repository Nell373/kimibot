/**
 * LINE 智能記帳與提醒助手 - 儀表板功能
 */

// 等待DOM完全加載
document.addEventListener('DOMContentLoaded', () => {
    // 載入用戶資訊
    loadUserInfo();
    
    // 註冊登出按鈕事件
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }
    
    // 註冊導航事件
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', () => handleNavigation(item.dataset.target));
    });
    
    // 載入統計數據
    loadDashboardData();
});

/**
 * 載入用戶資訊
 */
function loadUserInfo() {
    // 從本地存儲獲取用戶名稱
    const userName = localStorage.getItem('user_name') || '用戶';
    const userNameElement = document.getElementById('user-name');
    
    if (userNameElement) {
        userNameElement.textContent = userName;
    }
    
    // 檢查用戶授權狀態
    fetch('/api/check-auth', {
        method: 'GET',
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (!data.authenticated) {
            // 如果未登入，重定向到登入頁面
            window.location.href = '/login';
        } else {
            // 更新用戶信息
            if (userNameElement && data.user_name) {
                userNameElement.textContent = data.user_name;
                localStorage.setItem('user_name', data.user_name);
            }
        }
    })
    .catch(error => {
        console.error('驗證用戶狀態失敗', error);
        // 發生錯誤時，也重定向到登入頁面
        window.location.href = '/login';
    });
}

/**
 * 處理用戶登出
 */
function handleLogout() {
    // 發送登出請求到後端
    fetch('/api/logout', {
        method: 'POST',
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 清除本地存儲
            localStorage.removeItem('user_id');
            localStorage.removeItem('user_name');
            
            // 清除Cookie中的Token
            document.cookie = 'auth_token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT';
            
            // 重定向到登入頁面
            window.location.href = '/login';
        } else {
            console.error('登出失敗');
        }
    })
    .catch(error => {
        console.error('登出請求失敗', error);
        // 即使請求失敗，也嘗試清除本地資訊並重定向
        localStorage.removeItem('user_id');
        localStorage.removeItem('user_name');
        document.cookie = 'auth_token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT';
        window.location.href = '/login';
    });
}

/**
 * 處理頁面導航
 */
function handleNavigation(target) {
    // 更新活躍選項卡
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        if (item.getAttribute('data-target') === target) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    // 隱藏所有內容區塊
    const contentSections = document.querySelectorAll('.content-section');
    contentSections.forEach(section => {
        section.style.display = 'none';
    });

    // 顯示目標內容區塊
    const targetSection = document.getElementById(`${target}-section`);
    if (targetSection) {
        targetSection.style.display = 'block';
    }

    // 根據目標加載相應數據
    switch (target) {
        case 'overview':
            loadOverviewData();
            break;
        case 'transactions':
            loadTransactionsPageData();
            break;
        case 'accounts':
            loadAccountsPageData();
            break;
        case 'categories':
            loadCategoriesPageData();
            break;
        case 'reminders':
            loadRemindersPageData();
            break;
        case 'settings':
            loadSettingsData();
            break;
    }
}

/**
 * 載入儀表板初始數據
 */
function loadDashboardData() {
    // 默認載入總覽頁數據
    loadOverviewData();
}

/**
 * 載入總覽頁數據
 */
function loadOverviewData() {
    // 載入本月收支統計
    loadMonthSummary();
    
    // 載入收支趨勢圖表
    loadIncomeExpenseChart();
    
    // 載入支出分類圖表
    loadExpenseCategoryChart();
    
    // 載入近期提醒
    loadUpcomingReminders();
}

/**
 * 載入本月收支統計
 */
function loadMonthSummary() {
    // 獲取元素
    const monthIncomeElement = document.getElementById('month-income');
    const monthExpenseElement = document.getElementById('month-expense');
    const monthBalanceElement = document.getElementById('month-balance');
    
    if (!monthIncomeElement || !monthExpenseElement || !monthBalanceElement) return;
    
    // 顯示載入狀態
    monthIncomeElement.textContent = '-';
    monthExpenseElement.textContent = '-';
    monthBalanceElement.textContent = '-';
    
    // 獲取當前月份的開始和結束日期
    const today = new Date();
    const startDate = new Date(today.getFullYear(), today.getMonth(), 1).toISOString().split('T')[0];
    const endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0).toISOString().split('T')[0];
    
    // 獲取本月收支數據
    fetch(`/api/reports/daily-summary?start_date=${startDate}&end_date=${endDate}`)
        .then(response => response.json())
        .then(data => {
            // 計算總收入和總支出
            let totalIncome = 0;
            let totalExpense = 0;
            
            data.forEach(day => {
                totalIncome += day.total_income || 0;
                totalExpense += day.total_expense || 0;
            });
            
            const balance = totalIncome - totalExpense;
            
            // 更新DOM
            monthIncomeElement.textContent = formatCurrency(totalIncome);
            monthExpenseElement.textContent = formatCurrency(totalExpense);
            monthBalanceElement.textContent = formatCurrency(balance);
            
            // 設置顏色
            if (balance >= 0) {
                monthBalanceElement.classList.add('income');
                monthBalanceElement.classList.remove('expense');
            } else {
                monthBalanceElement.classList.add('expense');
                monthBalanceElement.classList.remove('income');
            }
        })
        .catch(error => {
            console.error('獲取本月收支統計失敗:', error);
            
            // 顯示錯誤狀態
            monthIncomeElement.textContent = '載入失敗';
            monthExpenseElement.textContent = '載入失敗';
            monthBalanceElement.textContent = '載入失敗';
        });
}

/**
 * 載入收支趨勢圖表
 */
function loadIncomeExpenseChart() {
    const ctx = document.getElementById('income-expense-chart');
    if (!ctx) return;
    
    // 显示加载状态
    const parentContainer = ctx.parentElement;
    if (parentContainer) {
        parentContainer.innerHTML = '<div class="loading-text">載入中...</div>';
        parentContainer.appendChild(ctx);
    }
    
    // 获取当前日期
    const today = new Date();
    const year = today.getFullYear();
    
    // 获取过去6个月的数据
    fetch(`/api/reports/monthly-summary?year=${year}`)
        .then(response => response.json())
        .then(data => {
            if (!data || data.length === 0) {
                if (parentContainer) {
                    parentContainer.innerHTML = '<div class="empty-state">沒有收支數據</div>';
                }
                return;
            }
            
            // 按月份排序
            data.sort((a, b) => parseInt(a.month) - parseInt(b.month));
            
            // 准备图表数据
            const months = [];
            const incomeData = [];
            const expenseData = [];
            
            // 获取最近6个月的数据
            let lastSixMonths = data;
            if (data.length > 6) {
                lastSixMonths = data.slice(data.length - 6);
            }
            
            // 准备数据
            lastSixMonths.forEach(item => {
                const monthIndex = parseInt(item.month) - 1; // 月份从0开始
                const monthNames = ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月'];
                months.push(monthNames[monthIndex]);
                incomeData.push(item.total_income || 0);
                expenseData.push(item.total_expense || 0);
            });
            
            // 创建图表
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: months,
                    datasets: [
                        {
                            label: '收入',
                            data: incomeData,
                            backgroundColor: 'rgba(75, 192, 192, 0.2)',
                            borderColor: 'rgba(75, 192, 192, 1)',
                            borderWidth: 1
                        },
                        {
                            label: '支出',
                            data: expenseData,
                            backgroundColor: 'rgba(255, 99, 132, 0.2)',
                            borderColor: 'rgba(255, 99, 132, 1)',
                            borderWidth: 1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('載入收支趨勢圖表失敗:', error);
            if (parentContainer) {
                parentContainer.innerHTML = `<div class="error-text">載入失敗: ${error.message}</div>`;
            }
        });
}

/**
 * 載入支出分類圖表
 */
function loadExpenseCategoryChart() {
    const ctx = document.getElementById('expense-category-chart');
    if (!ctx) return;
    
    // 显示加载状态
    const parentContainer = ctx.parentElement;
    if (parentContainer) {
        parentContainer.innerHTML = '<div class="loading-text">載入中...</div>';
        parentContainer.appendChild(ctx);
    }
    
    // 获取当前月份的开始和结束日期
    const today = new Date();
    const startDate = new Date(today.getFullYear(), today.getMonth(), 1).toISOString().split('T')[0];
    const endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0).toISOString().split('T')[0];
    
    // 获取支出分类数据
    fetch(`/api/reports/expense-summary?start_date=${startDate}&end_date=${endDate}`)
        .then(response => response.json())
        .then(data => {
            if (!data || data.length === 0) {
                if (parentContainer) {
                    parentContainer.innerHTML = '<div class="empty-state">沒有支出數據</div>';
                }
                return;
            }
            
            // 按金额排序
            data.sort((a, b) => b.total_amount - a.total_amount);
            
            // 准备图表数据
            const labels = [];
            const amounts = [];
            const backgroundColor = [
                'rgba(255, 99, 132, 0.7)',
                'rgba(54, 162, 235, 0.7)',
                'rgba(255, 206, 86, 0.7)',
                'rgba(75, 192, 192, 0.7)',
                'rgba(153, 102, 255, 0.7)',
                'rgba(255, 159, 64, 0.7)',
                'rgba(255, 99, 132, 0.5)',
                'rgba(54, 162, 235, 0.5)',
                'rgba(255, 206, 86, 0.5)',
                'rgba(75, 192, 192, 0.5)'
            ];
            
            // 限制最多显示10个分类，其余归为"其他"
            let otherAmount = 0;
            if (data.length > 10) {
                for (let i = 0; i < 9; i++) {
                    labels.push(data[i].category_name);
                    amounts.push(data[i].total_amount);
                }
                
                // 累计其他分类的金额
                for (let i = 9; i < data.length; i++) {
                    otherAmount += data[i].total_amount || 0;
                }
                
                labels.push('其他');
                amounts.push(otherAmount);
            } else {
                data.forEach(item => {
                    labels.push(item.category_name);
                    amounts.push(item.total_amount);
                });
            }
            
            // 创建图表
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: amounts,
                        backgroundColor: backgroundColor.slice(0, labels.length),
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'right'
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('載入支出分類圖表失敗:', error);
            if (parentContainer) {
                parentContainer.innerHTML = `<div class="error-text">載入失敗: ${error.message}</div>`;
            }
        });
}

/**
 * 載入近期提醒
 */
function loadUpcomingReminders() {
    const remindersContainer = document.getElementById('upcoming-reminders');
    if (!remindersContainer) return;
    
    // 清空容器并显示加载状态
    remindersContainer.innerHTML = '<div class="loading-text">載入中...</div>';
    
    // 获取近期提醒数据
    fetch('/api/reminders?status=pending')
        .then(response => response.json())
        .then(reminders => {
            if (!reminders || reminders.length === 0) {
                remindersContainer.innerHTML = '<div class="empty-state">目前沒有近期提醒</div>';
                return;
            }
            
            // 按日期升序排序
            reminders.sort((a, b) => {
                return new Date(a.datetime) - new Date(b.datetime);
            });
            
            // 只显示最近的5条提醒
            const recentReminders = reminders.slice(0, 5);
            
            // 清空容器
            remindersContainer.innerHTML = '';
            
            // 创建提醒项目
            recentReminders.forEach(reminder => {
                const reminderDate = new Date(reminder.datetime);
                const now = new Date();
                
                // 构建日期显示
                let dateDisplay = '';
                
                // 计算天数差异
                const diffTime = reminderDate - now;
                const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                
                // 根据差异生成不同文字
                if (diffDays === 0) {
                    dateDisplay = '今天';
                } else if (diffDays === 1) {
                    dateDisplay = '明天';
                } else if (diffDays <= 7) {
                    const dayNames = ['日', '一', '二', '三', '四', '五', '六'];
                    dateDisplay = `${diffDays}天後 (${dayNames[reminderDate.getDay()]})`;
                } else {
                    dateDisplay = formatDate(reminderDate);
                }
                
                // 获取时间部分
                const timeStr = reminderDate.toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' });
                
                // 创建提醒元素
                const reminderEl = document.createElement('div');
                reminderEl.className = 'reminder-item';
                
                reminderEl.innerHTML = `
                    <div class="reminder-content">${reminder.content}</div>
                    <div class="reminder-time">${dateDisplay} ${timeStr}</div>
                    <div class="reminder-actions">
                        <button class="complete-btn" data-id="${reminder.reminder_id}">完成</button>
                        <button class="delete-btn" data-id="${reminder.reminder_id}">刪除</button>
                    </div>
                `;
                
                remindersContainer.appendChild(reminderEl);
            });
            
            // 註冊提醒操作事件
            remindersContainer.querySelectorAll('.complete-btn').forEach(btn => {
                btn.addEventListener('click', () => completeReminderFromOverview(btn.dataset.id));
            });
            
            remindersContainer.querySelectorAll('.delete-btn').forEach(btn => {
                btn.addEventListener('click', () => deleteReminderFromOverview(btn.dataset.id));
            });
        })
        .catch(error => {
            console.error('載入近期提醒失敗:', error);
            remindersContainer.innerHTML = '<div class="error-text">載入失敗，請稍後再試</div>';
        });
}

/**
 * 在總覽頁面標記提醒為已完成
 * @param {string} reminderId - 提醒ID
 */
function completeReminderFromOverview(reminderId) {
    fetch(`/api/reminders/${reminderId}/complete`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 重新載入近期提醒
            loadUpcomingReminders();
        } else {
            alert(data.error || '操作失敗');
        }
    })
    .catch(error => {
        console.error('標記提醒完成失敗:', error);
        alert('標記提醒完成失敗: ' + error.message);
    });
}

/**
 * 在總覽頁面刪除提醒
 * @param {string} reminderId - 提醒ID
 */
function deleteReminderFromOverview(reminderId) {
    if (!confirm('確定要刪除此提醒嗎？')) {
        return;
    }
    
    fetch(`/api/reminders/${reminderId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 重新載入近期提醒
            loadUpcomingReminders();
        } else {
            alert(data.error || '操作失敗');
        }
    })
    .catch(error => {
        console.error('刪除提醒失敗:', error);
        alert('刪除提醒失敗: ' + error.message);
    });
}

/**
 * 格式化日期
 * @param {Date} date - 日期對象
 * @return {string} 格式化後的日期字符串
 */
function formatDate(date) {
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    return `${year}/${month}/${day}`;
}

/**
 * 載入交易記錄數據
 */
function loadTransactionsData() {
    // 顯示加載指示器
    const contentContainer = document.querySelector('#content-container');
    contentContainer.innerHTML = '<div class="text-center py-5"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">加載中...</span></div></div>';
    
    // 獲取過濾條件
    const type = document.querySelector('#transaction-type-filter')?.value || 'all';
    const dateRange = document.querySelector('#date-range-filter')?.value || 'this-month';
    const startDate = document.querySelector('#start-date')?.value || '';
    const endDate = document.querySelector('#end-date')?.value || '';
    const categoryId = document.querySelector('#category-filter')?.value || '';
    const page = currentPage || 1;
    
    // 構建API URL
    let apiUrl = `/api/transactions?page=${page}&type=${type}&date_range=${dateRange}`;
    
    if (startDate && endDate) {
        apiUrl += `&start_date=${startDate}&end_date=${endDate}`;
    }
    
    if (categoryId) {
        apiUrl += `&category_id=${categoryId}`;
    }
    
    // 發送API請求
    fetch(apiUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error('網絡請求失敗');
            }
            return response.json();
        })
        .then(data => {
            // 更新分頁信息
            updatePagination(data.pagination);
            
            // 顯示交易記錄
            displayTransactions(data.transactions, contentContainer);
            
            // 更新過濾器顯示
            updateFiltersDisplay(data.filters);
        })
        .catch(error => {
            console.error('獲取交易記錄失敗:', error);
            contentContainer.innerHTML = `
                <div class="alert alert-danger" role="alert">
                    載入交易記錄失敗: ${error.message}
                    <button class="btn btn-sm btn-outline-danger ms-2" onclick="loadTransactionsData()">重試</button>
                </div>
            `;
        });
}

/**
 * 顯示交易記錄列表
 */
function displayTransactions(transactions, container) {
    if (!transactions || transactions.length === 0) {
        container.innerHTML = `
            <div class="text-center py-5">
                <div class="mb-3">
                    <i class="bi bi-inbox fs-1 text-muted"></i>
                </div>
                <h5 class="text-muted">沒有找到交易記錄</h5>
                <p class="text-muted small">嘗試調整過濾條件或添加新交易</p>
                <button class="btn btn-primary btn-sm" onclick="showNewTransactionModal()">
                    <i class="bi bi-plus-circle me-1"></i>新增交易
                </button>
            </div>
        `;
        return;
    }
    
    // 創建交易記錄表格
    let html = `
        <div class="table-responsive">
            <table class="table table-hover align-middle">
                <thead class="table-light">
                    <tr>
                        <th>日期</th>
                        <th>分類</th>
                        <th>描述</th>
                        <th>帳戶</th>
                        <th class="text-end">金額</th>
                        <th class="text-center">操作</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    // 按日期對交易進行分組
    const groupedTransactions = groupTransactionsByDate(transactions);
    
    // 遍歷所有日期組
    Object.keys(groupedTransactions).forEach(dateGroup => {
        // 添加日期標題行
        html += `
            <tr class="table-secondary">
                <td colspan="6" class="fw-bold">
                    <i class="bi bi-calendar-event me-2"></i>${dateGroup}
                </td>
            </tr>
        `;
        
        // 添加該日期的所有交易
        groupedTransactions[dateGroup].forEach(transaction => {
            const isExpense = transaction.type === 'expense';
            const amountClass = isExpense ? 'text-danger' : 'text-success';
            const amountPrefix = isExpense ? '-' : '+';
            const amountFormatted = formatCurrency(transaction.amount);
            
            html += `
                <tr data-transaction-id="${transaction.transaction_id}">
                    <td class="text-nowrap small text-muted">${transaction.date_formatted || transaction.date}</td>
                    <td>
                        <span class="category-icon">${transaction.category_icon || getDefaultCategoryIcon(transaction.type)}</span>
                        ${transaction.category_name || '未分類'}
                    </td>
                    <td class="text-break">${transaction.memo || '無描述'}</td>
                    <td>${transaction.account_name || '默認帳戶'}</td>
                    <td class="text-end fw-semibold ${amountClass}">${amountPrefix}${amountFormatted}</td>
                    <td class="text-center">
                        <div class="btn-group btn-group-sm">
                            <button type="button" class="btn btn-outline-primary" 
                                    onclick="editTransaction(${transaction.transaction_id})">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button type="button" class="btn btn-outline-danger" 
                                    onclick="deleteTransaction(${transaction.transaction_id})">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        });
    });
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = html;
}

/**
 * 按日期對交易記錄進行分組
 */
function groupTransactionsByDate(transactions) {
    const groups = {};
    
    transactions.forEach(transaction => {
        const dateFormatted = transaction.date_formatted || formatDate(transaction.date);
        
        if (!groups[dateFormatted]) {
            groups[dateFormatted] = [];
        }
        
        groups[dateFormatted].push(transaction);
    });
    
    return groups;
}

/**
 * 格式化金額為貨幣格式
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('zh-TW', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    }).format(amount);
}

/**
 * 格式化日期
 */
function formatDate(dateStr) {
    if (!dateStr) return '';
    
    const date = new Date(dateStr);
    const year = date.getFullYear();
    const month = date.getMonth() + 1;
    const day = date.getDate();
    
    return `${year}年${month}月${day}日`;
}

/**
 * 獲取分類的默認圖標
 */
function getDefaultCategoryIcon(type) {
    return type === 'expense' ? '💰' : '💵';
}

/**
 * 更新分頁信息
 */
function updatePagination(pagination) {
    if (!pagination) return;
    
    const paginationEl = document.querySelector('#pagination');
    if (!paginationEl) return;
    
    const {current_page, total_pages, has_prev, has_next} = pagination;
    
    let html = `
        <nav aria-label="交易記錄分頁">
            <ul class="pagination justify-content-center">
                <li class="page-item ${!has_prev ? 'disabled' : ''}">
                    <a class="page-link" href="#" onclick="${has_prev ? 'changePage(' + (current_page - 1) + ')' : 'return false'}" aria-label="上一頁">
                        <span aria-hidden="true">&laquo;</span>
                    </a>
                </li>
    `;
    
    // 顯示頁碼
    const startPage = Math.max(1, current_page - 2);
    const endPage = Math.min(total_pages, startPage + 4);
    
    for (let i = startPage; i <= endPage; i++) {
        html += `
            <li class="page-item ${i === current_page ? 'active' : ''}">
                <a class="page-link" href="#" onclick="changePage(${i})">${i}</a>
            </li>
        `;
    }
    
    html += `
                <li class="page-item ${!has_next ? 'disabled' : ''}">
                    <a class="page-link" href="#" onclick="${has_next ? 'changePage(' + (current_page + 1) + ')' : 'return false'}" aria-label="下一頁">
                        <span aria-hidden="true">&raquo;</span>
                    </a>
                </li>
            </ul>
        </nav>
    `;
    
    paginationEl.innerHTML = html;
}

/**
 * 更改頁碼
 */
function changePage(page) {
    currentPage = page;
    loadTransactionsData();
    return false;
}

/**
 * 更新過濾器顯示
 */
function updateFiltersDisplay(filters) {
    if (!filters) return;
    
    // 更新日期範圍顯示
    const dateRangeText = document.querySelector('#date-range-text');
    if (dateRangeText) {
        let dateRangeStr = '';
        
        switch (filters.date_range) {
            case 'this-month':
                dateRangeStr = '本月';
                break;
            case 'last-month':
                dateRangeStr = '上月';
                break;
            case 'this-week':
                dateRangeStr = '本週';
                break;
            case 'last-week':
                dateRangeStr = '上週';
                break;
            case 'custom':
                const startDate = filters.start_date ? formatDate(filters.start_date) : '';
                const endDate = filters.end_date ? formatDate(filters.end_date) : '';
                dateRangeStr = `${startDate} 至 ${endDate}`;
                break;
            default:
                dateRangeStr = '全部時間';
        }
        
        dateRangeText.textContent = dateRangeStr;
    }
    
    // 更新交易類型過濾器
    const typeFilter = document.querySelector('#transaction-type-filter');
    if (typeFilter && filters.type) {
        typeFilter.value = filters.type;
    }
}

/**
 * 刪除交易記錄
 * @param {number} transactionId - 交易記錄ID
 */
function deleteTransaction(transactionId) {
    if (!confirm('確定要刪除此交易記錄嗎？')) {
        return;
    }
    
    fetch(`/api/transactions/${transactionId}`, {
        method: 'DELETE'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('刪除交易記錄失敗');
        }
        return response.json();
    })
    .then(data => {
        showToast('成功', '交易記錄已刪除', 'success');
        loadTransactionsData();
    })
    .catch(error => {
        console.error('刪除交易記錄失敗:', error);
        showToast('錯誤', `刪除交易記錄失敗: ${error.message}`, 'danger');
    });
}

/**
 * 顯示通知提示
 */
function showToast(title, message, type = 'info') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) return;
    
    const toastId = 'toast-' + Date.now();
    const html = `
        <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header bg-${type} text-white">
                <strong class="me-auto">${title}</strong>
                <small>剛剛</small>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', html);
    const toastEl = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastEl, { delay: 5000 });
    
    toast.show();
    
    // 自動移除已關閉的toast
    toastEl.addEventListener('hidden.bs.toast', () => {
        toastEl.remove();
    });
}

// 初始化頁面時載入交易記錄
let currentPage = 1;

// 初始化過濾器
function initFilters() {
    // 日期範圍過濾器
    const dateRangeFilter = document.querySelector('#date-range-filter');
    if (dateRangeFilter) {
        dateRangeFilter.addEventListener('change', function() {
            const customDateRange = document.querySelector('#custom-date-range');
            if (this.value === 'custom') {
                customDateRange.classList.remove('d-none');
            } else {
                customDateRange.classList.add('d-none');
                currentPage = 1;
                loadTransactionsData();
            }
        });
    }
    
    // 交易類型過濾器
    const typeFilter = document.querySelector('#transaction-type-filter');
    if (typeFilter) {
        typeFilter.addEventListener('change', function() {
            currentPage = 1;
            loadTransactionsData();
        });
    }
    
    // 應用自定義日期範圍按鈕
    const applyDateRangeBtn = document.querySelector('#apply-date-range');
    if (applyDateRangeBtn) {
        applyDateRangeBtn.addEventListener('click', function() {
            currentPage = 1;
            loadTransactionsData();
        });
    }
    
    // 分類過濾器
    const categoryFilter = document.querySelector('#category-filter');
    if (categoryFilter) {
        categoryFilter.addEventListener('change', function() {
            currentPage = 1;
            loadTransactionsData();
        });
    }
}

/**
 * 初始化頁面
 */
function init() {
    // 初始化篩選器
    initFilters();
    
    // 載入交易記錄
    loadTransactionsData();
    
    // 添加新增按鈕事件監聽
    document.getElementById('add-transaction-btn').addEventListener('click', showNewTransactionModal);
}

// 當頁面載入完成後初始化
document.addEventListener('DOMContentLoaded', init);

/**
 * 載入提醒事項頁數據
 */
function loadRemindersData() {
    // 這裡添加載入提醒數據的邏輯
    console.log('載入提醒事項數據');
}

/**
 * 載入帳戶管理頁數據
 */
function loadAccountsPageData() {
    // 綁定新增帳戶按鈕事件
    const addAccountButton = document.getElementById('add-account');
    if (addAccountButton) {
        addAccountButton.addEventListener('click', showAddAccountModal);
    }
    
    // 初始化帳戶模態框
    initializeAccountModal();
    
    // 載入帳戶數據
    loadAccountsData();
}

/**
 * 初始化帳戶模態框
 */
function initializeAccountModal() {
    // 創建模態框 HTML 如果不存在
    if (!document.getElementById('account-modal')) {
        const modalHtml = `
            <div class="modal" id="account-modal">
                <div class="modal-content">
                    <span class="close-btn">&times;</span>
                    <h3 id="account-modal-title">新增帳戶</h3>
                    <form id="account-form">
                        <input type="hidden" id="account-id" value="new">
                        
                        <div class="form-group">
                            <label for="account-name">帳戶名稱</label>
                            <input type="text" id="account-name" required placeholder="請輸入帳戶名稱">
                        </div>
                        
                        <div class="form-group">
                            <label for="account-balance">初始餘額</label>
                            <input type="number" id="account-balance" placeholder="請輸入初始餘額" value="0">
                        </div>
                        
                        <div class="form-group">
                            <label>
                                <input type="checkbox" id="account-is-default">
                                設為預設帳戶
                            </label>
                        </div>
                        
                        <div class="form-actions">
                            <button type="button" id="cancel-account" class="secondary-btn">取消</button>
                            <button type="submit" class="primary-btn">儲存</button>
                        </div>
                    </form>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
    }
    
    // 獲取模態框和關閉按鈕
    const modal = document.getElementById('account-modal');
    const closeBtn = modal.querySelector('.close-btn');
    const cancelBtn = document.getElementById('cancel-account');
    
    // 設置關閉按鈕事件
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            modal.style.display = 'none';
        });
    }
    
    // 設置取消按鈕事件
    if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
            modal.style.display = 'none';
        });
    }
    
    // 當用戶點擊模態框外部時關閉
    window.addEventListener('click', (event) => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
    
    // 設置表單提交事件
    const form = document.getElementById('account-form');
    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            saveAccount();
        });
    }
}

/**
 * 載入帳戶數據
 */
function loadAccountsData() {
    const accountsGrid = document.getElementById('accounts-grid');
    if (!accountsGrid) return;
    
    // 顯示載入中
    accountsGrid.innerHTML = '<div class="loading-text">載入中...</div>';
    
    // 獲取帳戶數據
    fetch('/api/accounts')
        .then(response => response.json())
        .then(accounts => {
            if (!accounts || accounts.length === 0) {
                accountsGrid.innerHTML = '<div class="empty-text">沒有帳戶數據，請新增帳戶</div>';
                return;
            }
            
            // 渲染帳戶列表
            let html = '';
            accounts.forEach(account => {
                const isDefault = account.is_default === 1;
                
                html += `
                <div class="account-card" data-account-id="${account.account_id}">
                    <div class="account-name">${account.name} ${isDefault ? '<span class="default-badge">預設</span>' : ''}</div>
                    <div class="account-balance">${formatCurrency(account.balance)}</div>
                    <div class="account-actions">
                        <button class="edit-btn" onclick="showEditAccountModal(${account.account_id})">編輯</button>
                        <button class="delete-btn" onclick="deleteAccount(${account.account_id})">刪除</button>
                    </div>
                </div>
                `;
            });
            
            accountsGrid.innerHTML = html;
        })
        .catch(error => {
            console.error('載入帳戶失敗:', error);
            accountsGrid.innerHTML = `<div class="error-text">載入失敗: ${error.message}</div>`;
        });
}

/**
 * 顯示新增帳戶模態框
 */
function showAddAccountModal() {
    const modal = document.getElementById('account-modal');
    if (!modal) return;
    
    // 設置模態框標題
    const modalTitle = document.getElementById('account-modal-title');
    if (modalTitle) {
        modalTitle.textContent = '新增帳戶';
    }
    
    // 重置表單
    const form = document.getElementById('account-form');
    if (form) {
        form.reset();
    }
    
    // 設置為新增模式
    document.getElementById('account-id').value = 'new';
    
    // 顯示模態框
    modal.style.display = 'block';
}

/**
 * 顯示編輯帳戶模態框
 * @param {number} accountId - 帳戶ID
 */
function showEditAccountModal(accountId) {
    const modal = document.getElementById('account-modal');
    if (!modal) return;
    
    // 設置模態框標題
    const modalTitle = document.getElementById('account-modal-title');
    if (modalTitle) {
        modalTitle.textContent = '編輯帳戶';
    }
    
    // 獲取帳戶數據
    fetch('/api/accounts')
        .then(response => response.json())
        .then(accounts => {
            const account = accounts.find(acc => acc.account_id === accountId);
            if (!account) {
                alert('找不到該帳戶');
                return;
            }
            
            // 填充表單數據
            document.getElementById('account-id').value = account.account_id;
            document.getElementById('account-name').value = account.name;
            document.getElementById('account-balance').value = account.balance;
            document.getElementById('account-is-default').checked = account.is_default === 1;
            
            // 如果是編輯，禁用餘額輸入框，避免直接修改餘額
            if (accountId !== 'new') {
                document.getElementById('account-balance').disabled = true;
            } else {
                document.getElementById('account-balance').disabled = false;
            }
            
            // 顯示模態框
            modal.style.display = 'block';
        })
        .catch(error => {
            console.error('獲取帳戶詳情失敗:', error);
            alert('獲取帳戶詳情失敗: ' + error.message);
        });
}

/**
 * 保存帳戶
 */
function saveAccount() {
    // 獲取表單數據
    const accountId = document.getElementById('account-id').value;
    const name = document.getElementById('account-name').value;
    const balance = parseFloat(document.getElementById('account-balance').value) || 0;
    const isDefault = document.getElementById('account-is-default').checked;
    
    // 表單驗證
    if (!name) {
        alert('請填寫帳戶名稱');
        return;
    }
    
    // 準備請求數據
    const accountData = {
        name,
        balance,
        is_default: isDefault
    };
    
    // 確定請求方法和URL
    const isNew = accountId === 'new';
    const method = isNew ? 'POST' : 'PUT';
    const url = isNew ? '/api/accounts' : `/api/accounts/${accountId}`;
    
    // 發送請求
    fetch(url, {
        method,
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(accountData)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => {
                throw new Error(err.error || '保存帳戶失敗');
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // 關閉模態框
            document.getElementById('account-modal').style.display = 'none';
            
            // 重新載入帳戶列表
            loadAccountsData();
            
            // 顯示成功訊息
            alert(isNew ? '帳戶已新增' : '帳戶已更新');
        } else {
            alert(data.error || '操作失敗');
        }
    })
    .catch(error => {
        console.error('保存帳戶失敗:', error);
        alert('保存帳戶失敗: ' + error.message);
    });
}

/**
 * 刪除帳戶
 * @param {number} accountId - 帳戶ID
 */
function deleteAccount(accountId) {
    if (!confirm('確定要刪除此帳戶嗎？這將刪除所有相關交易記錄。')) {
        return;
    }
    
    fetch(`/api/accounts/${accountId}`, {
        method: 'DELETE'
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => {
                throw new Error(err.error || '刪除帳戶失敗');
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // 重新載入帳戶列表
            loadAccountsData();
            
            // 顯示成功訊息
            alert('帳戶已刪除');
        } else {
            alert(data.error || '操作失敗');
        }
    })
    .catch(error => {
        console.error('刪除帳戶失敗:', error);
        alert('刪除帳戶失敗: ' + error.message);
    });
}

/**
 * 格式化貨幣
 * @param {number} amount - 金額
 * @return {string} 格式化後的金額字符串
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('zh-TW', {
        style: 'currency',
        currency: 'TWD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount);
}

/**
 * 載入設定頁數據
 */
function loadSettingsData() {
    // 這裡添加載入設定的邏輯
    console.log('載入設定數據');
}

/**
 * 標記提醒為完成
 */
function completeReminder(id) {
    console.log(`標記提醒 ${id} 為完成`);
    // 實際開發中應發送API請求來更新提醒狀態
}

/**
 * 刪除提醒
 * @param {number} reminderId - 提醒ID
 */
function deleteReminder(reminderId) {
    if (!confirm('確定要刪除此提醒嗎？')) {
        return;
    }
    
    fetch(`/api/reminders/${reminderId}`, {
        method: 'DELETE'
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => {
                throw new Error(err.error || '刪除提醒失敗');
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // 重新載入提醒列表
            const reminderStatus = document.getElementById('reminder-status');
            loadRemindersData(reminderStatus?.value || 'pending');
            
            // 顯示成功訊息
            alert('提醒已刪除');
        } else {
            alert(data.error || '刪除失敗');
        }
    })
    .catch(error => {
        console.error('刪除提醒失敗:', error);
        alert('刪除提醒失敗: ' + error.message);
    });
}

/**
 * 編輯交易記錄
 * @param {number} transactionId - 交易記錄ID
 */
function editTransaction(transactionId) {
    // 獲取交易記錄詳情
    fetch(`/api/transactions/${transactionId}`)
    .then(response => {
        if (!response.ok) {
            throw new Error('獲取交易記錄失敗');
        }
        return response.json();
    })
    .then(transaction => {
        showEditTransactionModal(transaction);
    })
    .catch(error => {
        console.error('獲取交易記錄失敗:', error);
        showToast('錯誤', `獲取交易記錄失敗: ${error.message}`, 'danger');
    });
}

/**
 * 顯示新增交易記錄模態框
 */
function showNewTransactionModal() {
    // 創建空白交易對象
    const emptyTransaction = {
        transaction_id: 'new',
        type: 'expense',
        amount: '',
        date: new Date().toISOString().split('T')[0],
        category_id: '',
        account_id: '',
        memo: ''
    };
    
    // 顯示編輯模態框
    showEditTransactionModal(emptyTransaction);
}

/**
 * 顯示編輯交易記錄模態框
 * @param {Object} transaction - 交易記錄對象
 */
function showEditTransactionModal(transaction) {
    // 獲取模態框元素
    const modalEl = document.getElementById('edit-transaction-modal');
    
    // 如果不存在則創建
    if (!modalEl) {
        createTransactionModal();
    }
    
    // 設置模態框標題
    const modalTitle = document.getElementById('edit-transaction-title');
    modalTitle.textContent = transaction.transaction_id === 'new' ? '新增交易記錄' : '編輯交易記錄';
    
    // 填充表單數據
    document.getElementById('edit-transaction-id').value = transaction.transaction_id;
    document.getElementById('edit-transaction-type').value = transaction.type || 'expense';
    document.getElementById('edit-transaction-amount').value = transaction.amount || '';
    document.getElementById('edit-transaction-date').value = formatDateForInput(transaction.date);
    document.getElementById('edit-transaction-memo').value = transaction.memo || '';
    
    // 加載分類和帳戶選項
    loadCategoriesAndAccounts(
        transaction.type || 'expense',
        transaction.category_id || '',
        transaction.account_id || ''
    );
    
    // 顯示模態框
    const modal = new bootstrap.Modal(modalEl);
    modal.show();
}

/**
 * 創建交易記錄模態框
 */
function createTransactionModal() {
    // 創建模態框HTML
    const modalHtml = `
    <div class="modal fade" id="edit-transaction-modal" tabindex="-1" aria-labelledby="edit-transaction-title" aria-hidden="true">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="edit-transaction-title">編輯交易記錄</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <form id="edit-transaction-form">
                        <input type="hidden" id="edit-transaction-id">
                        
                        <div class="mb-3">
                            <label class="form-label">交易類型</label>
                            <div class="btn-group w-100" role="group">
                                <input type="radio" class="btn-check" name="transaction-type" id="type-expense" value="expense" autocomplete="off" checked>
                                <label class="btn btn-outline-danger" for="type-expense">支出</label>
                                
                                <input type="radio" class="btn-check" name="transaction-type" id="type-income" value="income" autocomplete="off">
                                <label class="btn btn-outline-success" for="type-income">收入</label>
                            </div>
                            <input type="hidden" id="edit-transaction-type" value="expense">
                        </div>
                        
                        <div class="mb-3">
                            <label for="edit-transaction-amount" class="form-label">金額</label>
                            <input type="number" class="form-control" id="edit-transaction-amount" placeholder="輸入金額" required>
                        </div>
                        
                        <div class="mb-3">
                            <label for="edit-transaction-date" class="form-label">日期</label>
                            <input type="date" class="form-control" id="edit-transaction-date" required>
                        </div>
                        
                        <div class="mb-3">
                            <label for="edit-transaction-category" class="form-label">分類</label>
                            <select class="form-select" id="edit-transaction-category">
                                <option value="">選擇分類</option>
                            </select>
                        </div>
                        
                        <div class="mb-3">
                            <label for="edit-transaction-account" class="form-label">帳戶</label>
                            <select class="form-select" id="edit-transaction-account">
                                <option value="">選擇帳戶</option>
                            </select>
                        </div>
                        
                        <div class="mb-3">
                            <label for="edit-transaction-memo" class="form-label">備註</label>
                            <input type="text" class="form-control" id="edit-transaction-memo" placeholder="輸入備註">
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                    <button type="button" class="btn btn-primary" onclick="saveTransaction()">儲存</button>
                </div>
            </div>
        </div>
    </div>
    `;
    
    // 添加到頁面
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // 添加事件監聽器
    document.querySelectorAll('input[name="transaction-type"]').forEach(input => {
        input.addEventListener('change', function() {
            const type = this.value;
            document.getElementById('edit-transaction-type').value = type;
            
            // 重新加載分類和帳戶
            loadCategoriesAndAccounts(type, '', '');
        });
    });
}

/**
 * 格式化日期用於輸入欄位
 * @param {string} dateStr - 日期字串
 * @returns {string} 格式化的日期 (YYYY-MM-DD)
 */
function formatDateForInput(dateStr) {
    if (!dateStr) {
        return new Date().toISOString().split('T')[0];
    }
    
    const date = new Date(dateStr);
    return date.toISOString().split('T')[0];
}

/**
 * 加載分類和帳戶選項
 * @param {string} transactionType - 交易類型 ('expense' 或 'income')
 * @param {string} selectedCategoryId - 已選擇的分類ID
 * @param {string} selectedAccountId - 已選擇的帳戶ID
 */
function loadCategoriesAndAccounts(transactionType, selectedCategoryId, selectedAccountId) {
    // 加載分類
    fetch(`/api/categories?type=${transactionType}`)
    .then(response => {
        if (!response.ok) {
            throw new Error('獲取分類失敗');
        }
        return response.json();
    })
    .then(categories => {
        const categorySelect = document.getElementById('edit-transaction-category');
        categorySelect.innerHTML = '<option value="">選擇分類</option>';
        
        categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category.category_id;
            option.text = `${category.icon || ''} ${category.name}`;
            option.selected = category.category_id == selectedCategoryId;
            categorySelect.appendChild(option);
        });
    })
    .catch(error => {
        console.error('獲取分類失敗:', error);
    });
    
    // 加載帳戶
    fetch('/api/accounts')
    .then(response => {
        if (!response.ok) {
            throw new Error('獲取帳戶失敗');
        }
        return response.json();
    })
    .then(accounts => {
        const accountSelect = document.getElementById('edit-transaction-account');
        accountSelect.innerHTML = '<option value="">選擇帳戶</option>';
        
        accounts.forEach(account => {
            const option = document.createElement('option');
            option.value = account.account_id;
            option.text = account.name;
            option.selected = account.account_id == selectedAccountId;
            accountSelect.appendChild(option);
        });
    })
    .catch(error => {
        console.error('獲取帳戶失敗:', error);
    });
}

/**
 * 保存交易記錄
 */
function saveTransaction() {
    // 獲取表單數據
    const transactionId = document.getElementById('edit-transaction-id').value;
    const type = document.getElementById('edit-transaction-type').value;
    const amount = document.getElementById('edit-transaction-amount').value;
    const date = document.getElementById('edit-transaction-date').value;
    const categoryId = document.getElementById('edit-transaction-category').value;
    const accountId = document.getElementById('edit-transaction-account').value;
    const memo = document.getElementById('edit-transaction-memo').value;
    
    // 驗證表單
    if (!amount || !date) {
        showToast('錯誤', '請填寫必要欄位', 'danger');
        return;
    }
    
    // 準備提交的數據
    const transactionData = {
        type,
        amount: parseFloat(amount),
        date,
        category_id: categoryId || null,
        account_id: accountId || null,
        memo: memo || ''
    };
    
    // 判斷是新增還是更新
    const isNewTransaction = transactionId === 'new';
    const url = isNewTransaction ? '/api/transactions' : `/api/transactions/${transactionId}`;
    const method = isNewTransaction ? 'POST' : 'PUT';
    
    // 發送請求
    fetch(url, {
        method,
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(transactionData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(isNewTransaction ? '新增交易記錄失敗' : '更新交易記錄失敗');
        }
        return response.json();
    })
    .then(data => {
        // 關閉模態框
        const modalEl = document.getElementById('edit-transaction-modal');
        const modal = bootstrap.Modal.getInstance(modalEl);
        modal.hide();
        
        // 顯示成功訊息
        showToast('成功', isNewTransaction ? '交易記錄已新增' : '交易記錄已更新', 'success');
        
        // 重新載入交易列表
        loadTransactionsData();
    })
    .catch(error => {
        console.error(isNewTransaction ? '新增交易記錄失敗:' : '更新交易記錄失敗:', error);
        showToast('錯誤', `${isNewTransaction ? '新增' : '更新'}交易記錄失敗: ${error.message}`, 'danger');
    });
}

/**
 * 創建和初始化交易記錄編輯模態框
 */
function initializeTransactionModal() {
    // 檢查模態框是否已存在
    if (document.getElementById('transaction-modal')) {
        return;
    }
    
    // 創建模態框HTML
    const modalHTML = `
    <div class="modal" id="transaction-modal">
        <div class="modal-content">
            <span class="close-btn" id="close-transaction-modal">&times;</span>
            <h3 id="transaction-modal-title">新增交易</h3>
            <form id="transaction-form">
                <input type="hidden" id="transaction-id" value="new">
                
                <div class="form-group">
                    <label for="transaction-type">類型</label>
                    <select id="transaction-type">
                        <option value="expense">支出</option>
                        <option value="income">收入</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="transaction-date">日期</label>
                    <input type="date" id="transaction-date" required>
                </div>
                
                <div class="form-group">
                    <label for="transaction-amount">金額</label>
                    <input type="number" id="transaction-amount" required placeholder="請輸入金額">
                </div>
                
                <div class="form-group">
                    <label for="transaction-category">分類</label>
                    <select id="transaction-category" required>
                        <option value="">請選擇分類</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="transaction-account">帳戶</label>
                    <select id="transaction-account" required>
                        <option value="">請選擇帳戶</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="transaction-memo">描述</label>
                    <input type="text" id="transaction-memo" placeholder="交易描述">
                </div>
                
                <div class="form-actions">
                    <button type="button" id="cancel-transaction" class="secondary-btn">取消</button>
                    <button type="submit" class="primary-btn">儲存</button>
                </div>
            </form>
        </div>
    </div>
    `;
    
    // 將模態框添加到頁面
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // 獲取模態框元素
    const modal = document.getElementById('transaction-modal');
    const closeBtn = document.getElementById('close-transaction-modal');
    const cancelBtn = document.getElementById('cancel-transaction');
    const form = document.getElementById('transaction-form');
    const typeSelect = document.getElementById('transaction-type');
    
    // 關閉模態框的事件
    closeBtn.addEventListener('click', () => {
        modal.style.display = 'none';
    });
    
    cancelBtn.addEventListener('click', () => {
        modal.style.display = 'none';
    });
    
    // 點擊模態框外部關閉
    window.addEventListener('click', (event) => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
    
    // 當交易類型變更時，更新分類選項
    typeSelect.addEventListener('change', function() {
        loadCategories(this.value);
    });
    
    // 表單提交事件
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        saveTransaction();
    });
}

/**
 * 載入分類選項
 * @param {string} type - 交易類型 (expense 或 income)
 */
function loadCategories(type = 'expense') {
    const categorySelect = document.getElementById('transaction-category');
    
    // 清空現有選項
    categorySelect.innerHTML = '<option value="">請選擇分類</option>';
    
    // 載入分類選項
    fetch(`/api/categories?type=${type}`)
        .then(response => response.json())
        .then(data => {
            data.forEach(category => {
                const option = document.createElement('option');
                option.value = category.category_id;
                option.textContent = category.icon ? `${category.icon} ${category.name}` : category.name;
                categorySelect.appendChild(option);
            });
        })
        .catch(error => {
            console.error('載入分類失敗:', error);
        });
}

/**
 * 載入帳戶選項
 */
function loadAccounts() {
    const accountSelect = document.getElementById('transaction-account');
    
    // 清空現有選項
    accountSelect.innerHTML = '<option value="">請選擇帳戶</option>';
    
    // 載入帳戶選項
    fetch('/api/accounts')
        .then(response => response.json())
        .then(data => {
            data.forEach(account => {
                const option = document.createElement('option');
                option.value = account.account_id;
                option.textContent = account.name;
                accountSelect.appendChild(option);
            });
        })
        .catch(error => {
            console.error('載入帳戶失敗:', error);
        });
}

/**
 * 顯示新增交易模態框
 */
function showAddTransactionModal() {
    // 初始化模態框
    initializeTransactionModal();
    
    // 設置模態框標題
    document.getElementById('transaction-modal-title').textContent = '新增交易';
    
    // 重置表單
    document.getElementById('transaction-id').value = 'new';
    document.getElementById('transaction-type').value = 'expense';
    document.getElementById('transaction-date').value = new Date().toISOString().split('T')[0];
    document.getElementById('transaction-amount').value = '';
    document.getElementById('transaction-memo').value = '';
    
    // 載入分類和帳戶選項
    loadCategories('expense');
    loadAccounts();
    
    // 顯示模態框
    document.getElementById('transaction-modal').style.display = 'block';
}

/**
 * 顯示編輯交易模態框
 * @param {number} id - 交易記錄ID
 */
function showEditTransactionModal(id) {
    // 初始化模態框
    initializeTransactionModal();
    
    // 設置模態框標題
    document.getElementById('transaction-modal-title').textContent = '編輯交易';
    
    // 獲取交易記錄詳情
    fetch(`/api/transactions/${id}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('獲取交易記錄失敗');
            }
            return response.json();
        })
        .then(transaction => {
            // 填充表單數據
            document.getElementById('transaction-id').value = transaction.transaction_id;
            document.getElementById('transaction-type').value = transaction.type || 'expense';
            document.getElementById('transaction-date').value = transaction.date || '';
            document.getElementById('transaction-amount').value = transaction.amount || '';
            document.getElementById('transaction-memo').value = transaction.description || '';
            
            // 載入分類和帳戶選項
            loadCategories(transaction.type);
            loadAccounts();
            
            // 延遲設置選中項，等待選項載入完成
            setTimeout(() => {
                const categorySelect = document.getElementById('transaction-category');
                const accountSelect = document.getElementById('transaction-account');
                
                if (transaction.category_id) {
                    for(let i = 0; i < categorySelect.options.length; i++) {
                        if (categorySelect.options[i].value == transaction.category_id) {
                            categorySelect.selectedIndex = i;
                            break;
                        }
                    }
                }
                
                if (transaction.account_id) {
                    for(let i = 0; i < accountSelect.options.length; i++) {
                        if (accountSelect.options[i].value == transaction.account_id) {
                            accountSelect.selectedIndex = i;
                            break;
                        }
                    }
                }
            }, 500);
            
            // 顯示模態框
            document.getElementById('transaction-modal').style.display = 'block';
        })
        .catch(error => {
            console.error('獲取交易記錄失敗:', error);
            alert('獲取交易記錄失敗: ' + error.message);
        });
}

/**
 * 保存交易記錄
 */
function saveTransaction() {
    // 獲取表單數據
    const transactionId = document.getElementById('transaction-id').value;
    const type = document.getElementById('transaction-type').value;
    const date = document.getElementById('transaction-date').value;
    const amount = document.getElementById('transaction-amount').value;
    const categoryId = document.getElementById('transaction-category').value;
    const accountId = document.getElementById('transaction-account').value;
    const memo = document.getElementById('transaction-memo').value;
    
    // 表單驗證
    if (!date || !amount || !categoryId || !accountId) {
        alert('請填寫所有必填欄位');
        return;
    }
    
    // 準備請求數據
    const transactionData = {
        type,
        date,
        amount: parseFloat(amount),
        category_id: categoryId,
        account_id: accountId,
        memo
    };
    
    // 確定請求方法和URL
    const isNew = transactionId === 'new';
    const method = isNew ? 'POST' : 'PUT';
    const url = isNew ? '/api/transactions' : `/api/transactions/${transactionId}`;
    
    // 發送請求
    fetch(url, {
        method,
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(transactionData)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => {
                throw new Error(err.error || '保存交易記錄失敗');
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // 關閉模態框
            document.getElementById('transaction-modal').style.display = 'none';
            
            // 重新載入交易記錄
            loadTransactionsData();
            
            // 如果在總覽頁面，也重新載入總覽數據
            if (document.getElementById('overview').classList.contains('active')) {
                loadOverviewData();
            }
            
            // 顯示成功訊息
            alert(isNew ? '交易記錄新增成功' : '交易記錄更新成功');
        } else {
            alert(data.error || '操作失敗');
        }
    })
    .catch(error => {
        console.error('保存交易記錄失敗:', error);
        alert('保存交易記錄失敗: ' + error.message);
    });
}

/**
 * 刪除交易記錄
 * @param {number} id - 交易記錄ID
 */
function deleteTransaction(id) {
    if (!confirm('確定要刪除此交易記錄嗎？')) {
        return;
    }
    
    fetch(`/api/transactions/${id}`, {
        method: 'DELETE'
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => {
                throw new Error(err.error || '刪除交易記錄失敗');
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // 重新載入交易記錄
            loadTransactionsData();
            
            // 如果在總覽頁面，也重新載入總覽數據
            if (document.getElementById('overview').classList.contains('active')) {
                loadOverviewData();
            }
            
            // 顯示成功訊息
            alert('交易記錄已刪除');
        } else {
            alert(data.error || '刪除失敗');
        }
    })
    .catch(error => {
        console.error('刪除交易記錄失敗:', error);
        alert('刪除交易記錄失敗: ' + error.message);
    });
}

/**
 * 初始化交易記錄頁面
 */
function initTransactionsPage() {
    // 添加新增按鈕的點擊事件
    const addTransactionBtn = document.getElementById('add-transaction');
    if (addTransactionBtn) {
        addTransactionBtn.addEventListener('click', showAddTransactionModal);
    }
    
    // 添加篩選條件的變更事件
    const typeFilter = document.getElementById('transaction-type');
    if (typeFilter) {
        typeFilter.addEventListener('change', loadTransactionsData);
    }
    
    const dateRangeFilter = document.getElementById('date-range');
    if (dateRangeFilter) {
        dateRangeFilter.addEventListener('change', function() {
            const customDateRange = document.getElementById('custom-date-range');
            if (this.value === 'custom' && customDateRange) {
                customDateRange.style.display = 'block';
            } else if (customDateRange) {
                customDateRange.style.display = 'none';
            }
            loadTransactionsData();
        });
    }
    
    const applyFilterBtn = document.getElementById('apply-filter');
    if (applyFilterBtn) {
        applyFilterBtn.addEventListener('click', loadTransactionsData);
    }
    
    // 初始載入交易記錄數據
    loadTransactionsData();
}

// 當切換到交易記錄頁時初始化頁面
document.addEventListener('DOMContentLoaded', function() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', function() {
            if (this.dataset.target === 'transactions') {
                setTimeout(initTransactionsPage, 100);
            }
        });
    });
    
    // 如果初始頁面是交易記錄頁，立即初始化
    if (document.getElementById('transactions').classList.contains('active')) {
        initTransactionsPage();
    }
});

/**
 * 載入交易記錄數據
 */
function loadTransactionsData() {
    const transactionsBody = document.getElementById('transactions-body');
    if (!transactionsBody) {
        console.error('找不到交易記錄表格');
        return;
    }
    
    // 顯示載入中
    transactionsBody.innerHTML = '<tr><td colspan="7" class="loading-text">載入中...</td></tr>';
    
    // 獲取篩選條件
    const typeFilter = document.getElementById('transaction-type');
    const dateRangeFilter = document.getElementById('date-range');
    const startDateInput = document.getElementById('start-date');
    const endDateInput = document.getElementById('end-date');
    
    let type = typeFilter ? typeFilter.value : 'all';
    let dateRange = dateRangeFilter ? dateRangeFilter.value : 'this-month';
    let startDate = startDateInput ? startDateInput.value : '';
    let endDate = endDateInput ? endDateInput.value : '';
    
    // 構建API請求URL
    let apiUrl = `/api/transactions?type=${type}&date_range=${dateRange}`;
    
    if (dateRange === 'custom' && startDate && endDate) {
        apiUrl += `&start_date=${startDate}&end_date=${endDate}`;
    }
    
    // 獲取交易記錄數據
    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            if (!data.transactions || data.transactions.length === 0) {
                transactionsBody.innerHTML = '<tr><td colspan="7" class="empty-text">沒有符合條件的交易記錄</td></tr>';
                return;
            }
            
            // 渲染交易記錄
            let html = '';
            data.transactions.forEach(transaction => {
                const date = transaction.date_formatted || transaction.date;
                const type = transaction.type === 'expense' ? '支出' : '收入';
                const category = transaction.category_name || '未分類';
                const item = transaction.description || '';
                const amount = formatCurrency(transaction.amount);
                const account = transaction.account_name || '默認帳戶';
                
                html += `
                <tr>
                    <td>${date}</td>
                    <td>${type}</td>
                    <td>${category}</td>
                    <td>${item}</td>
                    <td>${amount}</td>
                    <td>${account}</td>
                    <td>
                        <button onclick="showEditTransactionModal(${transaction.transaction_id})" class="edit-btn">編輯</button>
                        <button onclick="deleteTransaction(${transaction.transaction_id})" class="delete-btn">刪除</button>
                    </td>
                </tr>
                `;
            });
            
            transactionsBody.innerHTML = html;
            
            // 更新分頁
            updatePagination(data.pagination);
        })
        .catch(error => {
            console.error('載入交易記錄失敗:', error);
            transactionsBody.innerHTML = '<tr><td colspan="7" class="error-text">載入失敗: ' + error.message + '</td></tr>';
        });
}

/**
 * 更新分頁控制
 * @param {Object} pagination - 分頁數據
 */
function updatePagination(pagination) {
    if (!pagination) return;
    
    const prevPageBtn = document.getElementById('prev-page');
    const nextPageBtn = document.getElementById('next-page');
    const pageInfo = document.getElementById('page-info');
    
    if (prevPageBtn && pageInfo && nextPageBtn) {
        pageInfo.textContent = `第 ${pagination.current_page} 頁 / 共 ${pagination.total_pages} 頁`;
        
        prevPageBtn.disabled = !pagination.has_prev;
        nextPageBtn.disabled = !pagination.has_next;
        
        prevPageBtn.onclick = pagination.has_prev ? () => {
            // 切換到上一頁
            const startDateInput = document.getElementById('start-date');
            const endDateInput = document.getElementById('end-date');
            
            let apiUrl = `/api/transactions?page=${pagination.current_page - 1}`;
            
            if (startDateInput && startDateInput.value && endDateInput && endDateInput.value) {
                apiUrl += `&start_date=${startDateInput.value}&end_date=${endDateInput.value}`;
            }
            
            fetch(apiUrl)
                .then(response => response.json())
                .then(data => {
                    // 重新渲染交易記錄
                    renderTransactions(data);
                })
                .catch(error => {
                    console.error('載入交易記錄失敗:', error);
                });
        } : null;
        
        nextPageBtn.onclick = pagination.has_next ? () => {
            // 切換到下一頁
            const startDateInput = document.getElementById('start-date');
            const endDateInput = document.getElementById('end-date');
            
            let apiUrl = `/api/transactions?page=${pagination.current_page + 1}`;
            
            if (startDateInput && startDateInput.value && endDateInput && endDateInput.value) {
                apiUrl += `&start_date=${startDateInput.value}&end_date=${endDateInput.value}`;
            }
            
            fetch(apiUrl)
                .then(response => response.json())
                .then(data => {
                    // 重新渲染交易記錄
                    renderTransactions(data);
                })
                .catch(error => {
                    console.error('載入交易記錄失敗:', error);
                });
        } : null;
    }
}

/**
 * 渲染交易記錄列表
 * @param {Object} data - 包含交易記錄和分頁信息的數據
 */
function renderTransactions(data) {
    const transactionsBody = document.getElementById('transactions-body');
    if (!transactionsBody) return;
    
    if (!data.transactions || data.transactions.length === 0) {
        transactionsBody.innerHTML = '<tr><td colspan="7" class="empty-text">沒有符合條件的交易記錄</td></tr>';
        return;
    }
    
    // 渲染交易記錄
    let html = '';
    data.transactions.forEach(transaction => {
        const date = transaction.date_formatted || transaction.date;
        const type = transaction.type === 'expense' ? '支出' : '收入';
        const category = transaction.category_name || '未分類';
        const item = transaction.description || '';
        const amount = formatCurrency(transaction.amount);
        const account = transaction.account_name || '默認帳戶';
        
        html += `
        <tr>
            <td>${date}</td>
            <td>${type}</td>
            <td>${category}</td>
            <td>${item}</td>
            <td>${amount}</td>
            <td>${account}</td>
            <td>
                <button onclick="showEditTransactionModal(${transaction.transaction_id})" class="edit-btn">編輯</button>
                <button onclick="deleteTransaction(${transaction.transaction_id})" class="delete-btn">刪除</button>
            </td>
        </tr>
        `;
    });
    
    transactionsBody.innerHTML = html;
    
    // 更新分頁
    updatePagination(data.pagination);
}

/**
 * 格式化貨幣
 * @param {number} amount - 金額
 * @returns {string} 格式化後的金額字符串
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('zh-TW', {
        style: 'currency',
        currency: 'TWD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount);
}

/**
 * 載入分類管理頁數據
 */
function loadCategoriesPageData() {
    // 獲取分類類型過濾器
    const categoryTypeFilter = document.getElementById('category-type-filter');
    const type = categoryTypeFilter ? categoryTypeFilter.value : 'expense';
    
    // 註冊類型過濾器變更事件
    if (categoryTypeFilter) {
        categoryTypeFilter.addEventListener('change', function() {
            loadCategoriesData(this.value);
        });
    }
    
    // 註冊新增分類按鈕事件
    const addCategoryBtn = document.getElementById('add-category');
    if (addCategoryBtn) {
        addCategoryBtn.addEventListener('click', function() {
            showAddCategoryModal();
        });
    }
    
    // 載入分類數據
    loadCategoriesData(type);
    
    // 初始化分類模態框
    initializeCategoryModal();
}

/**
 * 初始化分類模態框
 */
function initializeCategoryModal() {
    const modal = document.getElementById('category-modal');
    if (!modal) return;
    
    // 關閉按鈕事件
    const closeBtn = document.getElementById('close-category-modal');
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            modal.style.display = 'none';
        });
    }
    
    // 取消按鈕事件
    const cancelBtn = document.getElementById('cancel-category');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function() {
            modal.style.display = 'none';
        });
    }
    
    // 表單提交事件
    const form = document.getElementById('category-form');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            saveCategory();
        });
    }
    
    // 點擊表情符號事件
    const emojis = document.querySelectorAll('.emoji');
    emojis.forEach(emoji => {
        emoji.addEventListener('click', function() {
            const emojiIcon = this.getAttribute('data-emoji');
            document.getElementById('category-icon').value = emojiIcon;
        });
    });
    
    // 點擊模態框外部關閉
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
}

/**
 * 載入分類數據
 * @param {string} type - 分類類型，expense 或 income
 */
function loadCategoriesData(type = 'expense') {
    const categoriesBody = document.getElementById('categories-body');
    if (!categoriesBody) return;
    
    // 顯示載入中
    categoriesBody.innerHTML = '<tr><td colspan="4" class="loading-text">載入中...</td></tr>';
    
    // 獲取分類數據
    fetch(`/api/categories?type=${type}`)
        .then(response => response.json())
        .then(categories => {
            if (!categories || categories.length === 0) {
                categoriesBody.innerHTML = '<tr><td colspan="4" class="empty-text">沒有分類數據</td></tr>';
                return;
            }
            
            // 渲染分類列表
            let html = '';
            categories.forEach(category => {
                const isDefault = category.is_default === 1;
                const isSystemDefault = isDefault && !category.user_id;
                
                html += `
                <tr data-category-id="${category.category_id}">
                    <td class="category-icon">${category.icon || ''}</td>
                    <td>${category.name}</td>
                    <td>
                        <span class="category-type ${category.type}">
                            ${category.type === 'expense' ? '支出' : '收入'}
                        </span>
                    </td>
                    <td>
                `;
                
                // 系統默認分類不顯示操作按鈕
                if (!isSystemDefault) {
                    html += `
                        <button class="edit-btn" onclick="showEditCategoryModal(${category.category_id})">編輯</button>
                        <button class="delete-btn" onclick="deleteCategory(${category.category_id})">刪除</button>
                    `;
                } else {
                    html += `<span class="default-badge">系統預設</span>`;
                }
                
                html += `
                    </td>
                </tr>
                `;
            });
            
            categoriesBody.innerHTML = html;
        })
        .catch(error => {
            console.error('載入分類失敗:', error);
            categoriesBody.innerHTML = `<tr><td colspan="4" class="error-text">載入失敗: ${error.message}</td></tr>`;
        });
}

/**
 * 顯示新增分類模態框
 */
function showAddCategoryModal() {
    // 獲取當前過濾類型
    const categoryTypeFilter = document.getElementById('category-type-filter');
    const type = categoryTypeFilter ? categoryTypeFilter.value : 'expense';
    
    // 設置模態框標題
    document.getElementById('category-modal-title').textContent = '新增分類';
    
    // 重置表單
    document.getElementById('category-id').value = 'new';
    document.getElementById('category-type').value = type;
    document.getElementById('category-name').value = '';
    document.getElementById('category-icon').value = '';
    
    // 啟用類型選擇（新增時可以選擇類型）
    document.getElementById('category-type').disabled = false;
    
    // 顯示模態框
    document.getElementById('category-modal').style.display = 'block';
}

/**
 * 顯示編輯分類模態框
 * @param {number} categoryId - 分類ID
 */
function showEditCategoryModal(categoryId) {
    // 獲取分類詳情
    fetch(`/api/categories?type=all`)
        .then(response => response.json())
        .then(categories => {
            const category = categories.find(c => c.category_id === categoryId);
            if (!category) {
                alert('找不到該分類');
                return;
            }
            
            // 設置模態框標題
            document.getElementById('category-modal-title').textContent = '編輯分類';
            
            // 填充表單
            document.getElementById('category-id').value = category.category_id;
            document.getElementById('category-type').value = category.type;
            document.getElementById('category-name').value = category.name;
            document.getElementById('category-icon').value = category.icon || '';
            
            // 禁用類型選擇（編輯時不允許變更類型）
            document.getElementById('category-type').disabled = true;
            
            // 顯示模態框
            document.getElementById('category-modal').style.display = 'block';
        })
        .catch(error => {
            console.error('獲取分類詳情失敗:', error);
            alert('獲取分類詳情失敗: ' + error.message);
        });
}

/**
 * 保存分類
 */
function saveCategory() {
    // 獲取表單數據
    const categoryId = document.getElementById('category-id').value;
    const type = document.getElementById('category-type').value;
    const name = document.getElementById('category-name').value;
    const icon = document.getElementById('category-icon').value;
    
    // 表單驗證
    if (!name) {
        alert('請輸入分類名稱');
        return;
    }
    
    // 準備請求數據
    const categoryData = {
        type,
        name,
        icon
    };
    
    // 確定請求方法和URL
    const isNew = categoryId === 'new';
    const method = isNew ? 'POST' : 'PUT';
    const url = isNew ? '/api/categories' : `/api/categories/${categoryId}`;
    
    // 發送請求
    fetch(url, {
        method,
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(categoryData)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => {
                throw new Error(err.error || '保存分類失敗');
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // 關閉模態框
            document.getElementById('category-modal').style.display = 'none';
            
            // 重新載入分類數據
            const categoryTypeFilter = document.getElementById('category-type-filter');
            const currentType = categoryTypeFilter ? categoryTypeFilter.value : 'expense';
            loadCategoriesData(currentType);
            
            // 顯示成功訊息
            alert(isNew ? '分類新增成功' : '分類更新成功');
            
            // 重置類型選擇器
            document.getElementById('category-type').disabled = false;
        } else {
            alert(data.error || '操作失敗');
        }
    })
    .catch(error => {
        console.error('保存分類失敗:', error);
        alert('保存分類失敗: ' + error.message);
    });
}

/**
 * 刪除分類
 * @param {number} categoryId - 分類ID
 */
function deleteCategory(categoryId) {
    if (!confirm('確定要刪除此分類嗎？')) {
        return;
    }
    
    fetch(`/api/categories/${categoryId}`, {
        method: 'DELETE'
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => {
                throw new Error(err.error || '刪除分類失敗');
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // 重新載入分類數據
            const categoryTypeFilter = document.getElementById('category-type-filter');
            const currentType = categoryTypeFilter ? categoryTypeFilter.value : 'expense';
            loadCategoriesData(currentType);
            
            // 顯示成功訊息
            alert('分類已刪除');
        } else {
            alert(data.error || '刪除失敗');
        }
    })
    .catch(error => {
        console.error('刪除分類失敗:', error);
        alert('刪除分類失敗: ' + error.message);
    });
} 

/**
 * 載入提醒管理頁數據
 */
function loadRemindersPageData() {
    // 獲取提醒狀態過濾器
    const reminderStatus = document.getElementById('reminder-status');
    let status = reminderStatus ? reminderStatus.value : 'pending';
    
    // 註冊狀態過濾器變更事件
    if (reminderStatus) {
        reminderStatus.addEventListener('change', function() {
            loadRemindersData(this.value);
        });
    }
    
    // 註冊新增提醒按鈕事件
    const addReminderBtn = document.getElementById('add-reminder');
    if (addReminderBtn) {
        addReminderBtn.addEventListener('click', function() {
            showAddReminderModal();
        });
    }
    
    // 初始化提醒模態框
    initializeReminderModal();
    
    // 載入提醒數據
    loadRemindersData(status);
}

/**
 * 初始化提醒模態框
 */
function initializeReminderModal() {
    const modal = document.getElementById('reminder-modal');
    if (!modal) return;
    
    // 獲取關閉按鈕
    const closeBtn = modal.querySelector('.close-btn');
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            modal.style.display = 'none';
        });
    }
    
    // 點擊模態框外部關閉
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
    
    // 表單提交事件
    const form = document.getElementById('reminder-form');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            saveReminder();
        });
    }
    
    // 設置默認日期和時間
    const dateInput = document.getElementById('reminder-date');
    const timeInput = document.getElementById('reminder-time');
    if (dateInput && timeInput) {
        const now = new Date();
        
        // 設置默認日期為今天
        const today = now.toISOString().split('T')[0];
        dateInput.value = today;
        
        // 設置默認時間為當前時間的下一個整點
        const nextHour = new Date(now.getFullYear(), now.getMonth(), now.getDate(), now.getHours() + 1, 0);
        const hours = nextHour.getHours().toString().padStart(2, '0');
        const minutes = nextHour.getMinutes().toString().padStart(2, '0');
        timeInput.value = `${hours}:${minutes}`;
    }
}

/**
 * 載入提醒數據
 * @param {string} status - 提醒狀態，pending/completed/all
 */
function loadRemindersData(status = 'pending') {
    const remindersList = document.getElementById('reminders-list');
    if (!remindersList) return;
    
    // 顯示載入中
    remindersList.innerHTML = '<div class="loading-text">載入中...</div>';
    
    // 獲取提醒數據
    fetch(`/api/reminders?status=${status}`)
        .then(response => response.json())
        .then(reminders => {
            if (!reminders || reminders.length === 0) {
                remindersList.innerHTML = '<div class="empty-text">沒有提醒數據</div>';
                return;
            }
            
            // 渲染提醒列表
            let html = '';
            reminders.forEach(reminder => {
                // 格式化日期和時間
                const reminderDate = new Date(reminder.datetime);
                const dateFormatted = formatDate(reminderDate);
                const timeFormatted = reminderDate.toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' });
                
                const isPending = reminder.status === 'pending';
                const statusClass = isPending ? 'pending' : 'completed';
                
                // 格式化重複方式
                let repeatText = '';
                switch (reminder.repeat_type) {
                    case 'daily':
                        repeatText = '每天';
                        break;
                    case 'weekly':
                        repeatText = '每週';
                        break;
                    case 'monthly':
                        repeatText = '每月';
                        break;
                    default:
                        repeatText = '不重複';
                }
                
                // 格式化提前提醒時間
                let notifyBeforeText = '';
                if (reminder.notify_before > 0) {
                    if (reminder.notify_before < 60) {
                        notifyBeforeText = `提前 ${reminder.notify_before} 分鐘提醒`;
                    } else {
                        const hours = Math.floor(reminder.notify_before / 60);
                        notifyBeforeText = `提前 ${hours} 小時提醒`;
                    }
                }
                
                html += `
                <div class="reminder-item ${statusClass}" data-reminder-id="${reminder.reminder_id}">
                    <div class="reminder-content">${reminder.content}</div>
                    <div class="reminder-time">
                        <span class="date">${dateFormatted}</span>
                        <span class="time">${timeFormatted}</span>
                    </div>
                    ${repeatText ? `<div class="reminder-repeat">${repeatText}</div>` : ''}
                    ${notifyBeforeText ? `<div class="reminder-notify-before">${notifyBeforeText}</div>` : ''}
                    <div class="reminder-actions">
                `;
                
                if (isPending) {
                    html += `
                        <button class="complete-btn" onclick="completeReminder(${reminder.reminder_id})">完成</button>
                        <button class="edit-btn" onclick="showEditReminderModal(${reminder.reminder_id})">編輯</button>
                    `;
                }
                
                html += `
                        <button class="delete-btn" onclick="deleteReminder(${reminder.reminder_id})">刪除</button>
                    </div>
                </div>
                `;
            });
            
            remindersList.innerHTML = html;
        })
        .catch(error => {
            console.error('載入提醒失敗:', error);
            remindersList.innerHTML = `<div class="error-text">載入失敗: ${error.message}</div>`;
        });
}

/**
 * 顯示新增提醒模態框
 */
function showAddReminderModal() {
    const modal = document.getElementById('reminder-modal');
    if (!modal) return;
    
    // 設置模態框標題
    const modalTitle = modal.querySelector('h3');
    if (modalTitle) {
        modalTitle.textContent = '新增提醒';
    }
    
    // 重置表單
    const form = document.getElementById('reminder-form');
    if (form) {
        form.reset();
        
        // 添加隱藏字段，設置為新增模式
        let reminderIdInput = form.querySelector('input[name="reminder-id"]');
        if (!reminderIdInput) {
            reminderIdInput = document.createElement('input');
            reminderIdInput.type = 'hidden';
            reminderIdInput.name = 'reminder-id';
            form.appendChild(reminderIdInput);
        }
        reminderIdInput.value = 'new';
        
        // 設置默認日期和時間
        const dateInput = document.getElementById('reminder-date');
        const timeInput = document.getElementById('reminder-time');
        if (dateInput && timeInput) {
            const now = new Date();
            
            // 設置默認日期為今天
            const today = now.toISOString().split('T')[0];
            dateInput.value = today;
            
            // 設置默認時間為當前時間的下一個整點
            const nextHour = new Date(now.getFullYear(), now.getMonth(), now.getDate(), now.getHours() + 1, 0);
            const hours = nextHour.getHours().toString().padStart(2, '0');
            const minutes = nextHour.getMinutes().toString().padStart(2, '0');
            timeInput.value = `${hours}:${minutes}`;
        }
    }
    
    // 顯示模態框
    modal.style.display = 'block';
}

/**
 * 顯示編輯提醒模態框
 * @param {number} reminderId - 提醒ID
 */
function showEditReminderModal(reminderId) {
    const modal = document.getElementById('reminder-modal');
    if (!modal) return;
    
    // 設置模態框標題
    const modalTitle = modal.querySelector('h3');
    if (modalTitle) {
        modalTitle.textContent = '編輯提醒';
    }
    
    // 獲取提醒詳情
    fetch(`/api/reminders?status=all`)
        .then(response => response.json())
        .then(reminders => {
            const reminder = reminders.find(r => r.reminder_id === reminderId);
            if (!reminder) {
                alert('找不到該提醒');
                return;
            }
            
            // 獲取表單
            const form = document.getElementById('reminder-form');
            if (!form) return;
            
            // 添加隱藏字段，設置為編輯模式
            let reminderIdInput = form.querySelector('input[name="reminder-id"]');
            if (!reminderIdInput) {
                reminderIdInput = document.createElement('input');
                reminderIdInput.type = 'hidden';
                reminderIdInput.name = 'reminder-id';
                form.appendChild(reminderIdInput);
            }
            reminderIdInput.value = reminder.reminder_id;
            
            // 解析日期時間
            const dateTime = new Date(reminder.datetime);
            const dateStr = dateTime.toISOString().split('T')[0];
            const hours = dateTime.getHours().toString().padStart(2, '0');
            const minutes = dateTime.getMinutes().toString().padStart(2, '0');
            const timeStr = `${hours}:${minutes}`;
            
            // 填充表單數據
            document.getElementById('reminder-content').value = reminder.content;
            document.getElementById('reminder-date').value = dateStr;
            document.getElementById('reminder-time').value = timeStr;
            document.getElementById('reminder-repeat').value = reminder.repeat_type || 'none';
            document.getElementById('reminder-before').value = reminder.notify_before || '0';
            
            // 顯示模態框
            modal.style.display = 'block';
        })
        .catch(error => {
            console.error('獲取提醒詳情失敗:', error);
            alert('獲取提醒詳情失敗: ' + error.message);
        });
}

/**
 * 保存提醒
 */
function saveReminder() {
    // 獲取表單數據
    const form = document.getElementById('reminder-form');
    if (!form) return;
    
    const reminderId = form.querySelector('input[name="reminder-id"]')?.value || 'new';
    const content = document.getElementById('reminder-content').value;
    const date = document.getElementById('reminder-date').value;
    const time = document.getElementById('reminder-time').value;
    const repeatType = document.getElementById('reminder-repeat').value;
    const notifyBefore = parseInt(document.getElementById('reminder-before').value || '0', 10);
    
    // 表單驗證
    if (!content || !date || !time) {
        alert('請填寫必要欄位');
        return;
    }
    
    // 合併日期和時間為ISO格式
    const datetime = `${date}T${time}:00`;
    
    // 準備數據
    const reminderData = {
        content,
        datetime,
        repeat_type: repeatType,
        notify_before: notifyBefore
    };
    
    // 確定API路徑和方法
    const isNew = reminderId === 'new';
    const method = isNew ? 'POST' : 'PUT';
    const url = isNew ? '/api/reminders' : `/api/reminders/${reminderId}`;
    
    // 發送請求
    fetch(url, {
        method,
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(reminderData)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => {
                throw new Error(err.error || '保存提醒失敗');
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // 關閉模態框
            document.getElementById('reminder-modal').style.display = 'none';
            
            // 重新載入提醒列表
            const reminderStatus = document.getElementById('reminder-status');
            loadRemindersData(reminderStatus?.value || 'pending');
            
            // 顯示成功訊息
            alert(isNew ? '提醒已新增' : '提醒已更新');
        } else {
            alert(data.error || '操作失敗');
        }
    })
    .catch(error => {
        console.error('保存提醒失敗:', error);
        alert('保存提醒失敗: ' + error.message);
    });
}

/**
 * 完成提醒
 * @param {number} reminderId - 提醒ID
 */
function completeReminder(reminderId) {
    fetch(`/api/reminders/${reminderId}/complete`, {
        method: 'POST'
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => {
                throw new Error(err.error || '標記提醒失敗');
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // 重新載入提醒列表
            const reminderStatus = document.getElementById('reminder-status');
            loadRemindersData(reminderStatus?.value || 'pending');
            
            // 顯示成功訊息
            alert('提醒已標記為完成');
        } else {
            alert(data.error || '操作失敗');
        }
    })
    .catch(error => {
        console.error('標記提醒完成失敗:', error);
        alert('標記提醒完成失敗: ' + error.message);
    });
}

/**
 * 刪除提醒
 * @param {number} reminderId - 提醒ID
 */
function deleteReminder(reminderId) {
    if (!confirm('確定要刪除此提醒嗎？')) {
        return;
    }
    
    fetch(`/api/reminders/${reminderId}`, {
        method: 'DELETE'
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => {
                throw new Error(err.error || '刪除提醒失敗');
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // 重新載入提醒列表
            const reminderStatus = document.getElementById('reminder-status');
            loadRemindersData(reminderStatus?.value || 'pending');
            
            // 顯示成功訊息
            alert('提醒已刪除');
        } else {
            alert(data.error || '刪除失敗');
        }
    })
    .catch(error => {
        console.error('刪除提醒失敗:', error);
        alert('刪除提醒失敗: ' + error.message);
    });
}

/**
 * 初始化同步功能
 */
function initSyncFeature() {
    // 獲取同步按鈕元素
    const syncButton = document.getElementById('sync-button');
    if (!syncButton) return;

    // 檢查同步狀態
    checkSyncStatus();

    // 為同步按鈕添加點擊事件
    syncButton.addEventListener('click', function() {
        synchronizeData();
    });
}

/**
 * 檢查同步狀態
 */
function checkSyncStatus() {
    // 顯示載入中狀態
    const syncStatusElement = document.getElementById('sync-status');
    if (syncStatusElement) {
        syncStatusElement.innerHTML = '<span class="loading">檢查同步狀態...</span>';
    }

    // 發送請求檢查同步狀態
    fetch('/api/sync/status')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 更新同步狀態顯示
                if (syncStatusElement) {
                    if (data.lastSync) {
                        syncStatusElement.innerHTML = `上次同步: ${data.timeSinceLastSync}`;
                        
                        // 如果需要同步，顯示提示
                        if (data.needsSync) {
                            syncStatusElement.innerHTML += ' <span class="sync-needed">(建議同步)</span>';
                        }
                    } else {
                        syncStatusElement.innerHTML = '尚未同步';
                    }
                }
            } else {
                console.error('獲取同步狀態失敗:', data.error);
                if (syncStatusElement) {
                    syncStatusElement.innerHTML = '同步狀態未知';
                }
            }
        })
        .catch(error => {
            console.error('檢查同步狀態時發生錯誤:', error);
            if (syncStatusElement) {
                syncStatusElement.innerHTML = '同步狀態檢查失敗';
            }
        });
}

/**
 * 執行數據同步
 */
function synchronizeData() {
    // 顯示同步中狀態
    const syncButton = document.getElementById('sync-button');
    const syncStatusElement = document.getElementById('sync-status');
    
    if (syncButton) {
        syncButton.disabled = true;
        syncButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 同步中...';
    }
    
    if (syncStatusElement) {
        syncStatusElement.innerHTML = '<span class="loading">正在同步數據...</span>';
    }

    // 顯示同步進度提示
    showToast('正在進行數據同步，請稍候...', 'info');
    
    // 發送同步請求
    fetch('/api/sync', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 同步成功
            showToast('數據同步成功！', 'success');
            console.log('同步結果:', data.syncResults);
            
            // 更新同步狀態和按鈕
            if (syncStatusElement) {
                syncStatusElement.innerHTML = `上次同步: 剛剛`;
            }
            
            // 重新加載當前頁面的數據
            reloadCurrentPageData();
        } else {
            // 同步失敗
            showToast(`同步失敗: ${data.error}`, 'error');
            console.error('同步失敗:', data.error);
            
            if (syncStatusElement) {
                syncStatusElement.innerHTML = '同步失敗';
            }
        }
    })
    .catch(error => {
        // 捕獲異常
        showToast('同步過程中發生錯誤，請稍後再試', 'error');
        console.error('同步時發生錯誤:', error);
        
        if (syncStatusElement) {
            syncStatusElement.innerHTML = '同步失敗';
        }
    })
    .finally(() => {
        // 恢復按鈕狀態
        if (syncButton) {
            syncButton.disabled = false;
            syncButton.innerHTML = '<i class="fas fa-sync-alt"></i> 同步數據';
        }
    });
}

/**
 * 重新加載當前頁面的數據
 */
function reloadCurrentPageData() {
    // 判斷當前活躍的頁面標籤
    const activeTab = document.querySelector('.nav-link.active');
    if (!activeTab) return;
    
    const tabId = activeTab.getAttribute('href');
    
    // 根據不同頁面重新加載數據
    switch (tabId) {
        case '#overview':
            loadAccountsData();
            loadOverviewData();
            break;
        case '#transactions':
            const statusFilter = document.getElementById('transaction-type-filter');
            const status = statusFilter ? statusFilter.value : 'all';
            loadTransactionsData(status);
            break;
        case '#categories':
            const categoryTypeFilter = document.getElementById('category-type-filter');
            const type = categoryTypeFilter ? categoryTypeFilter.value : 'expense';
            loadCategoriesData(type);
            break;
        case '#reminders':
            const reminderStatusFilter = document.getElementById('reminder-status-filter');
            const reminderStatus = reminderStatusFilter ? reminderStatusFilter.value : 'pending';
            loadRemindersData(reminderStatus);
            break;
        case '#reports':
            loadReportData();
            break;
    }
}

// 在頁面載入時初始化同步功能
document.addEventListener('DOMContentLoaded', function() {
    // 初始化同步功能
    initSyncFeature();
    
    // ... existing code ...
});

/**
 * 載入報表頁面數據
 */
function loadReportData() {
    // 初始化報表頁面過濾器和事件
    initReportFilters();
    
    // 預設載入本月支出報表
    loadReportByType('expense', 'this-month');
}

/**
 * 初始化報表頁面過濾器和事件
 */
function initReportFilters() {
    const reportType = document.getElementById('report-type');
    const reportDateRange = document.getElementById('report-date-range');
    const reportCustomDateRange = document.getElementById('report-custom-date-range');
    const reportStartDate = document.getElementById('report-start-date');
    const reportEndDate = document.getElementById('report-end-date');
    const applyReportFilter = document.getElementById('apply-report-filter');
    const exportReportExcel = document.getElementById('export-report-excel');
    const exportReportPdf = document.getElementById('export-report-pdf');
    
    if (!reportType || !reportDateRange || !applyReportFilter) return;
    
    // 監聽日期範圍變更事件
    reportDateRange.addEventListener('change', function() {
        if (this.value === 'custom') {
            reportCustomDateRange.style.display = 'flex';
            // 設置預設日期 (本月)
            const today = new Date();
            const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
            const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0);
            
            reportStartDate.value = formatDateForInput(firstDay);
            reportEndDate.value = formatDateForInput(lastDay);
        } else {
            reportCustomDateRange.style.display = 'none';
        }
    });
    
    // 監聽套用過濾器按鈕點擊事件
    applyReportFilter.addEventListener('click', function() {
        const type = reportType.value;
        const dateRange = reportDateRange.value;
        
        loadReportByType(type, dateRange, reportStartDate.value, reportEndDate.value);
    });
    
    // 監聽匯出按鈕點擊事件
    if (exportReportExcel) {
        exportReportExcel.addEventListener('click', function() {
            exportReport('excel');
        });
    }
    
    if (exportReportPdf) {
        exportReportPdf.addEventListener('click', function() {
            exportReport('pdf');
        });
    }
}

/**
 * 根據類型和日期範圍載入報表
 * @param {string} type - 報表類型 (expense/income/balance)
 * @param {string} dateRange - 日期範圍 (this-month/last-month/this-year/last-year/custom)
 * @param {string} startDate - 自訂開始日期 (僅當dateRange為custom時使用)
 * @param {string} endDate - 自訂結束日期 (僅當dateRange為custom時使用)
 */
function loadReportByType(type, dateRange, startDate, endDate) {
    // 更新報表標題
    updateReportTitle(type, dateRange);
    
    // 計算日期範圍
    const dateRange1 = calculateDateRange(dateRange, startDate, endDate);
    const start = dateRange1.startDate;
    const end = dateRange1.endDate;
    
    // 根據類型載入不同報表
    if (type === 'expense') {
        loadExpenseReport(start, end);
    } else if (type === 'income') {
        loadIncomeReport(start, end);
    } else if (type === 'balance') {
        loadBalanceReport(start, end);
    }
}

/**
 * 更新報表標題
 * @param {string} type - 報表類型
 * @param {string} dateRange - 日期範圍
 */
function updateReportTitle(type, dateRange) {
    const reportTitle = document.getElementById('report-title');
    const reportDateRangeText = document.getElementById('report-date-range-text');
    const balanceContainer = document.getElementById('report-balance-container');
    
    if (!reportTitle || !reportDateRangeText || !balanceContainer) return;
    
    // 設置報表類型標題
    let title = '';
    switch (type) {
        case 'expense':
            title = '支出分析';
            balanceContainer.style.display = 'none';
            break;
        case 'income':
            title = '收入分析';
            balanceContainer.style.display = 'none';
            break;
        case 'balance':
            title = '收支平衡';
            balanceContainer.style.display = 'flex';
            break;
    }
    
    reportTitle.textContent = title;
    
    // 設置日期範圍文字
    let dateText = '';
    const today = new Date();
    
    switch (dateRange) {
        case 'this-month':
            dateText = `${today.getFullYear()}年${today.getMonth() + 1}月`;
            break;
        case 'last-month':
            const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1);
            dateText = `${lastMonth.getFullYear()}年${lastMonth.getMonth() + 1}月`;
            break;
        case 'this-year':
            dateText = `${today.getFullYear()}年`;
            break;
        case 'last-year':
            dateText = `${today.getFullYear() - 1}年`;
            break;
        case 'custom':
            // 自訂日期會在獲取數據後更新
            dateText = '自訂日期範圍';
            break;
    }
    
    reportDateRangeText.textContent = dateText;
}

/**
 * 計算日期範圍
 * @param {string} dateRange - 日期範圍選項
 * @param {string} startDate - 自訂開始日期
 * @param {string} endDate - 自訂結束日期
 * @returns {Object} 包含開始和結束日期的物件
 */
function calculateDateRange(dateRange, startDate, endDate) {
    const today = new Date();
    let start, end;
    
    switch (dateRange) {
        case 'this-month':
            start = new Date(today.getFullYear(), today.getMonth(), 1);
            end = new Date(today.getFullYear(), today.getMonth() + 1, 0);
            break;
        case 'last-month':
            start = new Date(today.getFullYear(), today.getMonth() - 1, 1);
            end = new Date(today.getFullYear(), today.getMonth(), 0);
            break;
        case 'this-year':
            start = new Date(today.getFullYear(), 0, 1);
            end = new Date(today.getFullYear(), 11, 31);
            break;
        case 'last-year':
            start = new Date(today.getFullYear() - 1, 0, 1);
            end = new Date(today.getFullYear() - 1, 11, 31);
            break;
        case 'custom':
            if (startDate && endDate) {
                start = new Date(startDate);
                end = new Date(endDate);
            } else {
                // 如果沒有提供自訂日期，默認使用本月
                start = new Date(today.getFullYear(), today.getMonth(), 1);
                end = new Date(today.getFullYear(), today.getMonth() + 1, 0);
            }
            break;
    }
    
    return {
        startDate: formatDateForAPI(start),
        endDate: formatDateForAPI(end)
    };
}

/**
 * 格式化日期為API請求格式 (YYYY-MM-DD)
 * @param {Date} date - 日期物件
 * @returns {string} 格式化後的日期字符串
 */
function formatDateForAPI(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

/**
 * 載入支出報表
 * @param {string} startDate - 開始日期
 * @param {string} endDate - 結束日期
 */
function loadExpenseReport(startDate, endDate) {
    // 顯示載入狀態
    const reportTotalAmount = document.getElementById('report-total-amount');
    const reportTransactionCount = document.getElementById('report-transaction-count');
    const reportDetailsBody = document.getElementById('report-details-body');
    
    if (reportTotalAmount) reportTotalAmount.textContent = '載入中...';
    if (reportTransactionCount) reportTransactionCount.textContent = '載入中...';
    if (reportDetailsBody) reportDetailsBody.innerHTML = '<tr><td colspan="5" class="loading-text">載入中...</td></tr>';
    
    // 清空圖表容器
    resetCharts();
    
    // 發送API請求
    fetch(`/api/reports/expense-summary?start_date=${startDate}&end_date=${endDate}`)
        .then(response => response.json())
        .then(data => {
            // 更新摘要信息
            updateExpenseSummary(data);
            
            // 繪製分類圖表
            drawCategoryChart(data, 'expense');
            
            // 獲取每日支出趨勢
            loadDailyExpenseTrend(startDate, endDate);
            
            // 獲取交易明細
            loadTransactionDetails('expense', startDate, endDate);
        })
        .catch(error => {
            console.error('載入支出報表失敗:', error);
            showReportError();
        });
}

/**
 * 載入收入報表
 * @param {string} startDate - 開始日期
 * @param {string} endDate - 結束日期
 */
function loadIncomeReport(startDate, endDate) {
    // 顯示載入狀態
    const reportTotalAmount = document.getElementById('report-total-amount');
    const reportTransactionCount = document.getElementById('report-transaction-count');
    const reportDetailsBody = document.getElementById('report-details-body');
    
    if (reportTotalAmount) reportTotalAmount.textContent = '載入中...';
    if (reportTransactionCount) reportTransactionCount.textContent = '載入中...';
    if (reportDetailsBody) reportDetailsBody.innerHTML = '<tr><td colspan="5" class="loading-text">載入中...</td></tr>';
    
    // 清空圖表容器
    resetCharts();
    
    // 發送API請求
    fetch(`/api/reports/income-summary?start_date=${startDate}&end_date=${endDate}`)
        .then(response => response.json())
        .then(data => {
            // 更新摘要信息
            updateIncomeSummary(data);
            
            // 繪製分類圖表
            drawCategoryChart(data, 'income');
            
            // 獲取每日收入趨勢
            loadDailyIncomeTrend(startDate, endDate);
            
            // 獲取交易明細
            loadTransactionDetails('income', startDate, endDate);
        })
        .catch(error => {
            console.error('載入收入報表失敗:', error);
            showReportError();
        });
}

/**
 * 載入收支平衡報表
 * @param {string} startDate - 開始日期
 * @param {string} endDate - 結束日期
 */
function loadBalanceReport(startDate, endDate) {
    // 顯示載入狀態
    const reportTotalAmount = document.getElementById('report-total-amount');
    const reportTransactionCount = document.getElementById('report-transaction-count');
    const reportBalance = document.getElementById('report-balance');
    const reportDetailsBody = document.getElementById('report-details-body');
    
    if (reportTotalAmount) reportTotalAmount.textContent = '載入中...';
    if (reportTransactionCount) reportTransactionCount.textContent = '載入中...';
    if (reportBalance) reportBalance.textContent = '載入中...';
    if (reportDetailsBody) reportDetailsBody.innerHTML = '<tr><td colspan="5" class="loading-text">載入中...</td></tr>';
    
    // 清空圖表容器
    resetCharts();
    
    // 發送API請求 - 獲取每日收支摘要
    fetch(`/api/reports/daily-summary?start_date=${startDate}&end_date=${endDate}`)
        .then(response => response.json())
        .then(data => {
            // 更新收支平衡摘要
            updateBalanceSummary(data);
            
            // 繪製收支比例圖表
            drawBalanceChart(data);
            
            // 繪製收支趨勢圖表
            drawBalanceTrendChart(data);
            
            // 獲取交易明細
            loadTransactionDetails('all', startDate, endDate);
        })
        .catch(error => {
            console.error('載入收支平衡報表失敗:', error);
            showReportError();
        });
}

/**
 * 重置圖表容器
 */
function resetCharts() {
    const categoryChartContainer = document.querySelector('#report-category-chart').parentElement;
    const trendChartContainer = document.querySelector('#report-trend-chart').parentElement;
    
    if (categoryChartContainer) {
        categoryChartContainer.innerHTML = '<div class="loading-text">載入中...</div><canvas id="report-category-chart"></canvas>';
    }
    
    if (trendChartContainer) {
        trendChartContainer.innerHTML = '<div class="loading-text">載入中...</div><canvas id="report-trend-chart"></canvas>';
    }
}

/**
 * 顯示報表錯誤
 */
function showReportError() {
    const reportTotalAmount = document.getElementById('report-total-amount');
    const reportTransactionCount = document.getElementById('report-transaction-count');
    const reportBalance = document.getElementById('report-balance');
    const reportDetailsBody = document.getElementById('report-details-body');
    const categoryChartContainer = document.querySelector('#report-category-chart').parentElement;
    const trendChartContainer = document.querySelector('#report-trend-chart').parentElement;
    
    if (reportTotalAmount) reportTotalAmount.textContent = '載入失敗';
    if (reportTransactionCount) reportTransactionCount.textContent = '載入失敗';
    if (reportBalance) reportBalance.textContent = '載入失敗';
    if (reportDetailsBody) reportDetailsBody.innerHTML = '<tr><td colspan="5" class="error-text">載入數據失敗</td></tr>';
    
    if (categoryChartContainer) {
        categoryChartContainer.innerHTML = '<div class="error-text">載入圖表失敗</div>';
    }
    
    if (trendChartContainer) {
        trendChartContainer.innerHTML = '<div class="error-text">載入圖表失敗</div>';
    }
}

/**
 * 更新支出報表摘要
 * @param {Array} data - 支出分類數據
 */
function updateExpenseSummary(data) {
    const reportTotalAmount = document.getElementById('report-total-amount');
    const reportTransactionCount = document.getElementById('report-transaction-count');
    
    if (!reportTotalAmount || !reportTransactionCount || !data || data.length === 0) {
        if (reportTotalAmount) reportTotalAmount.textContent = '0';
        if (reportTransactionCount) reportTransactionCount.textContent = '0';
        return;
    }
    
    // 計算總金額和交易筆數
    let totalAmount = 0;
    let totalCount = 0;
    
    data.forEach(item => {
        totalAmount += parseFloat(item.total_amount) || 0;
        totalCount += parseInt(item.transaction_count) || 0;
    });
    
    // 更新UI
    reportTotalAmount.textContent = formatCurrency(totalAmount);
    reportTransactionCount.textContent = totalCount;
}

/**
 * 更新收入報表摘要
 * @param {Array} data - 收入分類數據
 */
function updateIncomeSummary(data) {
    const reportTotalAmount = document.getElementById('report-total-amount');
    const reportTransactionCount = document.getElementById('report-transaction-count');
    
    if (!reportTotalAmount || !reportTransactionCount || !data || data.length === 0) {
        if (reportTotalAmount) reportTotalAmount.textContent = '0';
        if (reportTransactionCount) reportTransactionCount.textContent = '0';
        return;
    }
    
    // 計算總金額和交易筆數
    let totalAmount = 0;
    let totalCount = 0;
    
    data.forEach(item => {
        totalAmount += parseFloat(item.total_amount) || 0;
        totalCount += parseInt(item.transaction_count) || 0;
    });
    
    // 更新UI
    reportTotalAmount.textContent = formatCurrency(totalAmount);
    reportTransactionCount.textContent = totalCount;
}

/**
 * 更新收支平衡報表摘要
 * @param {Array} data - 每日收支數據
 */
function updateBalanceSummary(data) {
    const reportTotalAmount = document.getElementById('report-total-amount');
    const reportTransactionCount = document.getElementById('report-transaction-count');
    const reportBalance = document.getElementById('report-balance');
    
    if (!reportTotalAmount || !reportTransactionCount || !reportBalance || !data || data.length === 0) {
        if (reportTotalAmount) reportTotalAmount.textContent = '0';
        if (reportTransactionCount) reportTransactionCount.textContent = '0';
        if (reportBalance) reportBalance.textContent = '0';
        return;
    }
    
    // 計算總收入、總支出、總交易筆數和餘額
    let totalIncome = 0;
    let totalExpense = 0;
    let totalCount = 0;
    
    data.forEach(item => {
        totalIncome += parseFloat(item.total_income) || 0;
        totalExpense += parseFloat(item.total_expense) || 0;
        totalCount += (parseInt(item.income_count) || 0) + (parseInt(item.expense_count) || 0);
    });
    
    const balance = totalIncome - totalExpense;
    
    // 更新UI
    reportTotalAmount.textContent = formatCurrency(totalIncome + totalExpense);
    reportTransactionCount.textContent = totalCount;
    reportBalance.textContent = formatCurrency(balance);
    
    // 根據餘額調整顏色
    if (balance >= 0) {
        reportBalance.classList.add('income');
        reportBalance.classList.remove('expense');
    } else {
        reportBalance.classList.add('expense');
        reportBalance.classList.remove('income');
    }
}

/**
 * 繪製分類圖表
 * @param {Array} data - 分類數據
 * @param {string} type - 類型 (expense/income)
 */
function drawCategoryChart(data, type) {
    const ctx = document.getElementById('report-category-chart');
    if (!ctx || !data || data.length === 0) {
        const container = document.querySelector('#report-category-chart').parentElement;
        if (container) {
            container.innerHTML = '<div class="empty-state">沒有數據</div>';
        }
        return;
    }
    
    // 准備圖表數據
    const labels = [];
    const values = [];
    const colors = [];
    
    // 生成隨機顏色
    const getRandomColor = () => {
        const letters = '0123456789ABCDEF';
        let color = '#';
        for (let i = 0; i < 6; i++) {
            color += letters[Math.floor(Math.random() * 16)];
        }
        return color;
    };
    
    // 按金額從大到小排序
    data.sort((a, b) => parseFloat(b.total_amount) - parseFloat(a.total_amount));
    
    // 如果超過7個分類，將小的分類合併為"其他"
    if (data.length > 7) {
        const mainCategories = data.slice(0, 6);
        const otherCategories = data.slice(6);
        
        let otherAmount = 0;
        otherCategories.forEach(item => {
            otherAmount += parseFloat(item.total_amount) || 0;
        });
        
        mainCategories.forEach(item => {
            labels.push(item.category_name);
            values.push(parseFloat(item.total_amount) || 0);
            colors.push(getRandomColor());
        });
        
        labels.push('其他');
        values.push(otherAmount);
        colors.push(getRandomColor());
    } else {
        data.forEach(item => {
            labels.push(item.category_name);
            values.push(parseFloat(item.total_amount) || 0);
            colors.push(getRandomColor());
        });
    }
    
    // 創建圓餅圖
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = context.chart.getDatasetMeta(0).total;
                            const percentage = Math.round((value / total) * 100);
                            return `${label}: ${formatCurrency(value)} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * 載入每日支出趨勢
 * @param {string} startDate - 開始日期
 * @param {string} endDate - 結束日期
 */
function loadDailyExpenseTrend(startDate, endDate) {
    fetch(`/api/reports/daily-summary?start_date=${startDate}&end_date=${endDate}`)
        .then(response => response.json())
        .then(data => {
            drawTrendChart(data, 'expense');
        })
        .catch(error => {
            console.error('載入每日支出趨勢失敗:', error);
            const trendChartContainer = document.querySelector('#report-trend-chart').parentElement;
            if (trendChartContainer) {
                trendChartContainer.innerHTML = '<div class="error-text">載入趨勢圖表失敗</div>';
            }
        });
}

/**
 * 載入每日收入趨勢
 * @param {string} startDate - 開始日期
 * @param {string} endDate - 結束日期
 */
function loadDailyIncomeTrend(startDate, endDate) {
    fetch(`/api/reports/daily-summary?start_date=${startDate}&end_date=${endDate}`)
        .then(response => response.json())
        .then(data => {
            drawTrendChart(data, 'income');
        })
        .catch(error => {
            console.error('載入每日收入趨勢失敗:', error);
            const trendChartContainer = document.querySelector('#report-trend-chart').parentElement;
            if (trendChartContainer) {
                trendChartContainer.innerHTML = '<div class="error-text">載入趨勢圖表失敗</div>';
            }
        });
}

/**
 * 繪製趨勢圖表
 * @param {Array} data - 每日數據
 * @param {string} type - 類型 (expense/income)
 */
function drawTrendChart(data, type) {
    const ctx = document.getElementById('report-trend-chart');
    if (!ctx || !data || data.length === 0) {
        const container = document.querySelector('#report-trend-chart').parentElement;
        if (container) {
            container.innerHTML = '<div class="empty-state">沒有數據</div>';
        }
        return;
    }
    
    // 排序數據（按日期）
    data.sort((a, b) => new Date(a.date) - new Date(b.date));
    
    // 准備圖表數據
    const labels = [];
    const values = [];
    
    data.forEach(item => {
        // 格式化日期 (MM-DD)
        const date = new Date(item.date);
        const formattedDate = `${date.getMonth() + 1}/${date.getDate()}`;
        
        labels.push(formattedDate);
        
        if (type === 'expense') {
            values.push(parseFloat(item.total_expense) || 0);
        } else {
            values.push(parseFloat(item.total_income) || 0);
        }
    });
    
    // 創建趨勢圖
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: type === 'expense' ? '支出' : '收入',
                data: values,
                backgroundColor: type === 'expense' ? 'rgba(255, 99, 132, 0.2)' : 'rgba(75, 192, 192, 0.2)',
                borderColor: type === 'expense' ? 'rgba(255, 99, 132, 1)' : 'rgba(75, 192, 192, 1)',
                borderWidth: 1,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.dataset.label || '';
                            const value = context.raw || 0;
                            return `${label}: ${formatCurrency(value)}`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * 繪製收支平衡圖表
 * @param {Array} data - 每日收支數據
 */
function drawBalanceChart(data) {
    const ctx = document.getElementById('report-category-chart');
    if (!ctx || !data || data.length === 0) {
        const container = document.querySelector('#report-category-chart').parentElement;
        if (container) {
            container.innerHTML = '<div class="empty-state">沒有數據</div>';
        }
        return;
    }
    
    // 計算總收入和總支出
    let totalIncome = 0;
    let totalExpense = 0;
    
    data.forEach(item => {
        totalIncome += parseFloat(item.total_income) || 0;
        totalExpense += parseFloat(item.total_expense) || 0;
    });
    
    // 創建餅圖
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['收入', '支出'],
            datasets: [{
                data: [totalIncome, totalExpense],
                backgroundColor: ['rgba(75, 192, 192, 0.2)', 'rgba(255, 99, 132, 0.2)'],
                borderColor: ['rgba(75, 192, 192, 1)', 'rgba(255, 99, 132, 1)'],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = totalIncome + totalExpense;
                            const percentage = Math.round((value / total) * 100);
                            return `${label}: ${formatCurrency(value)} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * 繪製收支趨勢圖表
 * @param {Array} data - 每日收支數據
 */
function drawBalanceTrendChart(data) {
    const ctx = document.getElementById('report-trend-chart');
    if (!ctx || !data || data.length === 0) {
        const container = document.querySelector('#report-trend-chart').parentElement;
        if (container) {
            container.innerHTML = '<div class="empty-state">沒有數據</div>';
        }
        return;
    }
    
    // 排序數據（按日期）
    data.sort((a, b) => new Date(a.date) - new Date(b.date));
    
    // 准備圖表數據
    const labels = [];
    const incomeData = [];
    const expenseData = [];
    
    data.forEach(item => {
        // 格式化日期 (MM-DD)
        const date = new Date(item.date);
        const formattedDate = `${date.getMonth() + 1}/${date.getDate()}`;
        
        labels.push(formattedDate);
        incomeData.push(parseFloat(item.total_income) || 0);
        expenseData.push(parseFloat(item.total_expense) || 0);
    });
    
    // 創建趨勢圖
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: '收入',
                    data: incomeData,
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1,
                    tension: 0.4
                },
                {
                    label: '支出',
                    data: expenseData,
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.dataset.label || '';
                            const value = context.raw || 0;
                            return `${label}: ${formatCurrency(value)}`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * 載入交易明細
 * @param {string} type - 類型 (expense/income/all)
 * @param {string} startDate - 開始日期
 * @param {string} endDate - 結束日期
 */
function loadTransactionDetails(type, startDate, endDate) {
    const reportDetailsBody = document.getElementById('report-details-body');
    if (!reportDetailsBody) return;
    
    // 構建API URL
    let apiUrl = `/api/transactions?`;
    
    if (type !== 'all') {
        apiUrl += `type=${type}&`;
    }
    
    apiUrl += `start_date=${startDate}&end_date=${endDate}`;
    
    // 發送API請求
    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            if (!data || !data.transactions || data.transactions.length === 0) {
                reportDetailsBody.innerHTML = '<tr><td colspan="5" class="empty-text">無交易記錄</td></tr>';
                return;
            }
            
            // 渲染交易明細
            let html = '';
            data.transactions.forEach(transaction => {
                html += `
                <tr>
                    <td>${formatDate(transaction.date)}</td>
                    <td>${transaction.category_name}</td>
                    <td>${transaction.item || '-'}</td>
                    <td class="${transaction.type === 'expense' ? 'expense' : 'income'}">${formatCurrency(transaction.amount)}</td>
                    <td>${transaction.account_name}</td>
                </tr>
                `;
            });
            
            reportDetailsBody.innerHTML = html;
        })
        .catch(error => {
            console.error('載入交易明細失敗:', error);
            reportDetailsBody.innerHTML = '<tr><td colspan="5" class="error-text">載入數據失敗</td></tr>';
        });
}

/**
 * 匯出報表
 * @param {string} format - 匯出格式 (excel/pdf)
 */
function exportReport(format) {
    const reportType = document.getElementById('report-type').value;
    const dateRange = document.getElementById('report-date-range').value;
    const startDate = document.getElementById('report-start-date').value;
    const endDate = document.getElementById('report-end-date').value;
    
    // 計算日期範圍
    const dates = calculateDateRange(dateRange, startDate, endDate);
    
    // 構建API URL
    let apiUrl = `/api/reports/export?format=${format}&type=${reportType}&start_date=${dates.startDate}&end_date=${dates.endDate}`;
    
    // 使用新視窗下載檔案
    window.open(apiUrl, '_blank');
}
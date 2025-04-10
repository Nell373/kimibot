/**
 * LINE 智能記帳與提醒助手 - PWA預覽 JavaScript (第一部分)
 * 
 * 此文件提供PWA預覽的互動功能:
 * 1. 設備選擇與顯示
 * 2. 測試功能模擬
 * 3. 頁面導航
 * 4. PWA審計工具
 */

// 設備配置
const deviceConfig = {
    'mobile-portrait': {
        width: 375,
        height: 667,
        displayName: '手機 (直向)'
    },
    'mobile-landscape': {
        width: 667,
        height: 375,
        displayName: '手機 (橫向)'
    },
    'tablet-portrait': {
        width: 768,
        height: 1024,
        displayName: '平板 (直向)'
    },
    'tablet-landscape': {
        width: 1024,
        height: 768,
        displayName: '平板 (橫向)'
    },
    'desktop': {
        width: 1280,
        height: 800,
        displayName: '桌面'
    }
};

// 頁面配置
const pageConfig = {
    'login': {
        url: '/static/templates/login.html',
        displayName: '登入頁面'
    },
    'overview': {
        url: '/static/templates/dashboard.html#overview',
        displayName: '帳戶總覽'
    },
    'transactions': {
        url: '/static/templates/dashboard.html#transactions',
        displayName: '交易記錄'
    },
    'categories': {
        url: '/static/templates/dashboard.html#categories',
        displayName: '分類管理'
    },
    'reminders': {
        url: '/static/templates/dashboard.html#reminders',
        displayName: '提醒管理'
    },
    'reports': {
        url: '/static/templates/dashboard.html#reports',
        displayName: '報表分析'
    },
    'settings': {
        url: '/static/templates/dashboard.html#settings',
        displayName: '設置'
    }
};

// 當前狀態
let currentDevice = 'mobile-portrait';
let currentPage = 'login';
let inspectorActive = false;
let isOfflineMode = false;

// 初始化頁面
document.addEventListener('DOMContentLoaded', function() {
    // 獲取DOM元素
    const deviceButtons = document.querySelectorAll('.device-btn');
    const deviceFrame = document.getElementById('device-frame');
    const previewIframe = document.getElementById('preview-iframe');
    const currentResolution = document.getElementById('current-resolution');
    const pageButtons = document.querySelectorAll('.page-btn');
    const offlineTestButton = document.getElementById('offline-test');
    const cameraTestButton = document.getElementById('camera-test');
    const notificationTestButton = document.getElementById('notification-test');
    const installTestButton = document.getElementById('install-test');
    const toggleInspectorButton = document.getElementById('toggle-inspector');
    const runAuditButton = document.getElementById('run-audit');
    const clearLogsButton = document.getElementById('clear-logs');
    const closeModalButton = document.querySelector('#pwa-audit-modal .close');
    const auditModal = document.getElementById('pwa-audit-modal');

    // 設置設備按鈕事件
    deviceButtons.forEach(button => {
        button.addEventListener('click', function() {
            const device = this.getAttribute('data-device');
            changeDevice(device);
            
            // 更新按鈕狀態
            deviceButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // 設置頁面按鈕事件
    pageButtons.forEach(button => {
        button.addEventListener('click', function() {
            const page = this.getAttribute('data-page');
            changePage(page);
            
            // 更新按鈕狀態
            pageButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // 設置測試按鈕事件
    offlineTestButton.addEventListener('click', toggleOfflineMode);
    cameraTestButton.addEventListener('click', testCamera);
    notificationTestButton.addEventListener('click', testNotification);
    installTestButton.addEventListener('click', testInstallPrompt);

    // 設置元素檢查按鈕事件
    toggleInspectorButton.addEventListener('click', toggleInspector);

    // 設置審計按鈕事件
    runAuditButton.addEventListener('click', runPwaAudit);

    // 設置清除日誌按鈕事件
    clearLogsButton.addEventListener('click', clearEventLogs);

    // 設置模態框關閉按鈕事件
    closeModalButton.addEventListener('click', function() {
        auditModal.style.display = 'none';
    });

    window.addEventListener('click', function(event) {
        if (event.target === auditModal) {
            auditModal.style.display = 'none';
        }
    });

    // 設置iframe加載事件
    previewIframe.addEventListener('load', function() {
        addEventLog(`頁面 "${pageConfig[currentPage].displayName}" 已載入`);
        
        // 嘗試訪問iframe內容進行事件監聽
        try {
            const iframeDocument = this.contentDocument || this.contentWindow.document;
            
            // 監聽iframe內的點擊事件
            iframeDocument.addEventListener('click', function(event) {
                if (inspectorActive) {
                    inspectElement(event);
                }
            });
            
            // 監聽iframe內的頁面變化
            const iframeLinks = iframeDocument.querySelectorAll('a');
            iframeLinks.forEach(link => {
                link.addEventListener('click', function() {
                    addEventLog(`點擊了鏈接: ${this.href}`);
                });
            });
            
            // 注入偵錯代碼
            injectDebugCode(iframeDocument);
            
        } catch (error) {
            console.error('無法訪問iframe內容:', error);
            addEventLog(`無法訪問iframe內容: ${error.message}`);
        }
    });

    // 初始化設備和頁面
    changeDevice(currentDevice);
    changePage(currentPage);
    
    // 添加初始日誌訊息
    addEventLog('PWA 預覽已初始化');
});

/**
 * 更改設備顯示
 * @param {string} device - 設備類型
 */
function changeDevice(device) {
    if (!deviceConfig[device]) return;
    
    const { width, height, displayName } = deviceConfig[device];
    const deviceFrame = document.getElementById('device-frame');
    const currentResolution = document.getElementById('current-resolution');
    
    // 更新設備外觀
    deviceFrame.style.width = `${width}px`;
    deviceFrame.style.height = `${height}px`;
    
    // 如果是橫向設備，添加橫向類
    if (device.includes('landscape')) {
        deviceFrame.classList.add('landscape');
    } else {
        deviceFrame.classList.remove('landscape');
    }
    
    // 更新分辨率顯示
    currentResolution.textContent = `${width} x ${height} px`;
    
    // 更新當前設備
    currentDevice = device;
    
    addEventLog(`切換設備為 "${displayName}"`);
}

/**
 * 更改頁面顯示
 * @param {string} page - 頁面類型
 */
function changePage(page) {
    if (!pageConfig[page]) return;
    
    const previewIframe = document.getElementById('preview-iframe');
    
    // 更新iframe源
    previewIframe.src = pageConfig[page].url;
    
    // 更新當前頁面
    currentPage = page;
    
    addEventLog(`切換頁面為 "${pageConfig[page].displayName}"`);
}

/**
 * 添加事件日誌
 * @param {string} message - 日誌訊息
 */
function addEventLog(message) {
    const eventLogContent = document.getElementById('event-log-content');
    const timestamp = new Date().toLocaleTimeString();
    
    const logItem = document.createElement('div');
    logItem.className = 'log-item';
    logItem.textContent = `[${timestamp}] ${message}`;
    
    eventLogContent.appendChild(logItem);
    eventLogContent.scrollTop = eventLogContent.scrollHeight;
}

/**
 * 清除事件日誌
 */
function clearEventLogs() {
    const eventLogContent = document.getElementById('event-log-content');
    eventLogContent.innerHTML = '';
    addEventLog('日誌已清除');
}

/**
 * 切換離線模式
 */
function toggleOfflineMode() {
    isOfflineMode = !isOfflineMode;
    
    const previewIframe = document.getElementById('preview-iframe');
    const offlineTestButton = document.getElementById('offline-test');
    
    try {
        const iframeDocument = previewIframe.contentDocument || previewIframe.contentWindow.document;
        
        if (isOfflineMode) {
            // 模擬離線狀態
            iframeDocument.body.classList.add('offline-mode');
            
            // 在iframe中顯示離線通知
            const offlineNotification = document.createElement('div');
            offlineNotification.id = 'offline-notification';
            offlineNotification.style.position = 'fixed';
            offlineNotification.style.top = '0';
            offlineNotification.style.left = '0';
            offlineNotification.style.width = '100%';
            offlineNotification.style.padding = '10px';
            offlineNotification.style.backgroundColor = '#f44336';
            offlineNotification.style.color = 'white';
            offlineNotification.style.textAlign = 'center';
            offlineNotification.style.zIndex = '9999';
            offlineNotification.textContent = '您目前處於離線狀態';
            
            iframeDocument.body.appendChild(offlineNotification);
            
            // 修改按鈕樣式
            offlineTestButton.innerHTML = '<i class="fas fa-wifi"></i> 恢復在線模式';
            offlineTestButton.style.backgroundColor = '#f44336';
            
            addEventLog('已切換到離線模式');
        } else {
            // 恢復在線狀態
            iframeDocument.body.classList.remove('offline-mode');
            
            // 移除離線通知
            const offlineNotification = iframeDocument.getElementById('offline-notification');
            if (offlineNotification) {
                offlineNotification.remove();
            }
            
            // 恢復按鈕樣式
            offlineTestButton.innerHTML = '<i class="fas fa-wifi-slash"></i> 測試離線模式';
            offlineTestButton.style.backgroundColor = '';
            
            addEventLog('已恢復在線模式');
        }
        
        // 模擬離線/在線事件
        const eventType = isOfflineMode ? 'offline' : 'online';
        const event = new Event(eventType);
        iframeDocument.dispatchEvent(event);
        
    } catch (error) {
        console.error('模擬離線模式失敗:', error);
        addEventLog(`模擬離線模式失敗: ${error.message}`);
    }
}

/**
 * 測試相機功能
 */
function testCamera() {
    const previewIframe = document.getElementById('preview-iframe');
    
    try {
        const iframeWindow = previewIframe.contentWindow;
        
        // 創建相機測試模態框
        const modal = document.createElement('div');
        modal.style.position = 'fixed';
        modal.style.top = '0';
        modal.style.left = '0';
        modal.style.width = '100%';
        modal.style.height = '100%';
        modal.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
        modal.style.zIndex = '10000';
        modal.style.display = 'flex';
        modal.style.flexDirection = 'column';
        modal.style.alignItems = 'center';
        modal.style.justifyContent = 'center';
        
        // 創建相機視頻元素
        const video = document.createElement('video');
        video.style.width = '80%';
        video.style.maxHeight = '60%';
        video.style.backgroundColor = '#000';
        video.autoplay = true;
        
        // 創建關閉按鈕
        const closeButton = document.createElement('button');
        closeButton.textContent = '關閉相機';
        closeButton.style.marginTop = '20px';
        closeButton.style.padding = '10px 20px';
        closeButton.style.backgroundColor = '#f44336';
        closeButton.style.color = 'white';
        closeButton.style.border = 'none';
        closeButton.style.borderRadius = '4px';
        closeButton.style.cursor = 'pointer';
        
        modal.appendChild(video);
        modal.appendChild(closeButton);
        
        // 添加到iframe文檔
        const iframeDocument = previewIframe.contentDocument || previewIframe.contentWindow.document;
        iframeDocument.body.appendChild(modal);
        
        // 請求相機權限
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(stream => {
                video.srcObject = stream;
                addEventLog('相機已啟用');
                
                // 設置關閉事件
                closeButton.addEventListener('click', function() {
                    stream.getTracks().forEach(track => track.stop());
                    modal.remove();
                    addEventLog('相機已關閉');
                });
            })
            .catch(error => {
                console.error('無法訪問相機:', error);
                modal.innerHTML = `<div style="color: white; padding: 20px; text-align: center;">
                    <h3>無法訪問相機</h3>
                    <p>${error.message}</p>
                    <button style="margin-top: 20px; padding: 10px 20px; background-color: #f44336; color: white; border: none; border-radius: 4px; cursor: pointer;">關閉</button>
                </div>`;
                
                modal.querySelector('button').addEventListener('click', function() {
                    modal.remove();
                });
                
                addEventLog(`無法訪問相機: ${error.message}`);
            });
    } catch (error) {
        console.error('測試相機功能失敗:', error);
        addEventLog(`測試相機功能失敗: ${error.message}`);
    }
}

/**
 * 測試通知功能
 */
function testNotification() {
    try {
        // 檢查通知權限
        Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
                // 創建測試通知
                const notification = new Notification('LINE 智能記帳與提醒助手', {
                    body: '這是一條測試通知，用於檢查PWA通知功能是否正常。',
                    icon: '/static/img/logo.png'
                });
                
                // 設置通知點擊事件
                notification.onclick = function() {
                    addEventLog('用戶點擊了通知');
                    notification.close();
                };
                
                addEventLog('測試通知已發送');
            } else {
                addEventLog(`通知權限被拒絕: ${permission}`);
                
                // 顯示權限說明
                alert('為了測試通知功能，請允許通知權限。');
            }
        });
    } catch (error) {
        console.error('測試通知功能失敗:', error);
        addEventLog(`測試通知功能失敗: ${error.message}`);
    }
}

/**
 * 測試安裝提示
 */
function testInstallPrompt() {
    const previewIframe = document.getElementById('preview-iframe');
    
    try {
        const iframeDocument = previewIframe.contentDocument || previewIframe.contentWindow.document;
        
        // 創建安裝提示模態框
        const modal = document.createElement('div');
        modal.style.position = 'fixed';
        modal.style.top = '0';
        modal.style.left = '0';
        modal.style.width = '100%';
        modal.style.height = '100%';
        modal.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
        modal.style.zIndex = '10000';
        modal.style.display = 'flex';
        modal.style.alignItems = 'center';
        modal.style.justifyContent = 'center';
        
        // 創建提示內容
        const promptBox = document.createElement('div');
        promptBox.style.width = '80%';
        promptBox.style.maxWidth = '400px';
        promptBox.style.backgroundColor = 'white';
        promptBox.style.borderRadius = '8px';
        promptBox.style.padding = '20px';
        promptBox.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.2)';
        
        promptBox.innerHTML = `
            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                <img src="/static/img/logo.png" style="width: 40px; height: 40px; margin-right: 10px;">
                <div>
                    <div style="font-weight: bold;">LINE 智能記帳與提醒助手</div>
                    <div style="font-size: 12px; color: #666;">linebot-assistant.fly.dev</div>
                </div>
            </div>
            <div style="margin-bottom: 20px;">將此應用添加到主屏幕以便快速訪問。</div>
            <div style="display: flex; justify-content: flex-end;">
                <button id="cancel-install" style="padding: 8px 16px; background: none; border: none; margin-right: 10px; cursor: pointer;">取消</button>
                <button id="confirm-install" style="padding: 8px 16px; background-color: #06c755; color: white; border: none; border-radius: 4px; cursor: pointer;">安裝</button>
            </div>
        `;
        
        modal.appendChild(promptBox);
        iframeDocument.body.appendChild(modal);
        
        // 添加按鈕事件
        iframeDocument.getElementById('cancel-install').addEventListener('click', function() {
            modal.remove();
            addEventLog('用戶取消了安裝提示');
        });
        
        iframeDocument.getElementById('confirm-install').addEventListener('click', function() {
            modal.remove();
            
            // 顯示安裝成功提示
            const successToast = document.createElement('div');
            successToast.style.position = 'fixed';
            successToast.style.bottom = '20px';
            successToast.style.left = '50%';
            successToast.style.transform = 'translateX(-50%)';
            successToast.style.padding = '10px 20px';
            successToast.style.backgroundColor = '#06c755';
            successToast.style.color = 'white';
            successToast.style.borderRadius = '4px';
            successToast.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.2)';
            successToast.style.zIndex = '10001';
            successToast.textContent = '應用已成功添加到主屏幕';
            
            iframeDocument.body.appendChild(successToast);
            
            // 3秒後移除提示
            setTimeout(() => {
                successToast.remove();
            }, 3000);
            
            addEventLog('用戶確認了安裝提示');
        });
        
        addEventLog('顯示安裝提示');
        
    } catch (error) {
        console.error('測試安裝提示失敗:', error);
        addEventLog(`測試安裝提示失敗: ${error.message}`);
    }
}

/**
 * 切換元素檢查器
 */
function toggleInspector() {
    inspectorActive = !inspectorActive;
    
    const toggleInspectorButton = document.getElementById('toggle-inspector');
    const elementDetails = document.getElementById('element-details');
    
    if (inspectorActive) {
        toggleInspectorButton.innerHTML = '<i class="fas fa-times"></i> 關閉元素檢查';
        toggleInspectorButton.style.backgroundColor = '#f44336';
        elementDetails.innerHTML = '<div class="info-item">請在預覽中點擊元素以檢查</div>';
        
        addEventLog('元素檢查已啟用');
    } else {
        toggleInspectorButton.innerHTML = '<i class="fas fa-crosshairs"></i> 啟用元素檢查';
        toggleInspectorButton.style.backgroundColor = '';
        elementDetails.innerHTML = '<div class="info-item">點擊 "啟用元素檢查" 以檢查元素</div>';
        
        addEventLog('元素檢查已關閉');
    }
}

/**
 * 檢查元素
 * @param {Event} event - 點擊事件
 */
function inspectElement(event) {
    if (!inspectorActive) return;
    
    const target = event.target;
    const elementDetails = document.getElementById('element-details');
    
    // 阻止默認行為和事件冒泡
    event.preventDefault();
    event.stopPropagation();
    
    // 獲取元素信息
    const tagName = target.tagName.toLowerCase();
    const id = target.id ? `#${target.id}` : '';
    const classes = Array.from(target.classList).map(c => `.${c}`).join('');
    const selector = `${tagName}${id}${classes}`;
    
    // 獲取計算樣式
    const computedStyle = window.getComputedStyle(target);
    const styles = {
        width: computedStyle.width,
        height: computedStyle.height,
        padding: computedStyle.padding,
        margin: computedStyle.margin,
        color: computedStyle.color,
        backgroundColor: computedStyle.backgroundColor,
        fontSize: computedStyle.fontSize,
        fontFamily: computedStyle.fontFamily
    };
    
    // 生成詳情HTML
    let detailsHTML = `
        <div class="element-info">
            <div class="info-item"><strong>元素:</strong> ${tagName}</div>
            <div class="info-item"><strong>選擇器:</strong> ${selector}</div>
            <div class="info-item"><strong>文本:</strong> ${target.textContent.substring(0, 50)}${target.textContent.length > 50 ? '...' : ''}</div>
            <div class="info-item"><strong>尺寸:</strong> ${styles.width} x ${styles.height}</div>
            <div class="info-item"><strong>內邊距:</strong> ${styles.padding}</div>
            <div class="info-item"><strong>外邊距:</strong> ${styles.margin}</div>
            <div class="info-item"><strong>顏色:</strong> ${styles.color}</div>
            <div class="info-item"><strong>背景色:</strong> ${styles.backgroundColor}</div>
            <div class="info-item"><strong>字體大小:</strong> ${styles.fontSize}</div>
            <div class="info-item"><strong>字體:</strong> ${styles.fontFamily}</div>
        </div>
    `;
    
    // 添加屬性信息
    if (target.attributes.length > 0) {
        detailsHTML += '<div class="element-attributes"><strong>屬性:</strong><ul>';
        for (let i = 0; i < target.attributes.length; i++) {
            const attr = target.attributes[i];
            detailsHTML += `<li>${attr.name}: ${attr.value}</li>`;
        }
        detailsHTML += '</ul></div>';
    }
    
    elementDetails.innerHTML = detailsHTML;
    addEventLog(`檢查元素: ${selector}`);
}

/**
 * 注入偵錯代碼
 * @param {Document} iframeDocument - iframe文檔
 */
function injectDebugCode(iframeDocument) {
    try {
        // 創建偵錯樣式
        const debugStyle = iframeDocument.createElement('style');
        debugStyle.textContent = `
            .debug-highlight {
                outline: 2px solid red !important;
                background-color: rgba(255, 0, 0, 0.1) !important;
            }
        `;
        iframeDocument.head.appendChild(debugStyle);
        
        // 注入Console代理
        const script = iframeDocument.createElement('script');
        script.textContent = `
            (function() {
                // 保存原始方法
                const originalConsole = {
                    log: console.log,
                    error: console.error,
                    warn: console.warn,
                    info: console.info
                };
                
                // 重寫方法以捕獲日誌
                console.log = function() {
                    // 發送事件到父窗口
                    window.parent.postMessage({
                        type: 'console',
                        level: 'log',
                        args: Array.from(arguments).map(arg => String(arg))
                    }, '*');
                    
                    // 調用原始方法
                    return originalConsole.log.apply(console, arguments);
                };
                
                console.error = function() {
                    // 發送事件到父窗口
                    window.parent.postMessage({
                        type: 'console',
                        level: 'error',
                        args: Array.from(arguments).map(arg => String(arg))
                    }, '*');
                    
                    // 調用原始方法
                    return originalConsole.error.apply(console, arguments);
                };
                
                console.warn = function() {
                    // 發送事件到父窗口
                    window.parent.postMessage({
                        type: 'console',
                        level: 'warn',
                        args: Array.from(arguments).map(arg => String(arg))
                    }, '*');
                    
                    // 調用原始方法
                    return originalConsole.warn.apply(console, arguments);
                };
                
                console.info = function() {
                    // 發送事件到父窗口
                    window.parent.postMessage({
                        type: 'console',
                        level: 'info',
                        args: Array.from(arguments).map(arg => String(arg))
                    }, '*');
                    
                    // 調用原始方法
                    return originalConsole.info.apply(console, arguments);
                };
                
                // 捕獲錯誤
                window.addEventListener('error', function(event) {
                    window.parent.postMessage({
                        type: 'error',
                        message: event.message,
                        filename: event.filename,
                        lineno: event.lineno,
                        colno: event.colno
                    }, '*');
                });
                
                // 捕捉所有fetch請求
                const originalFetch = window.fetch;
                window.fetch = function() {
                    const url = arguments[0];
                    const options = arguments[1] || {};
                    
                    window.parent.postMessage({
                        type: 'fetch',
                        url: typeof url === 'string' ? url : url.url,
                        method: options.method || 'GET'
                    }, '*');
                    
                    return originalFetch.apply(window, arguments);
                };
                
                // 捕捉所有XMLHttpRequest
                const originalXhrOpen = XMLHttpRequest.prototype.open;
                XMLHttpRequest.prototype.open = function() {
                    const method = arguments[0];
                    const url = arguments[1];
                    
                    window.parent.postMessage({
                        type: 'xhr',
                        url: url,
                        method: method
                    }, '*');
                    
                    return originalXhrOpen.apply(this, arguments);
                };
                
                console.log('偵錯代碼已注入');
            })();
        `;
        iframeDocument.body.appendChild(script);
        
        // 監聽來自iframe的消息
        window.addEventListener('message', function(event) {
            if (event.data && event.data.type) {
                switch (event.data.type) {
                    case 'console':
                        addEventLog(`Console.${event.data.level}: ${event.data.args.join(' ')}`);
                        break;
                    case 'error':
                        addEventLog(`錯誤: ${event.data.message} [${event.data.filename}:${event.data.lineno}:${event.data.colno}]`);
                        break;
                    case 'fetch':
                        addEventLog(`Fetch請求: ${event.data.method} ${event.data.url}`);
                        break;
                    case 'xhr':
                        addEventLog(`XHR請求: ${event.data.method} ${event.data.url}`);
                        break;
                }
            }
        });
        
        addEventLog('偵錯代碼已注入');
    } catch (error) {
        console.error('注入偵錯代碼失敗:', error);
        addEventLog(`注入偵錯代碼失敗: ${error.message}`);
    }
}

/**
 * 執行PWA審計
 */
function runPwaAudit() {
    const auditScores = document.querySelectorAll('.score-circle');
    const auditDetails = document.getElementById('audit-details');
    const auditFullReport = document.getElementById('pwa-audit-full-report');
    const auditModal = document.getElementById('pwa-audit-modal');
    
    // 重置分數
    auditScores.forEach(score => {
        score.setAttribute('data-score', '0');
        score.querySelector('.score-value').textContent = '?';
    });
    
    // 顯示加載狀態
    auditDetails.innerHTML = '<div class="loading">正在評測中，請稍候...</div>';
    
    addEventLog('開始執行PWA符合度評測');
    
    // 模擬評測過程
    setTimeout(() => {
        // 此處應該是實際評測邏輯，這裡僅做模擬
        const scores = {
            performance: Math.floor(Math.random() * 40) + 60, // 60-100
            accessibility: Math.floor(Math.random() * 30) + 70, // 70-100
            bestPractices: Math.floor(Math.random() * 25) + 75, // 75-100
            seo: Math.floor(Math.random() * 20) + 80, // 80-100
            pwa: Math.floor(Math.random() * 50) + 50 // 50-100
        };
        
        // 更新分數
        auditScores[0].setAttribute('data-score', getScoreLevel(scores.performance));
        auditScores[0].querySelector('.score-value').textContent = scores.performance;
        
        auditScores[1].setAttribute('data-score', getScoreLevel(scores.accessibility));
        auditScores[1].querySelector('.score-value').textContent = scores.accessibility;
        
        auditScores[2].setAttribute('data-score', getScoreLevel(scores.bestPractices));
        auditScores[2].querySelector('.score-value').textContent = scores.bestPractices;
        
        auditScores[3].setAttribute('data-score', getScoreLevel(scores.seo));
        auditScores[3].querySelector('.score-value').textContent = scores.seo;
        
        auditScores[4].setAttribute('data-score', getScoreLevel(scores.pwa));
        auditScores[4].querySelector('.score-value').textContent = scores.pwa;
        
        // 更新詳情
        auditDetails.innerHTML = generateAuditDetails(scores);
        
        // 更新完整報告
        auditFullReport.innerHTML = generateAuditFullReport(scores);
        
        addEventLog('PWA符合度評測完成');
    }, 2000);
}

/**
 * 獲取分數等級
 * @param {number} score - 分數
 * @returns {number} 等級 (1-5)
 */
function getScoreLevel(score) {
    if (score < 50) return 1;
    if (score < 70) return 2;
    if (score < 80) return 3;
    if (score < 90) return 4;
    return 5;
}

/**
 * 生成審計詳情
 * @param {Object} scores - 分數對象
 * @returns {string} 詳情HTML
 */
function generateAuditDetails(scores) {
    const now = new Date().toLocaleString();
    
    return `
        <div class="audit-summary">
            <p><strong>評測時間:</strong> ${now}</p>
            <p><strong>評測頁面:</strong> ${pageConfig[currentPage].displayName}</p>
            <p><strong>評測設備:</strong> ${deviceConfig[currentDevice].displayName}</p>
            <p><strong>總體評分:</strong> ${Math.round((scores.performance + scores.accessibility + scores.bestPractices + scores.seo + scores.pwa) / 5)}</p>
        </div>
        <div class="audit-recommendations">
            <h4>改進建議:</h4>
            <ul>
                ${scores.performance < 90 ? '<li>優化頁面載入效能，減少不必要的資源載入。</li>' : ''}
                ${scores.accessibility < 90 ? '<li>提高頁面可訪問性，確保所有元素都有適當的標籤。</li>' : ''}
                ${scores.bestPractices < 90 ? '<li>遵循Web最佳實踐，更新過時的API使用。</li>' : ''}
                ${scores.seo < 90 ? '<li>優化搜索引擎可見性，添加適當的meta標籤。</li>' : ''}
                ${scores.pwa < 90 ? '<li>完善PWA功能，確保應用可安裝且支援離線使用。</li>' : ''}
            </ul>
        </div>
        <button id="view-full-report" class="btn" onclick="document.getElementById('pwa-audit-modal').style.display='block'">查看完整報告</button>
    `;
}

/**
 * 生成審計完整報告
 * @param {Object} scores - 分數對象
 * @returns {string} 完整報告HTML
 */
function generateAuditFullReport(scores) {
    const pwaItems = [
        { name: '應用清單', pass: true, details: '已提供有效的manifest.json文件' },
        { name: '離線支援', pass: scores.pwa > 70, details: scores.pwa > 70 ? '應用可在離線模式下運行' : '應用在離線模式下不可用' },
        { name: '安裝提示', pass: scores.pwa > 60, details: scores.pwa > 60 ? '應用可被安裝到主屏幕' : '缺少必要的安裝條件' },
        { name: 'Service Worker', pass: true, details: '已註冊有效的Service Worker' },
        { name: 'HTTPS', pass: true, details: '應用通過安全連接提供' },
        { name: '推送通知', pass: scores.pwa > 80, details: scores.pwa > 80 ? '應用支援推送通知' : '推送通知功能未完全實現' }
    ];
    
    return `
        <div class="full-report">
            <h3>PWA符合度評測報告</h3>
            <p class="report-date">評測時間: ${new Date().toLocaleString()}</p>
            
            <h4>PWA功能檢查:</h4>
            <table class="audit-table">
                <thead>
                    <tr>
                        <th>功能</th>
                        <th>狀態</th>
                        <th>詳情</th>
                    </tr>
                </thead>
                <tbody>
                    ${pwaItems.map(item => `
                        <tr>
                            <td>${item.name}</td>
                            <td class="${item.pass ? 'pass' : 'fail'}">${item.pass ? '通過' : '未通過'}</td>
                            <td>${item.details}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
            
            <h4>詳細評分:</h4>
            <table class="audit-table">
                <thead>
                    <tr>
                        <th>類別</th>
                        <th>分數</th>
                        <th>評價</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>效能</td>
                        <td>${scores.performance}</td>
                        <td>${getScoreDescription(scores.performance)}</td>
                    </tr>
                    <tr>
                        <td>可訪問性</td>
                        <td>${scores.accessibility}</td>
                        <td>${getScoreDescription(scores.accessibility)}</td>
                    </tr>
                    <tr>
                        <td>最佳實踐</td>
                        <td>${scores.bestPractices}</td>
                        <td>${getScoreDescription(scores.bestPractices)}</td>
                    </tr>
                    <tr>
                        <td>SEO</td>
                        <td>${scores.seo}</td>
                        <td>${getScoreDescription(scores.seo)}</td>
                    </tr>
                    <tr>
                        <td>PWA</td>
                        <td>${scores.pwa}</td>
                        <td>${getScoreDescription(scores.pwa)}</td>
                    </tr>
                </tbody>
            </table>
            
            <div class="report-actions">
                <button class="btn" onclick="window.print()">打印報告</button>
                <button class="btn" onclick="document.getElementById('pwa-audit-modal').style.display='none'">關閉</button>
            </div>
        </div>
    `;
}

/**
 * 獲取分數描述
 * @param {number} score - 分數
 * @returns {string} 分數描述
 */
function getScoreDescription(score) {
    if (score < 50) return '很差，需要立即改進';
    if (score < 70) return '較差，有明顯改進空間';
    if (score < 80) return '一般，可以改進';
    if (score < 90) return '良好，有小幅改進空間';
    return '優秀，符合最佳實踐';
} 
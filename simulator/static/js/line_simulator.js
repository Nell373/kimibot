/**
 * LINE 智能記帳與提醒助手 - LINE模擬器 JavaScript
 * 
 * 此文件提供LINE模擬器的互動功能:
 * 1. 聊天訊息發送與接收
 * 2. 模板訊息使用
 * 3. 快速選單功能
 * 4. Flex Message 渲染
 * 5. 回應詳情查看
 */

// 全域變數
let chatHistory = [];
let templateMessages = [];
let currentUserID = 'test_user_id';
let flexMessages = {};

// 初始化頁面
document.addEventListener('DOMContentLoaded', function() {
    // 獲取DOM元素
    const chatContainer = document.getElementById('chat-container');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const userIdInput = document.getElementById('user-id');
    const clearChatButton = document.getElementById('clear-chat');
    const saveChatButton = document.getElementById('save-chat');
    const templateButtons = document.querySelectorAll('.template-btn');
    const customMessageInput = document.getElementById('custom-message');
    const addTemplateButton = document.getElementById('add-template');
    const quickButtons = document.querySelectorAll('.quick-btn');
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const flexPreviewModal = document.getElementById('flex-preview-modal');
    const flexPreviewClose = document.querySelector('#flex-preview-modal .close');
    const testFlexButton = document.getElementById('test-flex');
    const testApiButton = document.getElementById('test-api');
    const reloadBotButton = document.getElementById('reload-bot');

    // 載入之前的聊天記錄
    loadChatHistory();
    loadTemplateMessages();

    // 設置用戶ID變更事件
    userIdInput.addEventListener('change', function() {
        currentUserID = this.value;
        addLogMessage(`用戶ID已變更為: ${currentUserID}`);
    });

    // 設置發送訊息事件
    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // 設置清除聊天記錄事件
    clearChatButton.addEventListener('click', function() {
        if (confirm('確定要清除所有聊天記錄嗎？')) {
            chatContainer.innerHTML = '';
            chatHistory = [];
            localStorage.removeItem('chatHistory');
            addLogMessage('聊天記錄已清除');
        }
    });

    // 設置儲存聊天記錄事件
    saveChatButton.addEventListener('click', function() {
        saveChatHistory();
        addLogMessage('聊天記錄已儲存');
    });

    // 設置模板訊息事件
    templateButtons.forEach(button => {
        button.addEventListener('click', function() {
            const message = this.getAttribute('data-message');
            messageInput.value = message;
        });
    });

    // 設置新增自訂模板事件
    addTemplateButton.addEventListener('click', function() {
        const customMessage = customMessageInput.value.trim();
        if (customMessage) {
            addTemplateMessage(customMessage);
            customMessageInput.value = '';
        }
    });

    // 設置快速選單事件
    quickButtons.forEach(button => {
        button.addEventListener('click', function() {
            const action = this.getAttribute('data-action');
            handleQuickAction(action);
        });
    });

    // 設置分頁切換事件
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tabId = this.getAttribute('data-tab');
            
            // 移除所有分頁的 active 類
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // 為當前分頁添加 active 類
            this.classList.add('active');
            document.getElementById(`${tabId}-content`).classList.add('active');
        });
    });

    // 設置 Flex 預覽模態框事件
    flexPreviewClose.addEventListener('click', function() {
        flexPreviewModal.style.display = 'none';
    });

    window.addEventListener('click', function(event) {
        if (event.target === flexPreviewModal) {
            flexPreviewModal.style.display = 'none';
        }
    });

    // 設置測試按鈕事件
    testFlexButton.addEventListener('click', testFlexMessage);
    testApiButton.addEventListener('click', testApiConnection);
    reloadBotButton.addEventListener('click', reloadBot);

    // 添加初始日誌訊息
    addLogMessage('LINE 模擬器已初始化');
});

/**
 * 發送訊息到Bot
 */
function sendMessage() {
    const messageInput = document.getElementById('message-input');
    const message = messageInput.value.trim();
    
    if (!message) return;
    
    // 顯示用戶訊息
    displayUserMessage(message);
    
    // 發送訊息到API
    sendToApi(message);
    
    // 清空輸入框
    messageInput.value = '';
}

/**
 * 在聊天視窗顯示用戶訊息
 * @param {string} message - 用戶發送的訊息
 */
function displayUserMessage(message) {
    const chatContainer = document.getElementById('chat-container');
    const timestamp = new Date().toLocaleTimeString();
    
    const messageElement = document.createElement('div');
    messageElement.className = 'user-message';
    messageElement.innerHTML = `
        <div class="message-content">${message}</div>
        <div class="timestamp">${timestamp}</div>
    `;
    
    chatContainer.appendChild(messageElement);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    // 添加到聊天歷史
    chatHistory.push({
        type: 'user',
        message: message,
        timestamp: timestamp
    });
}

/**
 * 在聊天視窗顯示機器人訊息
 * @param {string|object} message - 機器人發送的訊息或Flex Message
 * @param {string} type - 訊息類型 (text/flex)
 */
function displayBotMessage(message, type = 'text') {
    const chatContainer = document.getElementById('chat-container');
    const timestamp = new Date().toLocaleTimeString();
    
    const messageElement = document.createElement('div');
    messageElement.className = 'bot-message';
    
    if (type === 'text') {
        messageElement.innerHTML = `
            <div class="message-content">${message}</div>
            <div class="timestamp">${timestamp}</div>
        `;
    } else if (type === 'flex') {
        // 保存Flex消息以供預覽
        const flexId = 'flex_' + Date.now();
        flexMessages[flexId] = message;
        
        // 呈現Flex消息
        renderFlexMessage(message, messageElement, flexId);
        
        const timestampElement = document.createElement('div');
        timestampElement.className = 'timestamp';
        timestampElement.textContent = timestamp;
        messageElement.appendChild(timestampElement);
    }
    
    chatContainer.appendChild(messageElement);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    // 添加到聊天歷史
    chatHistory.push({
        type: 'bot',
        message: message,
        messageType: type,
        timestamp: timestamp
    });
}

/**
 * 渲染Flex Message
 * @param {object} flexContent - Flex Message內容
 * @param {HTMLElement} container - 容器元素
 * @param {string} flexId - Flex Message ID
 */
function renderFlexMessage(flexContent, container, flexId) {
    // 創建渲染好的flex內容容器
    const flexContainer = document.createElement('div');
    flexContainer.className = 'flex-message-container';
    flexContainer.setAttribute('data-flex-id', flexId);
    
    // 發送API請求渲染Flex Message
    fetch('/api/flex/render', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ content: flexContent })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            flexContainer.innerHTML = data.html;
            
            // 添加預覽按鈕
            const previewButton = document.createElement('button');
            previewButton.className = 'flex-preview-btn';
            previewButton.innerHTML = '<i class="fas fa-expand"></i> 預覽';
            previewButton.addEventListener('click', function() {
                showFlexPreview(flexId);
            });
            
            flexContainer.appendChild(previewButton);
        } else {
            flexContainer.innerHTML = `<div class="error-message">無法渲染Flex Message: ${data.error}</div>`;
        }
    })
    .catch(error => {
        console.error('渲染Flex Message失敗:', error);
        flexContainer.innerHTML = `<div class="error-message">渲染失敗: ${error.message}</div>`;
    });
    
    // 將訊息內容添加到消息元素中
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    messageContent.appendChild(flexContainer);
    container.appendChild(messageContent);
}

/**
 * 顯示Flex Message預覽
 * @param {string} flexId - Flex Message ID
 */
function showFlexPreview(flexId) {
    const flexPreviewModal = document.getElementById('flex-preview-modal');
    const flexPreviewContainer = document.getElementById('flex-preview-container');
    
    // 獲取Flex Message內容
    const flexContent = flexMessages[flexId];
    
    // 發送API請求渲染Flex Message
    fetch('/api/flex/render', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
            content: flexContent,
            fullPreview: true
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            flexPreviewContainer.innerHTML = data.html;
            flexPreviewModal.style.display = 'block';
        } else {
            alert(`無法預覽Flex Message: ${data.error}`);
        }
    })
    .catch(error => {
        console.error('預覽Flex Message失敗:', error);
        alert(`預覽失敗: ${error.message}`);
    });
}

/**
 * 發送訊息到API
 * @param {string} message - 用戶發送的訊息
 */
function sendToApi(message) {
    const responseJson = document.getElementById('response-json');
    responseJson.textContent = '發送請求中...';
    
    fetch('/api/line/send', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            user_id: currentUserID,
            message: message
        })
    })
    .then(response => response.json())
    .then(data => {
        // 顯示JSON回應
        responseJson.textContent = JSON.stringify(data, null, 2);
        
        if (data.success) {
            // 處理回應訊息
            handleBotResponse(data.response);
            addLogMessage(`收到Bot回應: ${data.response.length}個訊息`);
        } else {
            // 顯示錯誤訊息
            displayBotMessage(`錯誤: ${data.error}`);
            addLogMessage(`錯誤: ${data.error}`);
        }
    })
    .catch(error => {
        console.error('發送訊息失敗:', error);
        responseJson.textContent = `發送失敗: ${error.message}`;
        displayBotMessage(`發送失敗: ${error.message}`);
        addLogMessage(`發送失敗: ${error.message}`);
    });
}

/**
 * 處理Bot回應
 * @param {Array} responses - Bot回應的訊息陣列
 */
function handleBotResponse(responses) {
    if (!Array.isArray(responses)) {
        responses = [responses];
    }
    
    responses.forEach(response => {
        if (typeof response === 'string') {
            // 文字訊息
            displayBotMessage(response);
        } else if (response.type === 'flex') {
            // Flex訊息
            displayBotMessage(response.contents, 'flex');
        } else {
            // 其他類型訊息
            displayBotMessage(JSON.stringify(response));
        }
    });
}

/**
 * 處理快速選單動作
 * @param {string} action - 快速選單動作
 */
function handleQuickAction(action) {
    let message = '';
    
    switch (action) {
        case 'menu':
            message = '選單';
            break;
        case 'accounting':
            message = '記帳';
            break;
        case 'reminder':
            message = '提醒';
            break;
        case 'query':
            message = '查詢';
            break;
    }
    
    if (message) {
        document.getElementById('message-input').value = message;
        sendMessage();
    }
}

/**
 * 添加日誌訊息
 * @param {string} message - 日誌訊息
 */
function addLogMessage(message) {
    const logMessages = document.getElementById('log-messages');
    const timestamp = new Date().toLocaleTimeString();
    
    const logItem = document.createElement('div');
    logItem.className = 'log-item';
    logItem.textContent = `[${timestamp}] ${message}`;
    
    logMessages.appendChild(logItem);
    logMessages.scrollTop = logMessages.scrollHeight;
}

/**
 * 添加模板訊息
 * @param {string} message - 模板訊息
 */
function addTemplateMessage(message) {
    const templateList = document.querySelector('.template-list');
    
    const templateButton = document.createElement('button');
    templateButton.className = 'template-btn';
    templateButton.setAttribute('data-message', message);
    templateButton.textContent = message.length > 20 ? message.substring(0, 20) + '...' : message;
    
    templateButton.addEventListener('click', function() {
        document.getElementById('message-input').value = message;
    });
    
    templateList.appendChild(templateButton);
    
    // 保存到本地
    templateMessages.push(message);
    localStorage.setItem('templateMessages', JSON.stringify(templateMessages));
    
    addLogMessage(`新增模板訊息: ${message}`);
}

/**
 * 測試 Flex Message
 */
function testFlexMessage() {
    const debugOutput = document.getElementById('debug-output');
    debugOutput.textContent = '測試 Flex Message 中...';
    
    // 範例 Flex Message
    const sampleFlex = {
        "type": "bubble",
        "hero": {
            "type": "image",
            "url": "https://via.placeholder.com/1000x400/06c755/ffffff?text=LINE+Bot",
            "size": "full",
            "aspectRatio": "20:8",
            "aspectMode": "cover"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "Flex Message 測試",
                    "weight": "bold",
                    "size": "xl",
                    "color": "#06c755"
                },
                {
                    "type": "text",
                    "text": "這是一個測試用的 Flex Message 範例",
                    "margin": "md"
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "action": {
                        "type": "message",
                        "label": "確認",
                        "text": "確認"
                    },
                    "color": "#06c755"
                }
            ]
        }
    };
    
    displayBotMessage(sampleFlex, 'flex');
    debugOutput.textContent = '已顯示測試用 Flex Message';
    addLogMessage('已顯示測試用 Flex Message');
}

/**
 * 測試 API 連接
 */
function testApiConnection() {
    const debugOutput = document.getElementById('debug-output');
    debugOutput.textContent = '測試 API 連接中...';
    
    fetch('/health')
        .then(response => response.json())
        .then(data => {
            debugOutput.textContent = `API 連接成功\n狀態: ${data.status}\n版本: ${data.version}`;
            addLogMessage(`API 連接成功，狀態: ${data.status}`);
        })
        .catch(error => {
            debugOutput.textContent = `API 連接失敗: ${error.message}`;
            addLogMessage(`API 連接失敗: ${error.message}`);
        });
}

/**
 * 重新載入 Bot
 */
function reloadBot() {
    const debugOutput = document.getElementById('debug-output');
    debugOutput.textContent = '重新載入 Bot 中...';
    
    fetch('/api/line/send', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            user_id: currentUserID,
            message: '__reload__'  // 特殊指令用於重新載入 Bot
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            debugOutput.textContent = 'Bot 已重新載入';
            addLogMessage('Bot 已重新載入');
            displayBotMessage('Bot 已重新載入，可以開始測試新功能。');
        } else {
            debugOutput.textContent = `重新載入 Bot 失敗: ${data.error}`;
            addLogMessage(`重新載入 Bot 失敗: ${data.error}`);
        }
    })
    .catch(error => {
        debugOutput.textContent = `重新載入 Bot 失敗: ${error.message}`;
        addLogMessage(`重新載入 Bot 失敗: ${error.message}`);
    });
}

/**
 * 載入聊天歷史
 */
function loadChatHistory() {
    const chatContainer = document.getElementById('chat-container');
    
    // 從 localStorage 載入聊天歷史
    const savedHistory = localStorage.getItem('chatHistory');
    
    if (savedHistory) {
        try {
            chatHistory = JSON.parse(savedHistory);
            
            // 顯示歷史訊息
            chatHistory.forEach(item => {
                if (item.type === 'user') {
                    const messageElement = document.createElement('div');
                    messageElement.className = 'user-message';
                    messageElement.innerHTML = `
                        <div class="message-content">${item.message}</div>
                        <div class="timestamp">${item.timestamp}</div>
                    `;
                    chatContainer.appendChild(messageElement);
                } else if (item.type === 'bot') {
                    const messageElement = document.createElement('div');
                    messageElement.className = 'bot-message';
                    
                    if (item.messageType === 'text') {
                        messageElement.innerHTML = `
                            <div class="message-content">${item.message}</div>
                            <div class="timestamp">${item.timestamp}</div>
                        `;
                    } else if (item.messageType === 'flex') {
                        const flexId = 'flex_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
                        flexMessages[flexId] = item.message;
                        renderFlexMessage(item.message, messageElement, flexId);
                        
                        const timestampElement = document.createElement('div');
                        timestampElement.className = 'timestamp';
                        timestampElement.textContent = item.timestamp;
                        messageElement.appendChild(timestampElement);
                    }
                    
                    chatContainer.appendChild(messageElement);
                }
            });
            
            chatContainer.scrollTop = chatContainer.scrollHeight;
            addLogMessage(`已載入${chatHistory.length}條聊天記錄`);
        } catch (error) {
            console.error('載入聊天歷史失敗:', error);
            addLogMessage(`載入聊天歷史失敗: ${error.message}`);
        }
    }
}

/**
 * 載入模板訊息
 */
function loadTemplateMessages() {
    const savedTemplates = localStorage.getItem('templateMessages');
    
    if (savedTemplates) {
        try {
            templateMessages = JSON.parse(savedTemplates);
            
            // 顯示模板訊息
            templateMessages.forEach(message => {
                addTemplateMessage(message);
            });
            
            addLogMessage(`已載入${templateMessages.length}個模板訊息`);
        } catch (error) {
            console.error('載入模板訊息失敗:', error);
            addLogMessage(`載入模板訊息失敗: ${error.message}`);
        }
    }
}

/**
 * 保存聊天歷史
 */
function saveChatHistory() {
    localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
} 
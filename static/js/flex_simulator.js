/**
 * LINE Flex消息模擬器
 * 此程式用於將LINE Flex消息JSON轉換為HTML以便在PWA中顯示
 */

class FlexSimulator {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`容器元素 #${containerId} 未找到`);
            return;
        }
        
        this.options = Object.assign({
            maxWidth: 450,
            primaryColor: '#06c755',
            secondaryColor: '#f5f5f5',
            backgroundColor: '#ffffff',
            darkMode: false
        }, options);
        
        this.init();
    }
    
    init() {
        this.container.classList.add('line-flex-container');
        if (this.options.darkMode) {
            this.container.classList.add('dark-mode');
        }
        this.container.style.maxWidth = `${this.options.maxWidth}px`;
    }
    
    /**
     * 渲染Flex消息
     * @param {Object} flexJson - LINE Flex消息JSON對象
     * @returns {HTMLElement} 渲染後的HTML元素
     */
    render(flexJson) {
        if (!flexJson) {
            return this._createErrorElement('無效的Flex消息JSON');
        }
        
        try {
            // 清空容器
            this.container.innerHTML = '';
            
            // 創建Flex消息元素
            const messageElement = this._createFlexMessage(flexJson);
            this.container.appendChild(messageElement);
            
            return messageElement;
        } catch (error) {
            console.error('渲染Flex消息時發生錯誤:', error);
            const errorElement = this._createErrorElement(`渲染錯誤: ${error.message}`);
            this.container.appendChild(errorElement);
            return errorElement;
        }
    }
    
    /**
     * 創建Flex消息元素
     * @private
     * @param {Object} message - Flex消息對象
     * @returns {HTMLElement} 消息元素
     */
    _createFlexMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('line-flex-message');
        
        const type = message.type;
        const contents = message.contents;
        
        if (type === 'flex' && contents) {
            switch (contents.type) {
                case 'bubble':
                    messageElement.appendChild(this._createBubble(contents));
                    break;
                case 'carousel':
                    messageElement.appendChild(this._createCarousel(contents));
                    break;
                default:
                    messageElement.appendChild(this._createErrorElement(`不支持的Flex類型: ${contents.type}`));
            }
        } else {
            messageElement.appendChild(this._createErrorElement('無效的Flex消息格式'));
        }
        
        return messageElement;
    }
    
    /**
     * 創建氣泡容器
     * @private
     * @param {Object} bubble - 氣泡容器對象
     * @returns {HTMLElement} 氣泡元素
     */
    _createBubble(bubble) {
        const bubbleElement = document.createElement('div');
        bubbleElement.classList.add('line-flex-bubble');
        
        // 設置背景色
        if (bubble.styles && bubble.styles.body && bubble.styles.body.backgroundColor) {
            bubbleElement.style.backgroundColor = bubble.styles.body.backgroundColor;
        }
        
        // 處理各部分內容
        if (bubble.hero) {
            bubbleElement.appendChild(this._createHero(bubble.hero));
        }
        
        if (bubble.header) {
            bubbleElement.appendChild(this._createBox(bubble.header, 'header'));
        }
        
        if (bubble.body) {
            bubbleElement.appendChild(this._createBox(bubble.body, 'body'));
        }
        
        if (bubble.footer) {
            bubbleElement.appendChild(this._createBox(bubble.footer, 'footer'));
        }
        
        return bubbleElement;
    }
    
    /**
     * 創建輪播容器
     * @private
     * @param {Object} carousel - 輪播容器對象
     * @returns {HTMLElement} 輪播元素
     */
    _createCarousel(carousel) {
        const carouselElement = document.createElement('div');
        carouselElement.classList.add('line-flex-carousel');
        
        if (carousel.contents && Array.isArray(carousel.contents)) {
            carousel.contents.forEach(bubble => {
                if (bubble.type === 'bubble') {
                    carouselElement.appendChild(this._createBubble(bubble));
                }
            });
        }
        
        return carouselElement;
    }
    
    /**
     * 創建英雄部分
     * @private
     * @param {Object} hero - 英雄部分對象
     * @returns {HTMLElement} 英雄元素
     */
    _createHero(hero) {
        const heroElement = document.createElement('div');
        heroElement.classList.add('line-flex-hero');
        
        if (hero.type === 'image') {
            const imageElement = this._createImage(hero);
            heroElement.appendChild(imageElement);
            
            // 處理英雄圖片上的按鈕
            if (hero.action) {
                heroElement.style.cursor = 'pointer';
                heroElement.addEventListener('click', () => this._handleAction(hero.action));
            }
        }
        
        return heroElement;
    }
    
    /**
     * 創建盒子容器
     * @private
     * @param {Object} box - 盒子容器對象
     * @param {String} section - 盒子所在部分
     * @returns {HTMLElement} 盒子元素
     */
    _createBox(box, section = '') {
        const boxElement = document.createElement('div');
        boxElement.classList.add('line-flex-box');
        
        // 設置佈局方向
        if (box.layout === 'horizontal') {
            boxElement.classList.add('horizontal');
        } else {
            boxElement.classList.add('vertical');
        }
        
        // 設置對齊方式
        if (box.alignItems) {
            boxElement.classList.add(box.alignItems);
        }
        
        if (box.justifyContent) {
            boxElement.classList.add(`justify-${box.justifyContent}`);
        }
        
        // 設置背景色
        if (box.backgroundColor) {
            boxElement.style.backgroundColor = box.backgroundColor;
        }
        
        // 設置內邊距
        if (box.paddingAll) {
            boxElement.style.padding = `${box.paddingAll}px`;
        } else {
            if (box.paddingTop) boxElement.style.paddingTop = `${box.paddingTop}px`;
            if (box.paddingBottom) boxElement.style.paddingBottom = `${box.paddingBottom}px`;
            if (box.paddingStart) boxElement.style.paddingLeft = `${box.paddingStart}px`;
            if (box.paddingEnd) boxElement.style.paddingRight = `${box.paddingEnd}px`;
        }
        
        // 設置邊距
        if (box.margin) {
            boxElement.style.margin = `${box.margin}px`;
        } else {
            if (box.marginTop) boxElement.style.marginTop = `${box.marginTop}px`;
            if (box.marginBottom) boxElement.style.marginBottom = `${box.marginBottom}px`;
            if (box.marginStart) boxElement.style.marginLeft = `${box.marginStart}px`;
            if (box.marginEnd) boxElement.style.marginRight = `${box.marginEnd}px`;
        }
        
        // 添加section特定的類
        if (section) {
            boxElement.classList.add(`line-flex-${section}`);
        }
        
        // 處理內容
        if (box.contents && Array.isArray(box.contents)) {
            box.contents.forEach(content => {
                boxElement.appendChild(this._createComponent(content));
            });
        }
        
        return boxElement;
    }
    
    /**
     * 創建組件
     * @private
     * @param {Object} component - 組件對象
     * @returns {HTMLElement} 組件元素
     */
    _createComponent(component) {
        if (!component || !component.type) {
            return this._createErrorElement('無效的組件');
        }
        
        let componentElement;
        
        switch (component.type) {
            case 'box':
                componentElement = this._createBox(component);
                break;
            case 'text':
                componentElement = this._createText(component);
                break;
            case 'image':
                componentElement = this._createImage(component);
                break;
            case 'button':
                componentElement = this._createButton(component);
                break;
            case 'separator':
                componentElement = this._createSeparator(component);
                break;
            case 'spacer':
                componentElement = this._createSpacer(component);
                break;
            case 'icon':
                componentElement = this._createIcon(component);
                break;
            default:
                componentElement = this._createErrorElement(`不支持的組件類型: ${component.type}`);
        }
        
        // 設置彈性比例
        if (component.flex !== undefined) {
            componentElement.style.flex = component.flex;
        }
        
        // 處理元素點擊動作
        if (component.action) {
            componentElement.style.cursor = 'pointer';
            componentElement.addEventListener('click', () => this._handleAction(component.action));
        }
        
        return componentElement;
    }
    
    /**
     * 創建文字組件
     * @private
     * @param {Object} text - 文字組件對象
     * @returns {HTMLElement} 文字元素
     */
    _createText(text) {
        const textElement = document.createElement('div');
        textElement.classList.add('line-flex-text');
        
        // 設置文字大小
        if (text.size) {
            textElement.classList.add(text.size);
        }
        
        // 設置文字顏色
        if (text.color) {
            textElement.style.color = text.color;
        }
        
        // 設置文字對齊
        if (text.align) {
            textElement.classList.add(text.align);
        }
        
        // 設置文字裝飾
        if (text.weight === 'bold') {
            textElement.classList.add('bold');
        }
        
        if (text.style === 'italic') {
            textElement.classList.add('italic');
        }
        
        if (text.decoration === 'underline') {
            textElement.classList.add('underline');
        }
        
        // 設置內容
        if (text.text) {
            // 處理可能包含HTML標籤的內容
            if (text.wrap) {
                textElement.innerHTML = text.text.replace(/\n/g, '<br>');
            } else {
                textElement.textContent = text.text;
                textElement.style.whiteSpace = 'nowrap';
                textElement.style.overflow = 'hidden';
                textElement.style.textOverflow = 'ellipsis';
            }
        }
        
        // 設置內外邊距
        if (text.margin) {
            textElement.style.margin = `${text.margin}px`;
        }
        
        if (text.paddingAll) {
            textElement.style.padding = `${text.paddingAll}px`;
        }
        
        return textElement;
    }
    
    /**
     * 創建圖片組件
     * @private
     * @param {Object} image - 圖片組件對象
     * @returns {HTMLElement} 圖片元素
     */
    _createImage(image) {
        const container = document.createElement('div');
        container.style.position = 'relative';
        
        if (image.aspectRatio) {
            const ratio = image.aspectRatio.split(':');
            if (ratio.length === 2) {
                const width = parseFloat(ratio[0]);
                const height = parseFloat(ratio[1]);
                if (!isNaN(width) && !isNaN(height) && height > 0) {
                    container.style.paddingBottom = `${(height / width) * 100}%`;
                    container.style.width = '100%';
                }
            }
        }
        
        const imgElement = document.createElement('img');
        imgElement.classList.add('line-flex-image');
        
        // 設置圖片URL
        if (image.url) {
            imgElement.src = image.url;
            imgElement.alt = image.altText || '';
        } else {
            imgElement.src = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMDAiIGhlaWdodD0iMTAwIiB2aWV3Qm94PSIwIDAgMTAwIDEwMCI+PHJlY3Qgd2lkdGg9IjEwMCIgaGVpZ2h0PSIxMDAiIGZpbGw9IiNlZWUiLz48dGV4dCB4PSI1MCIgeT0iNTAiIGZvbnQtc2l6ZT0iMTQiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGFsaWdubWVudC1iYXNlbGluZT0ibWlkZGxlIiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZmlsbD0iIzk5OSI+5Zu+54mHPC90ZXh0Pjwvc3ZnPg==';
            imgElement.alt = '預設圖片';
        }
        
        // 設置大小和佈局
        if (image.size === 'full') {
            imgElement.style.width = '100%';
        } else if (image.size) {
            imgElement.style.width = image.size;
        }
        
        // 設置圖片尺寸方式
        if (image.aspectMode === 'cover') {
            imgElement.classList.add('fill');
            imgElement.style.position = 'absolute';
            imgElement.style.top = '0';
            imgElement.style.left = '0';
            imgElement.style.width = '100%';
            imgElement.style.height = '100%';
        } else {
            imgElement.style.maxWidth = '100%';
        }
        
        // 設置圖片圓角
        if (image.aspectMode === 'cover' && image.cornerRadius) {
            container.style.borderRadius = `${image.cornerRadius}px`;
            container.style.overflow = 'hidden';
        } else if (image.cornerRadius) {
            imgElement.style.borderRadius = `${image.cornerRadius}px`;
        }
        
        // 設置內外邊距
        if (image.margin) {
            container.style.margin = `${image.margin}px`;
        }
        
        container.appendChild(imgElement);
        return container;
    }
    
    /**
     * 創建按鈕組件
     * @private
     * @param {Object} button - 按鈕組件對象
     * @returns {HTMLElement} 按鈕元素
     */
    _createButton(button) {
        const buttonElement = document.createElement('div');
        buttonElement.classList.add('line-flex-button');
        
        // 設置按鈕樣式
        if (button.style === 'primary') {
            buttonElement.classList.add('primary');
        } else if (button.style === 'secondary') {
            buttonElement.classList.add('secondary');
        } else if (button.style === 'link') {
            buttonElement.classList.add('link');
        }
        
        // 設置按鈕高度
        if (button.height === 'sm') {
            buttonElement.style.padding = '8px';
        }
        
        // 設置按鈕顏色
        if (button.color) {
            buttonElement.style.backgroundColor = button.color;
        }
        
        if (button.action) {
            // 設置按鈕文字
            buttonElement.textContent = button.action.label || '';
            
            // 處理按鈕點擊
            buttonElement.addEventListener('click', () => this._handleAction(button.action));
        }
        
        // 設置內外邊距
        if (button.margin) {
            buttonElement.style.margin = `${button.margin}px`;
        }
        
        return buttonElement;
    }
    
    /**
     * 創建分隔線組件
     * @private
     * @param {Object} separator - 分隔線組件對象
     * @returns {HTMLElement} 分隔線元素
     */
    _createSeparator(separator) {
        const separatorElement = document.createElement('div');
        separatorElement.classList.add('line-flex-separator');
        
        // 設置分隔線顏色
        if (separator.color) {
            separatorElement.style.backgroundColor = separator.color;
        }
        
        // 設置內外邊距
        if (separator.margin) {
            separatorElement.style.margin = `${separator.margin}px`;
        }
        
        return separatorElement;
    }
    
    /**
     * 創建間隔組件
     * @private
     * @param {Object} spacer - 間隔組件對象
     * @returns {HTMLElement} 間隔元素
     */
    _createSpacer(spacer) {
        const spacerElement = document.createElement('div');
        spacerElement.classList.add('line-flex-spacer');
        
        // 設置間隔大小
        if (spacer.size) {
            spacerElement.classList.add(spacer.size);
        }
        
        return spacerElement;
    }
    
    /**
     * 創建圖標組件
     * @private
     * @param {Object} icon - 圖標組件對象
     * @returns {HTMLElement} 圖標元素
     */
    _createIcon(icon) {
        const iconElement = document.createElement('img');
        iconElement.classList.add('line-flex-icon');
        
        // 設置圖標URL
        if (icon.url) {
            iconElement.src = icon.url;
            iconElement.alt = '圖標';
        } else {
            iconElement.src = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0Ij48cGF0aCBkPSJNMTIgMkM2LjQ4IDIgMiA2LjQ4IDIgMTJzNC40OCAxMCAxMCAxMCAxMC00LjQ4IDEwLTEwUzE3LjUyIDIgMTIgMnptMCAxOGMtNC40MiAwLTgtMy41OC04LThzMy41OC04IDgtOCA4IDMuNTggOCA4LTMuNTggOC04IDh6Ii8+PHBhdGggZD0iTTAgMGgyNHYyNEgweiIgZmlsbD0ibm9uZSIvPjwvc3ZnPg==';
            iconElement.alt = '預設圖標';
        }
        
        // 設置圖標大小
        if (icon.size) {
            iconElement.classList.add(icon.size);
        }
        
        // 設置內外邊距
        if (icon.margin) {
            iconElement.style.margin = `${icon.margin}px`;
        }
        
        return iconElement;
    }
    
    /**
     * 創建錯誤提示元素
     * @private
     * @param {String} message - 錯誤消息
     * @returns {HTMLElement} 錯誤元素
     */
    _createErrorElement(message) {
        const errorElement = document.createElement('div');
        errorElement.classList.add('line-flex-error');
        errorElement.textContent = message;
        return errorElement;
    }
    
    /**
     * 處理元素點擊動作
     * @private
     * @param {Object} action - 動作對象
     */
    _handleAction(action) {
        if (!action || !action.type) return;
        
        console.log('執行動作:', action);
        
        switch (action.type) {
            case 'uri':
                // 打開URL
                if (action.uri) {
                    window.open(action.uri, '_blank');
                }
                break;
            case 'message':
                // 顯示消息
                if (action.text) {
                    this._showActionFeedback(`發送消息: ${action.text}`);
                }
                break;
            case 'postback':
                // 處理回發數據
                if (action.data) {
                    this._showActionFeedback(`回發數據: ${action.data}`);
                    // 在模擬器中發送事件
                    const event = new CustomEvent('flex:postback', {
                        detail: {
                            data: action.data,
                            displayText: action.displayText
                        }
                    });
                    window.dispatchEvent(event);
                }
                break;
            default:
                console.log(`不支持的動作類型: ${action.type}`);
        }
    }
    
    /**
     * 顯示動作反饋
     * @private
     * @param {String} message - 反饋消息
     */
    _showActionFeedback(message) {
        const feedbackEl = document.createElement('div');
        feedbackEl.style.position = 'fixed';
        feedbackEl.style.bottom = '20px';
        feedbackEl.style.left = '50%';
        feedbackEl.style.transform = 'translateX(-50%)';
        feedbackEl.style.background = 'rgba(0,0,0,0.7)';
        feedbackEl.style.color = 'white';
        feedbackEl.style.padding = '10px 15px';
        feedbackEl.style.borderRadius = '5px';
        feedbackEl.style.zIndex = '9999';
        feedbackEl.textContent = message;
        
        document.body.appendChild(feedbackEl);
        
        setTimeout(() => {
            feedbackEl.style.opacity = '0';
            feedbackEl.style.transition = 'opacity 0.5s';
            setTimeout(() => document.body.removeChild(feedbackEl), 500);
        }, 2000);
    }
}

// 全局暴露FlexSimulator
window.FlexSimulator = FlexSimulator; 
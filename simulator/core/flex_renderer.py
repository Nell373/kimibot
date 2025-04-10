#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
LINE Flex Message 渲染器
將 LINE Flex Message 轉換為 HTML 顯示
"""

import logging
import json
import re
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class FlexRenderer:
    """將 LINE Flex Message 轉換為 HTML 的類"""
    
    def __init__(self):
        """初始化渲染器"""
        # 載入 Flex Message 樣式
        self.css = self._load_css()
        logger.info("Flex Message 渲染器初始化完成")
    
    def render(self, flex_content):
        """渲染 Flex Message 為 HTML"""
        try:
            if isinstance(flex_content, str):
                try:
                    flex_content = json.loads(flex_content)
                except json.JSONDecodeError:
                    return f"<div class='error'>無效的 JSON: {flex_content}</div>"
            
            # 檢查是否為完整的 Flex Message 格式
            if "type" in flex_content and flex_content["type"] == "flex":
                # 使用 contents 物件渲染
                return self._render_flex_message(flex_content)
            elif "contents" in flex_content:
                # 直接使用 contents 物件渲染
                return self._render_container(flex_content["contents"])
            elif "type" in flex_content and flex_content["type"] in ["bubble", "carousel"]:
                # 直接渲染容器
                return self._render_container(flex_content)
            else:
                # 不符合 Flex Message 格式
                return f"<div class='error'>不支援的訊息格式: {json.dumps(flex_content, ensure_ascii=False, indent=2)}</div>"
                
        except Exception as e:
            logger.error(f"渲染 Flex Message 時出錯: {str(e)}")
            return f"<div class='error'>渲染錯誤: {str(e)}</div>"
    
    def _render_flex_message(self, flex_message):
        """渲染完整的 Flex Message 格式"""
        # 添加基本樣式
        html = f"""
        <div class="line-flex-message">
            <div class="flex-message-header">
                <div class="flex-message-alt">{flex_message.get('altText', 'Flex Message')}</div>
            </div>
            <div class="flex-message-body">
                {self._render_container(flex_message["contents"])}
            </div>
        </div>
        <style>
            {self.css}
        </style>
        """
        return html
    
    def _render_container(self, container):
        """渲染容器 (bubble 或 carousel)"""
        container_type = container.get("type", "").lower()
        
        if container_type == "bubble":
            return self._render_bubble(container)
        elif container_type == "carousel":
            return self._render_carousel(container)
        else:
            return f"<div class='error'>不支援的容器類型: {container_type}</div>"
    
    def _render_bubble(self, bubble):
        """渲染 Bubble 容器"""
        # 設置 Bubble 樣式
        styles = bubble.get("styles", {})
        bubble_style = self._get_bubble_styles(styles)
        
        # 渲染各部分
        header_html = ""
        hero_html = ""
        body_html = ""
        footer_html = ""
        
        if "header" in bubble:
            header_html = self._render_box(bubble["header"], is_header=True)
        
        if "hero" in bubble:
            hero_html = self._render_hero(bubble["hero"])
        
        if "body" in bubble:
            body_html = self._render_box(bubble["body"])
        
        if "footer" in bubble:
            footer_html = self._render_box(bubble["footer"], is_footer=True)
        
        # 組合成完整的 Bubble
        html = f"""
        <div class="line-bubble" style="{bubble_style}">
            {header_html}
            {hero_html}
            {body_html}
            {footer_html}
        </div>
        """
        return html
    
    def _render_carousel(self, carousel):
        """渲染 Carousel 容器"""
        contents = carousel.get("contents", [])
        
        if not contents:
            return "<div class='error'>Carousel 沒有內容</div>"
        
        bubbles_html = []
        for bubble in contents:
            if bubble.get("type", "").lower() == "bubble":
                bubbles_html.append(self._render_bubble(bubble))
            else:
                bubbles_html.append(f"<div class='error'>Carousel 中的非 Bubble 元素: {bubble.get('type')}</div>")
        
        # 組合成完整的 Carousel
        html = f"""
        <div class="line-carousel">
            {''.join(bubbles_html)}
            <div class="carousel-indicators">
                {self._render_carousel_indicators(len(contents))}
            </div>
        </div>
        """
        return html
    
    def _render_carousel_indicators(self, count):
        """渲染 Carousel 指示器"""
        indicators = []
        for i in range(count):
            active = " active" if i == 0 else ""
            indicators.append(f'<div class="carousel-indicator{active}" data-index="{i}"></div>')
        
        return ''.join(indicators)
    
    def _render_hero(self, hero):
        """渲染 Hero 區塊"""
        if hero.get("type", "").lower() != "image":
            return f"<div class='error'>Hero 必須是 image 類型，不支援: {hero.get('type')}</div>"
        
        image_url = hero.get("url", "")
        if not image_url:
            return "<div class='error'>Hero image 缺少 URL</div>"
        
        # 設置圖片樣式
        size = hero.get("size", "full")
        aspect_ratio = hero.get("aspectRatio", "20:13")
        aspect_mode = hero.get("aspectMode", "cover")
        
        style = f"""
            width: 100%;
            background-image: url('{image_url}');
            background-size: {aspect_mode};
            background-position: center;
            background-repeat: no-repeat;
        """
        
        # 解析寬高比
        if ":" in aspect_ratio:
            w, h = aspect_ratio.split(":")
            try:
                ratio = float(h) / float(w) * 100
                style += f"padding-top: {ratio}%;"
            except:
                style += "padding-top: 65%;"  # 預設 20:13 的比例
        else:
            style += "padding-top: 65%;"  # 預設比例
        
        # 添加點擊事件
        action = hero.get("action", {})
        action_html = self._get_action_attributes(action)
        
        html = f"""
        <div class="line-hero" style="{style}" {action_html}>
        </div>
        """
        return html
    
    def _render_box(self, box, is_header=False, is_footer=False):
        """渲染 Box 元素"""
        if box.get("type", "").lower() != "box":
            return f"<div class='error'>預期是 Box 類型，但收到: {box.get('type')}</div>"
        
        layout = box.get("layout", "vertical").lower()
        padding = box.get("padding", "lg" if not is_footer else "xs")
        spacing = box.get("spacing", "md")
        margin = box.get("margin", "none")
        background_color = box.get("backgroundColor", "")
        
        # 設置 Box 樣式
        style = f"""
            padding: {self._get_spacing_value(padding)};
            background-color: {background_color};
            margin: {self._get_spacing_value(margin)};
        """
        
        # 添加特定部分的類別
        section_class = ""
        if is_header:
            section_class = " line-header"
        elif is_footer:
            section_class = " line-footer"
        
        # 渲染內容
        contents_html = []
        for content in box.get("contents", []):
            content_html = self._render_content(content)
            contents_html.append(f"""
                <div class="line-box-item" style="margin-bottom: {self._get_spacing_value(spacing)};">
                    {content_html}
                </div>
            """)
        
        layout_class = f"line-box-{layout}"
        
        html = f"""
        <div class="line-box {layout_class}{section_class}" style="{style}">
            {''.join(contents_html)}
        </div>
        """
        return html
    
    def _render_content(self, content):
        """渲染內容元素"""
        content_type = content.get("type", "").lower()
        
        if content_type == "text":
            return self._render_text(content)
        elif content_type == "image":
            return self._render_image(content)
        elif content_type == "button":
            return self._render_button(content)
        elif content_type == "separator":
            return self._render_separator(content)
        elif content_type == "box":
            return self._render_box(content)
        elif content_type == "icon":
            return self._render_icon(content)
        elif content_type == "spacer":
            return self._render_spacer(content)
        else:
            return f"<div class='error'>不支援的內容類型: {content_type}</div>"
    
    def _render_text(self, text):
        """渲染文字元素"""
        content = text.get("text", "")
        size = text.get("size", "md").lower()
        weight = text.get("weight", "regular").lower()
        color = text.get("color", "#000000")
        align = text.get("align", "left").lower()
        wrap = text.get("wrap", True)
        maxLines = text.get("maxLines", 0)
        decoration = text.get("decoration", "none").lower()
        
        style = f"""
            color: {color};
            text-align: {align};
            font-weight: {self._get_font_weight(weight)};
            text-decoration: {decoration};
        """
        
        style += f"font-size: {self._get_font_size(size)};"
        
        if not wrap:
            style += """
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            """
        elif maxLines > 0:
            style += f"""
                display: -webkit-box;
                -webkit-line-clamp: {maxLines};
                -webkit-box-orient: vertical;
                overflow: hidden;
            """
        
        # 添加點擊事件
        action = text.get("action", {})
        action_html = self._get_action_attributes(action)
        
        html = f"""
        <div class="line-text line-text-{size}" style="{style}" {action_html}>
            {content}
        </div>
        """
        return html
    
    def _render_image(self, image):
        """渲染圖片元素"""
        image_url = image.get("url", "")
        if not image_url:
            return "<div class='error'>圖片缺少 URL</div>"
        
        size = image.get("size", "md").lower()
        aspect_ratio = image.get("aspectRatio", "1:1")
        aspect_mode = image.get("aspectMode", "fit").lower()
        
        # 設置圖片尺寸
        width = self._get_image_width(size)
        
        # 解析寬高比
        if ":" in aspect_ratio:
            w, h = aspect_ratio.split(":")
            try:
                ratio = float(h) / float(w) * 100
            except:
                ratio = 100  # 預設 1:1 的比例
        else:
            ratio = 100  # 預設比例
        
        # 設置圖片樣式
        img_style = f"""
            width: 100%;
            height: 100%;
            object-fit: {aspect_mode};
        """
        
        container_style = f"""
            width: {width};
            padding-top: {ratio}%;
            position: relative;
            overflow: hidden;
            margin: 0 auto;
        """
        
        # 添加點擊事件
        action = image.get("action", {})
        action_html = self._get_action_attributes(action)
        
        html = f"""
        <div class="line-image-container" style="{container_style}" {action_html}>
            <img src="{image_url}" class="line-image line-image-{size}" style="{img_style}">
        </div>
        """
        return html
    
    def _render_button(self, button):
        """渲染按鈕元素"""
        # 渲染按鈕樣式
        style = button.get("style", "primary").lower()
        color = button.get("color", "#00B900" if style == "primary" else "#FFFFFF")
        height = button.get("height", "md").lower()
        
        # 按鈕文字
        title = ""
        if "title" in button:
            title = button["title"]
        elif "action" in button and "label" in button["action"]:
            title = button["action"]["label"]
        
        # 設置按鈕樣式
        btn_style = f"""
            background-color: {color if style == 'primary' else '#FFFFFF'};
            color: {color if style != 'primary' else '#FFFFFF'};
            border: 1px solid {color};
            height: {self._get_button_height(height)};
        """
        
        if style == "link":
            btn_style += """
                background-color: transparent;
                border: none;
                color: #0000FF;
                text-decoration: underline;
            """
        
        # 添加點擊事件
        action = button.get("action", {})
        action_html = self._get_action_attributes(action)
        
        html = f"""
        <button class="line-button line-button-{style} line-button-{height}" style="{btn_style}" {action_html}>
            {title}
        </button>
        """
        return html
    
    def _render_separator(self, separator):
        """渲染分隔線元素"""
        color = separator.get("color", "#EEEEEE")
        margin = separator.get("margin", "md")
        
        style = f"""
            border-top: 1px solid {color};
            margin: {self._get_spacing_value(margin)} 0;
        """
        
        html = f"""
        <div class="line-separator" style="{style}"></div>
        """
        return html
    
    def _render_icon(self, icon):
        """渲染圖標元素"""
        url = icon.get("url", "")
        if not url:
            return "<div class='error'>圖標缺少 URL</div>"
        
        size = icon.get("size", "md").lower()
        
        # 設置圖標尺寸
        width = self._get_icon_size(size)
        
        html = f"""
        <div class="line-icon" style="display: inline-block; vertical-align: middle;">
            <img src="{url}" style="width: {width}; height: auto;" alt="icon">
        </div>
        """
        return html
    
    def _render_spacer(self, spacer):
        """渲染間隔元素"""
        size = spacer.get("size", "md").lower()
        
        # 設置間隔尺寸
        height = self._get_spacing_value(size)
        
        html = f"""
        <div class="line-spacer" style="height: {height};"></div>
        """
        return html
    
    def _get_bubble_styles(self, styles):
        """獲取 Bubble 的樣式"""
        style = ""
        
        if "header" in styles:
            if "backgroundColor" in styles["header"]:
                style += f"--header-bg-color: {styles['header']['backgroundColor']};"
        
        if "hero" in styles:
            if "backgroundColor" in styles["hero"]:
                style += f"--hero-bg-color: {styles['hero']['backgroundColor']};"
        
        if "body" in styles:
            if "backgroundColor" in styles["body"]:
                style += f"--body-bg-color: {styles['body']['backgroundColor']};"
        
        if "footer" in styles:
            if "backgroundColor" in styles["footer"]:
                style += f"--footer-bg-color: {styles['footer']['backgroundColor']};"
        
        return style
    
    def _get_action_attributes(self, action):
        """獲取點擊事件的屬性"""
        if not action:
            return ""
        
        action_type = action.get("type", "").lower()
        data = json.dumps(action, ensure_ascii=False).replace('"', "&quot;")
        
        return f'data-action="{action_type}" data-action-data="{data}"'
    
    def _get_font_size(self, size):
        """獲取文字大小"""
        sizes = {
            "xxs": "11px",
            "xs": "12px",
            "sm": "13px",
            "md": "14px",
            "lg": "16px",
            "xl": "18px",
            "xxl": "20px",
            "3xl": "24px",
            "4xl": "28px",
            "5xl": "32px"
        }
        return sizes.get(size.lower(), "14px")
    
    def _get_font_weight(self, weight):
        """獲取文字粗細"""
        weights = {
            "regular": "400",
            "bold": "700"
        }
        return weights.get(weight.lower(), "400")
    
    def _get_spacing_value(self, spacing):
        """獲取間距值"""
        spacings = {
            "none": "0",
            "xs": "4px",
            "sm": "8px",
            "md": "12px",
            "lg": "16px",
            "xl": "20px",
            "xxl": "24px"
        }
        return spacings.get(str(spacing).lower(), "12px")
    
    def _get_image_width(self, size):
        """獲取圖片寬度"""
        sizes = {
            "xxs": "20px",
            "xs": "40px",
            "sm": "80px",
            "md": "120px",
            "lg": "200px",
            "xl": "300px",
            "xxl": "400px",
            "3xl": "500px",
            "4xl": "600px",
            "5xl": "700px",
            "full": "100%"
        }
        return sizes.get(size.lower(), "120px")
    
    def _get_button_height(self, height):
        """獲取按鈕高度"""
        heights = {
            "sm": "30px",
            "md": "40px",
            "lg": "50px"
        }
        return heights.get(height.lower(), "40px")
    
    def _get_icon_size(self, size):
        """獲取圖標大小"""
        sizes = {
            "xxs": "12px",
            "xs": "16px",
            "sm": "20px",
            "md": "24px",
            "lg": "32px",
            "xl": "40px",
            "xxl": "48px"
        }
        return sizes.get(size.lower(), "24px")
    
    def _load_css(self):
        """載入 Flex Message 的 CSS 樣式"""
        css = """
            .line-flex-message {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                width: 100%;
                max-width: 450px;
                border-radius: 8px;
                overflow: hidden;
                margin: 10px auto;
                box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
            }
            
            .flex-message-header {
                background-color: #00B900;
                color: white;
                padding: 6px 12px;
                font-size: 12px;
            }
            
            .flex-message-body {
                background-color: #FFFFFF;
            }
            
            .line-bubble {
                border-radius: 8px;
                overflow: hidden;
                background-color: #FFFFFF;
                --header-bg-color: #FFFFFF;
                --hero-bg-color: #FFFFFF;
                --body-bg-color: #FFFFFF;
                --footer-bg-color: #FFFFFF;
            }
            
            .line-carousel {
                display: flex;
                overflow-x: auto;
                scroll-snap-type: x mandatory;
                width: 100%;
                -webkit-overflow-scrolling: touch;
            }
            
            .line-carousel .line-bubble {
                flex: 0 0 auto;
                width: 80%;
                margin-right: 10px;
                scroll-snap-align: start;
            }
            
            .carousel-indicators {
                display: flex;
                justify-content: center;
                padding: 10px 0;
            }
            
            .carousel-indicator {
                width: 8px;
                height: 8px;
                background-color: #DDDDDD;
                border-radius: 50%;
                margin: 0 4px;
            }
            
            .carousel-indicator.active {
                background-color: #00B900;
            }
            
            .line-header {
                background-color: var(--header-bg-color);
            }
            
            .line-hero {
                background-color: var(--hero-bg-color);
            }
            
            .line-box {
                background-color: var(--body-bg-color);
            }
            
            .line-footer {
                background-color: var(--footer-bg-color);
            }
            
            .line-box-horizontal {
                display: flex;
                flex-direction: row;
                flex-wrap: nowrap;
                align-items: center;
            }
            
            .line-box-vertical {
                display: flex;
                flex-direction: column;
            }
            
            .line-box-item {
                flex: 0 0 auto;
            }
            
            .line-text {
                word-break: break-word;
            }
            
            .line-image-container {
                position: relative;
                overflow: hidden;
            }
            
            .line-image {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
            }
            
            .line-button {
                display: block;
                width: 100%;
                border-radius: 4px;
                font-size: 14px;
                font-weight: 700;
                line-height: 1;
                text-align: center;
                text-decoration: none;
                cursor: pointer;
                transition: opacity 0.2s;
            }
            
            .line-button:hover {
                opacity: 0.8;
            }
            
            .error {
                color: red;
                padding: 10px;
                background-color: #FFEEEE;
                border: 1px solid #FFAAAA;
                border-radius: 4px;
            }
        """
        return css 
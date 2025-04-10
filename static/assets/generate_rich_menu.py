#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
富選單圖片生成工具
"""

from PIL import Image, ImageDraw, ImageFont
import os

# 圖像尺寸 (LINE 富選單標準尺寸)
WIDTH = 2500
HEIGHT = 1686

# 確保資源目錄存在
os.makedirs('static/assets', exist_ok=True)

# 創建圖像
img = Image.new('RGBA', (WIDTH, HEIGHT), color=(255, 255, 255, 255))
draw = ImageDraw.Draw(img)

# 設定背景顏色
draw.rectangle([(0, 0), (WIDTH, HEIGHT)], fill=(255, 255, 255, 255))

# 定義選單按鈕
buttons = [
    # 第一行
    {"text": "支出記帳", "icon": "💰", "x": WIDTH//4, "y": HEIGHT//4, "color": (144, 238, 144, 255)},
    {"text": "收入記帳", "icon": "💵", "x": WIDTH*3//4, "y": HEIGHT//4, "color": (173, 216, 230, 255)},
    
    # 第二行
    {"text": "設置提醒", "icon": "⏰", "x": WIDTH//4, "y": HEIGHT*2//4, "color": (255, 218, 185, 255)},
    {"text": "常用帳戶", "icon": "💼", "x": WIDTH*3//4, "y": HEIGHT*2//4, "color": (221, 160, 221, 255)},
    
    # 第三行
    {"text": "查詢記錄", "icon": "📊", "x": WIDTH//4, "y": HEIGHT*3//4, "color": (255, 182, 193, 255)},
    {"text": "更多功能", "icon": "⚙️", "x": WIDTH*3//4, "y": HEIGHT*3//4, "color": (176, 196, 222, 255)},
]

# 繪製網格線
for i in range(1, 3):
    # 水平線
    draw.line([(0, HEIGHT*i//3), (WIDTH, HEIGHT*i//3)], fill=(200, 200, 200, 255), width=3)
    # 垂直線
    draw.line([(WIDTH//2, 0), (WIDTH//2, HEIGHT)], fill=(200, 200, 200, 255), width=3)

# 嘗試加載字體，若失敗則使用默認字體
try:
    font_large = ImageFont.truetype("Arial Unicode.ttf", 80)
    font_small = ImageFont.truetype("Arial Unicode.ttf", 60)
except IOError:
    font_large = ImageFont.load_default()
    font_small = ImageFont.load_default()

# 繪製按鈕
for button in buttons:
    # 繪製按鈕背景
    btn_width, btn_height = WIDTH//3, HEIGHT//4
    x1 = button["x"] - btn_width//2
    y1 = button["y"] - btn_height//2
    x2 = button["x"] + btn_width//2
    y2 = button["y"] + btn_height//2
    
    # 圓角矩形 (模擬)
    draw.rectangle([(x1, y1), (x2, y2)], fill=button["color"], outline=(100, 100, 100, 255), width=2)
    
    # 繪製圖示
    icon_text = button["icon"]
    icon_width = draw.textlength(icon_text, font=font_large)
    draw.text((button["x"] - icon_width//2, button["y"] - 80), icon_text, fill=(0, 0, 0, 255), font=font_large)
    
    # 繪製文字
    text_width = draw.textlength(button["text"], font=font_small)
    draw.text((button["x"] - text_width//2, button["y"] + 20), button["text"], fill=(0, 0, 0, 255), font=font_small)

# 保存圖片
img.save("static/assets/rich_menu.png")

print("富選單圖片已生成：static/assets/rich_menu.png") 
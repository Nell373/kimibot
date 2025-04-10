#!/usr/bin/env python3
"""
生成Rich Menu圖片，使用Selenium和Chrome驅動將HTML頁面轉換為圖片。
需要安裝以下依賴：
    pip install selenium Pillow webdriver-manager
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image

def generate_rich_menu_image(html_path, output_path):
    """
    將HTML頁面轉換為圖片
    
    Args:
        html_path: HTML文件的路徑
        output_path: 輸出圖片的路徑
    """
    # 獲取當前工作目錄
    current_dir = os.getcwd()
    
    # HTML文件的完整路徑
    html_url = f"file://{current_dir}/{html_path}"
    
    # 配置Chrome選項
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 無頭模式
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=2500,1686")  # 設置窗口大小與Rich Menu尺寸相同
    chrome_options.add_argument("--hide-scrollbars")
    
    # 啟動Chrome瀏覽器
    print("啟動Chrome瀏覽器...")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        # 加載HTML頁面
        print(f"加載HTML頁面: {html_url}")
        driver.get(html_url)
        
        # 等待頁面渲染完成
        time.sleep(2)
        
        # 獲取指定元素的截圖
        print("正在截圖...")
        element = driver.find_element("id", "rich-menu")
        
        # 截取元素的截圖
        element.screenshot(output_path)
        
        print(f"Rich Menu圖片已生成: {output_path}")
        
        # 打開並顯示圖片尺寸
        img = Image.open(output_path)
        print(f"圖片尺寸: {img.size[0]}x{img.size[1]}")
        
    finally:
        # 關閉瀏覽器
        driver.quit()
        print("瀏覽器已關閉")

if __name__ == "__main__":
    # 設置HTML文件路徑和輸出圖片路徑
    html_path = "static/assets/rich_menu.html"
    output_path = "static/assets/rich_menu.png"
    
    # 生成Rich Menu圖片
    generate_rich_menu_image(html_path, output_path) 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from PIL import Image
from io import BytesIO

def html_to_image(html_path, output_path, width=2500, height=1686):
    """將HTML文件轉換為PNG圖像

    Args:
        html_path (str): HTML文件的路徑
        output_path (str): 輸出PNG圖像的路徑
        width (int, optional): 圖像寬度. 預設為2500.
        height (int, optional): 圖像高度. 預設為1686.
    """
    print(f"正在將 {html_path} 轉換為圖像...")
    
    # 確保輸出目錄存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 設置Chrome選項
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"--window-size={width},{height}")
    
    try:
        # 初始化瀏覽器
        driver = webdriver.Chrome(options=chrome_options)
        
        # 載入HTML文件
        html_path = os.path.abspath(html_path)
        driver.get(f"file://{html_path}")
        
        # 等待頁面渲染完成
        time.sleep(2)
        
        # 獲取屏幕截圖
        screenshot = driver.get_screenshot_as_png()
        
        # 保存為PNG
        img = Image.open(BytesIO(screenshot))
        img.save(output_path)
        
        print(f"圖像已保存到 {output_path}")
    except Exception as e:
        print(f"轉換過程中發生錯誤: {e}")
    finally:
        # 關閉瀏覽器
        if 'driver' in locals():
            driver.quit()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python html_to_image.py <html路徑> <輸出路徑> [寬度] [高度]")
        sys.exit(1)
        
    html_path = sys.argv[1]
    output_path = sys.argv[2]
    
    width = int(sys.argv[3]) if len(sys.argv) > 3 else 2500
    height = int(sys.argv[4]) if len(sys.argv) > 4 else 1686
    
    html_to_image(html_path, output_path, width, height) 
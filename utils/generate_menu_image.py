#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_rich_menu_image(template_path, output_path, width=2500, height=1686):
    """
    使用Selenium和Chrome瀏覽器將HTML模板轉換為圖像
    
    Args:
        template_path: HTML模板的路徑
        output_path: 輸出圖像的路徑
        width: 圖像寬度，預設為2500px (LINE標準)
        height: 圖像高度，預設為1686px (LINE標準)
    
    Returns:
        bool: 是否成功生成圖像
    """
    try:
        # 檢查目錄是否存在，不存在則創建
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logger.info(f"創建目錄: {output_dir}")
        
        # 獲取HTML模板的絕對路徑
        absolute_template_path = os.path.abspath(template_path)
        if not os.path.exists(absolute_template_path):
            logger.error(f"HTML模板不存在: {absolute_template_path}")
            return False
        
        # 設置Chrome選項
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 無頭模式
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(f"--window-size={width},{height}")
        
        # 初始化WebDriver
        logger.info("初始化WebDriver...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 載入HTML文件
        logger.info(f"載入HTML模板: {absolute_template_path}")
        driver.get(f"file://{absolute_template_path}")
        
        # 等待頁面加載
        time.sleep(2)
        
        # 截圖
        logger.info(f"截取圖像並保存到: {output_path}")
        driver.save_screenshot(output_path)
        
        # 關閉WebDriver
        driver.quit()
        
        # 使用PIL優化圖像
        img = Image.open(output_path)
        img = img.resize((width, height), Image.LANCZOS)
        img.save(output_path, optimize=True, quality=90)
        
        logger.info(f"成功生成並優化圖像: {output_path}")
        return True
    
    except Exception as e:
        logger.error(f"生成圖像時發生錯誤: {str(e)}")
        return False

def main():
    """主函數，用於測試生成圖像功能"""
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_path = os.path.join(current_dir, "static", "assets", "quick_menu_template.html")
    output_path = os.path.join(current_dir, "static", "assets", "quick_menu.png")
    
    logger.info("開始生成LINE快速選單圖像...")
    success = generate_rich_menu_image(template_path, output_path)
    
    if success:
        logger.info(f"圖像生成成功: {output_path}")
    else:
        logger.error("圖像生成失敗")

if __name__ == "__main__":
    main() 
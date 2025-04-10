#!/usr/bin/env python
import sys
import os
import logging
import unittest

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 將項目根目錄添加到系統路徑中
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_tests():
    """運行所有測試"""
    logger.info("開始運行測試...")
    
    # 發現並加載所有測試用例
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(
        start_dir=os.path.dirname(os.path.abspath(__file__)),
        pattern='test_*.py'
    )
    
    # 運行測試套件
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # 顯示測試結果
    logger.info(f"測試完成！")
    logger.info(f"運行測試總數: {result.testsRun}")
    logger.info(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    logger.info(f"失敗: {len(result.failures)}")
    logger.info(f"錯誤: {len(result.errors)}")
    
    # 返回測試結果（用於自動化流程）
    return len(result.failures) == 0 and len(result.errors) == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1) 
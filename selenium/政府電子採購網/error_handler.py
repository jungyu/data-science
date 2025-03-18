import logging
import time
import random
from datetime import datetime
from functools import wraps
from selenium.common.exceptions import WebDriverException

logger = logging.getLogger(__name__)

def retry_on_exception(max_retries=3, retry_delay=(5, 10)):
    """重試裝飾器，處理例外情況"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retry_count = 0
            while retry_count < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retry_count += 1
                    logger.error(f"第 {retry_count} 次嘗試失敗: {e}")
                    if retry_count >= max_retries:
                        logger.error("已達到最大重試次數，程式終止")
                        raise
                    delay = random.uniform(*retry_delay)
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

def handle_browser_error(driver, error):
    """處理瀏覽器相關錯誤"""
    try:
        if driver:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = f"error_{timestamp}.png"
            driver.save_screenshot(screenshot_path)
            logger.error(f"錯誤截圖已保存至: {screenshot_path}")
    except Exception as e:
        logger.error(f"保存錯誤截圖時發生錯誤: {e}")

def handle_selenium_error(error):
    """處理 Selenium 相關錯誤"""
    if isinstance(error, WebDriverException):
        logger.error(f"Selenium 錯誤: {error}")
    else:
        logger.error(f"未預期的錯誤: {error}")

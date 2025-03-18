import os
import pickle
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

def get_cookie_filename(url):
    """基於 URL 自動生成 cookie 檔案名稱"""
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.replace("www.", "")

    # 為每個域名創建獨立的 cookie 檔案
    cookie_dir = "cookies"
    os.makedirs(cookie_dir, exist_ok=True)

    return os.path.join(cookie_dir, f"{domain}_cookies.pkl")

def save_cookies(driver, filename=None):
    """儲存 Cookie 到檔案，如果未提供檔名則自動生成"""
    try:
        if not filename:
            current_url = driver.current_url
            filename = get_cookie_filename(current_url)

        cookies = driver.get_cookies()
        
        # 檢查檔案是否存在，如果存在則讀取現有 Cookie
        if os.path.exists(filename):
            with open(filename, "rb") as f:
                existing_cookies = pickle.load(f)
            # 合併現有 Cookie 和新的 Cookie，以避免覆蓋
            # 注意：這裡簡單地將新的 Cookie 加入到現有的 Cookie 列表中 
            # 您可能需要更複雜的邏輯來處理重複的 Cookie
            cookies = existing_cookies + cookies  

        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "wb") as f:
            pickle.dump(cookies, f)
        logger.info(f"Cookie 已儲存至 {filename}")
        return True, filename
    except Exception as e:
        logger.error(f"儲存 Cookie 失敗: {e}")
        return False, None

def load_cookies(driver, url, filename=None):
    """從檔案載入 Cookie"""
    try:
        if not filename:
            filename = get_cookie_filename(url)

        if not os.path.exists(filename):
            logger.warning(f"Cookie 檔案 {filename} 不存在，將在訪問後建立")
            return False, filename

        # 先訪問目標域名，再設置 Cookie
        driver.get(url)

        with open(filename, "rb") as f:
            cookies = pickle.load(f)

        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except Exception as cookie_error:
                logger.warning(f"新增 Cookie 失敗: {cookie_error}")

        logger.info(f"Cookie 已從 {filename} 載入")
        return True, filename
    except Exception as e:
        logger.error(f"載入 Cookie 失敗: {e}")
        return False, filename

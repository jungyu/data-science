#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
政府電子採購網爬蟲程式

此程式用於爬取政府電子採購網的公開資訊，
使用 Selenium 進行網頁自動化操作。

Created by: Aaron Yu
Repository: https://github.com/aaronyu/Data-Science
Email: jungyuyu@gmail.com
Created Date: 2025-3-1
Last Modified: 2025-3-18

Copyright (c) 2023-2025 Aaron Yu
All rights reserved.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.
"""

import os
import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import undetected_chromedriver as uc
from fake_useragent import UserAgent
from datetime import datetime
import json
from procurement_crawler import ProcurementCrawler  # 引入 ProcurementCrawler 類別
from cookie_manager import load_cookies, save_cookies # 引入 Cookie 管理器
from error_handler import retry_on_exception, handle_browser_error, handle_selenium_error

# 確保 logs 目錄存在
os.makedirs('logs', exist_ok=True)

# 設定日誌記錄
current_date = datetime.now().strftime('%Y-%m-%d')
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler(f"logs/crawler_{current_date}.log"),
                              logging.StreamHandler()])
logger = logging.getLogger(__name__)

def get_driver(use_proxy=False, user_agent=None, headless=True):
    """配置並獲取 Chrome WebDriver"""
    options = webdriver.ChromeOptions()

    # 基本設定
    if headless:
        options.add_argument('--headless')

    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-notifications')
    options.add_argument('--disable-popup-blocking')
    options.add_argument('--ignore-certificate-errors')  # 忽略 SSL 認證錯誤
    options.add_argument('--ignore-ssl-errors')  # 忽略 SSL 認證錯誤
    if user_agent:
        options.add_argument(f'--user-agent={user_agent}')
    else:
        ua = UserAgent()
        options.add_argument(f'--user-agent={ua.random}')

    # 使用代理伺服器 (如果需要)
    if use_proxy:
        proxy = "YOUR_PROXY_ADDRESS"  # 替換為您的代理伺服器地址
        options.add_argument(f'--proxy-server={proxy}')

    # 其他反檢測設定
    options.add_argument('--disable-blink-features=AutomationControlled')
    # options.add_experimental_option("excludeSwitches", ["enable-automation"])
    # options.add_experimental_option('useAutomationExtension', False)

    try:
        driver = uc.Chrome(options=options)
        # 執行 JavaScript 隱藏 WebDriver
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        logger.info("WebDriver 已成功啟動")
        return driver
    except Exception as e:
        logger.error(f"WebDriver 啟動失敗: {e}")
        raise

def wait_for_element(driver, locator, by=By.XPATH, timeout=20, condition="presence", retries=3):
    """等待元素出現/可點擊/可見，增加重試機制"""
    for attempt in range(retries):
        try:
            wait = WebDriverWait(driver, timeout)
            if condition == "clickable":
                element = wait.until(EC.element_to_be_clickable((by, locator)))
            elif condition == "visible":
                element = wait.until(EC.visibility_of_element_located((by, locator)))
            else:  # 預設為 presence
                element = wait.until(EC.presence_of_element_located((by, locator)))
            return element
        except TimeoutException:
            logger.warning(f"等待元素 {locator} 超時 (嘗試 {attempt + 1}/{retries})")
            if attempt == retries - 1:
                return None
            # 重試前重新整理頁面
            try:
                driver.refresh()
                random_sleep(2, 4)
            except Exception as e:
                logger.error(f"重新整理頁面時發生錯誤: {e}")
            finally:
                pass  # 可以在這裡添加任何需要的清理代碼
        except Exception as e:
            logger.error(f"等待元素時發生錯誤: {e}")
            return None

def random_sleep(min_sec=1, max_sec=3):
    """隨機等待一段時間，模擬人類行為"""
    sleep_time = random.uniform(min_sec, max_sec)
    time.sleep(sleep_time)
    return sleep_time

def handle_login(driver, cookie_file):
    """處理登入頁面的邏輯"""
    try:
        logger.info("需要登入，執行登入流程")
        # 使用 XPath 定位登入元素
        # username_input = wait_for_element(driver, "//input[@id='username' or @name='username']")
        # if username_input:
        #     username_input.send_keys("your_username")
        # password_input = wait_for_element(driver, "//input[@id='password' or @name='password']")
        # if password_input:
        #     password_input.send_keys("your_password")
        # login_button = wait_for_element(driver, "//button[contains(@class, 'login') or contains(text(), '登入')]", condition="clickable")
        # if login_button:
        #     login_button.click()

        # 登入後保存 Cookie
        random_sleep(3, 5)
        success, new_cookie_file = save_cookies(driver, cookie_file)
        
        if success:
            logger.info("登入成功並保存了新的 Cookie")
            return True, new_cookie_file
        else:
            logger.error("登入後保存 Cookie 失敗")
            return False, cookie_file
            
    except Exception as e:
        logger.error(f"登入過程發生錯誤: {e}")
        return False, cookie_file

def load_config_and_build_url():
    """從設定檔讀取配置並組合目標 URL"""
    try:
        # 從 config.json 讀取配置
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)

        base_url = config['base_url']
        query_params = config['query_params']

        # 組合 URL
        target_url = base_url + '?'
        params = []
        for key, value in query_params.items():
            params.append(f"{key}={value}")
        target_url += '&'.join(params)

        logger.info(f"成功讀取設定檔並組合 URL: {target_url}")
        return True, target_url

    except FileNotFoundError:
        logger.error("找不到 config.json 設定檔")
        return False, None
    except json.JSONDecodeError:
        logger.error("config.json 格式錯誤")
        return False, None
    except KeyError as e:
        logger.error(f"設定檔缺少必要的配置項: {e}")
        return False, None
    except Exception as e:
        logger.error(f"讀取設定檔時發生錯誤: {e}")
        return False, None

def crawl_data(crawler, all_items=None):
    """爬取數據的核心邏輯"""
    if all_items is None:
        all_items = []
    
    items = crawler.extract_data()
    if not items:
        logger.warning("當前頁面未找到任何數據")
        return all_items
    
    all_items.extend(items)
    logger.info(f"當前頁面成功爬取 {len(items)} 條資料")
    return all_items

def save_data(data, filename='procurement_data.json', timestamp=True):
    """保存數據到 JSON 文件"""
    try:
        if not data:
            logger.error("沒有數據可供保存")
            return False
            
        if timestamp:
            base, ext = os.path.splitext(filename)
            filename = f"{base}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
            
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"數據已成功保存至: {filename}")
        return True
    except Exception as e:
        logger.error(f"保存數據時發生錯誤: {e}")
        return False

def main():
    driver = None
    try:
        # 讀取設定並組合 URL
        success, target_url = load_config_and_build_url()
        if not success:
            logger.error("無法取得目標 URL，程式終止")
            return

        driver = get_driver(headless=True)
        driver.set_page_load_timeout(30)
        
        # 載入 Cookie 並訪問目標網站
        cookie_loaded, cookie_file = load_cookies(driver, target_url)
        logger.info(f"正在訪問 {target_url}")
        driver.get(target_url)
        random_sleep(3, 5)

        # 驗證頁面載入狀態
        if not driver.current_url or "error" in driver.current_url.lower() or "404" in driver.current_url:
            raise WebDriverException("頁面載入失敗或無效")

        # 處理登入邏輯
        if not cookie_loaded or "login" in driver.current_url.lower():
            login_success, cookie_file = handle_login(driver, cookie_file)
            if not login_success:
                raise Exception("登入失敗")

        # 初始化爬蟲並開始爬取
        crawler = ProcurementCrawler(driver)
        all_items = []
        page_count = 0

        # 爬取第一頁
        all_items = crawl_data(crawler)
        page_count += 1

        # 爬取後續頁面
        while True:
            next_page_link = crawler.get_next_page_link()
            if not next_page_link:
                break

            logger.info(f"正在訪問第 {page_count + 1} 頁")
            if not crawler.get_page_with_selenium(next_page_link, driver):
                logger.error("無法獲取下一頁")
                break

            random_sleep(2, 3)
            all_items = crawl_data(crawler, all_items)
            page_count += 1

            if page_count % 5 == 0:  # 每爬取5頁保存一次
                save_data(all_items, filename=f'procurement_data_partial_{page_count}.json')

        logger.info(f"共爬取 {len(all_items)} 條列表資料，來自 {page_count} 頁")

        # 爬取詳情頁
        for i, item in enumerate(all_items, 1):
            detail_link = item.get('detail_link')
            if not detail_link:
                continue

            try:
                logger.info(f"正在處理第 {i}/{len(all_items)} 條記錄的詳情頁")
                detail_page_data = crawler.parse_detail_page(detail_link)
                if detail_page_data:
                    item['detail_data'] = detail_page_data
                    logger.info(f"成功獲取詳情頁資料: {item.get('tender_name', 'Unknown')}")
                
                delay = random_sleep(5, 8)
                logger.debug(f"等待 {delay:.2f} 秒後繼續...")
                
                if i % 10 == 0:  # 每處理10條詳情頁保存一次
                    save_data(all_items, filename=f'procurement_data_with_details_partial_{i}.json')
                    
            except Exception as e:
                logger.error(f"處理詳情頁時發生錯誤 ({detail_link}): {e}")
                continue

        # 最終保存完整數據
        if save_data(all_items):
            logger.info("爬蟲任務完成")
        else:
            logger.error("數據保存失敗")

    except WebDriverException as e:
        handle_selenium_error(e)
        raise
    except Exception as e:
        handle_browser_error(driver, e)
        raise
    finally:
        if driver:
            driver.quit()
            logger.info("WebDriver 已關閉")

if __name__ == "__main__":
    main()
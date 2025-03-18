import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from lxml import etree

logger = logging.getLogger(__name__)

class ProcurementCrawler:
    def __init__(self, driver):
        self.driver = driver
        self.driver.delete_all_cookies()  # 初始化時清除所有 cookie

    def clear_cookies(self):
        """清除瀏覽器所有 cookie"""
        try:
            self.driver.delete_all_cookies()
            logger.info("已清除所有 cookie")
        except Exception as e:
            logger.error(f"清除 cookie 時發生錯誤: {e}")

    def parse_with_xpath(self, html_content):
        """使用 lxml 的 XPath 解析 HTML 內容"""
        try:
            tree = etree.HTML(html_content)
            return tree
        except Exception as e:
            logger.error(f"解析 HTML 失敗: {e}")
            return None

    def extract_elements_by_xpath(self, xpath_expression):
        """使用 XPath 從當前頁面提取元素"""
        try:
            tree = self.parse_with_xpath(self.driver.page_source)
            if tree is None:
                return []

            elements = tree.xpath(xpath_expression)
            return elements
        except Exception as e:
            logger.error(f"XPath 提取元素失敗: {e}")
            return []

    def extract_data(self):
        items = []
        try:
            # 等待表格加載
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//table[@id="tpam"]/tbody/tr'))
            )

            rows = self.driver.find_elements(By.XPATH, '//table[@id="tpam"]/tbody/tr')

            for row in rows:
                try:
                    tender_case_no = row.find_elements(By.XPATH, './td[3]')[0].text.strip() if row.find_elements(By.XPATH, './td[3]') else ''
                    org_name = row.find_elements(By.XPATH, './td[2]')[0].text.strip() if row.find_elements(By.XPATH, './td[2]') else ''

                    tender_name_elem = row.find_elements(By.XPATH, './td[3]/a/span')
                    tender_name = tender_name_elem[0].text.strip() if tender_name_elem else ''

                    tender_type = row.find_elements(By.XPATH, './td[5]')[0].text.strip() if row.find_elements(By.XPATH, './td[5]') else ''
                    announce_date = row.find_elements(By.XPATH, './td[7]')[0].text.strip() if row.find_elements(By.XPATH, './td[7]') else ''
                    tender_deadline = row.find_elements(By.XPATH, './td[8]')[0].text.strip() if row.find_elements(By.XPATH, './td[8]') else ''

                    budget_elem = row.find_elements(By.XPATH, './td[9]/span')
                    budget = budget_elem[0].text.strip() if budget_elem else ''

                    detail_link_elem = row.find_elements(By.XPATH, './td[3]/a')
                    detail_link = detail_link_elem[0].get_attribute('href') if detail_link_elem else ''

                    item = {
                        'tender_case_no': tender_case_no,
                        'org_name': org_name,
                        'tender_name': tender_name,
                        'tender_type': tender_type,
                        'announce_date': announce_date,
                        'tender_deadline': tender_deadline,
                        'budget': budget,
                        'detail_link': detail_link
                    }
                    items.append(item)
                    print(item)
                except Exception as e:
                    print(f"處理行數據時出錯: {str(e)}")
                    continue
        except Exception as e:
            print(f"提取數據時出錯: {str(e)}")

        return items

    def get_next_page_link(self):
        try:
            next_page_elements = self.driver.find_elements(By.XPATH, '//span[@id="pagelinks"]/a[contains(text(), "下一頁")]')
            if next_page_elements:
                return next_page_elements[0].get_attribute('href')
            else:
                return None
        except Exception as e:
            print(f"獲取下一頁鏈接時出錯: {str(e)}")
            return None

    def parse_detail_page(self, url, max_retries=3):
        print(f"正在請求 URL: {url}")
        all_data = {}
        retry_count = 0

        while retry_count < max_retries:
            try:
                # 每次重試前清除 cookie
                self.clear_cookies()
                
                # 使用 Selenium 訪問詳情頁面
                if not self.get_page_with_selenium(url, self.driver):
                    print(f"無法獲取詳情頁面，重試次數：{retry_count + 1}")
                    retry_count += 1
                    continue

                # 增加明確的等待時間
                try:
                    print("等待頁面主要內容載入...")
                    WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located((By.XPATH, '//div[@id="printRange"]'))
                    )
                    # 額外等待確保動態內容完全載入
                    WebDriverWait(self.driver, 10).until(
                        lambda d: len(d.find_elements(By.XPATH, '//div[@id="printRange"]/table')) > 0
                    )
                except Exception as wait_error:
                    print(f"等待頁面載入超時: {str(wait_error)}")
                    retry_count += 1
                    continue

                print("頁面 DOM 獲取成功")

                # 使用 JavaScript 確保頁面完全加載
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # 提取表格並處理
                tables = self.driver.find_elements(By.XPATH, '//div[@id="printRange"]/table')
                if not tables:
                    print("未找到任何表格，可能是頁面結構異常")
                    retry_count += 1
                    continue

                print(f"找到 {len(tables)} 個表格")

                for i, table in enumerate(tables):
                    try:
                        print(f"處理第 {i+1} 個表格")
                        captions = table.find_elements(By.XPATH, './caption')
                        table_name = captions[0].text.strip() if captions else f'unnamed_table_{i}'
                        
                        table_data = {}
                        rows = table.find_elements(By.XPATH, './/tr')
                        
                        for row in rows:
                            try:
                                cols = row.find_elements(By.XPATH, './/td')
                                if len(cols) >= 2:
                                    label = cols[0].text.strip()
                                    value = cols[1].text.strip()
                                    if label:
                                        table_data[label] = value
                            except Exception as row_error:
                                print(f"處理表格行時發生錯誤: {str(row_error)}")
                                continue
                        
                        if table_data:
                            all_data[table_name] = table_data
                    except Exception as table_error:
                        print(f"處理表格時發生錯誤: {str(table_error)}")
                        continue

                if all_data:
                    print(f"成功解析頁面，包含 {len(all_data)} 個表格")
                    return all_data
                
                retry_count += 1
                
            except Exception as e:
                print(f"解析詳情頁面時發生錯誤: {str(e)}")
                retry_count += 1
                if retry_count < max_retries:
                    print(f"將在 3 秒後重試... ({retry_count + 1}/{max_retries})")
                    import time
                    time.sleep(3)
                continue

        print(f"達到最大重試次數 ({max_retries})，返回已收集的數據")
        return all_data

    def get_page_with_selenium(self, url, driver):
        try:
            # 清除現有的 cookie
            self.clear_cookies()
            
            driver.get(url)
            # 增加頁面加載等待時間
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # 印出當前的 cookie 以便偵錯
            cookies = driver.get_cookies()
            logger.info(f"目前的 cookies: {cookies}")
            
            return True
        except Exception as e:
            logger.error(f"請求失敗: {str(e)}")
            return False

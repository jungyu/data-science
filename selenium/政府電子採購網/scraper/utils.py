from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import logging
from .settings import ELEMENT_WAIT_TIMEOUT, ELEMENT_POLL_FREQUENCY, MAX_RETRIES

def wait_for_element(driver, xpath, timeout=ELEMENT_WAIT_TIMEOUT, retries=MAX_RETRIES):
    """
    等待元素出現，如果超時則重試
    """
    for attempt in range(retries):
        try:
            element = WebDriverWait(driver, timeout, ELEMENT_POLL_FREQUENCY).until(
                EC.presence_of_element_located(("xpath", xpath))
            )
            return element
        except TimeoutException:
            if attempt < retries - 1:
                logging.warning(f"等待元素 {xpath} 超時，正在進行第 {attempt + 1} 次重試")
                continue
            else:
                logging.error(f"等待元素 {xpath} 已超過最大重試次數")
                raise

import os
from bot.components.error import Error
from config.bot import USERNAME, PASSWORD
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class Webdriver:
    def __init__(self, timeout):
        self.timeout = timeout

    def startDriver(self):
        print('Starting Google Chrome Webdriver...')
        try:
            chrome_options = Options()
            chrome_exec_shim = os.environ.get(
                "GOOGLE_CHROME_SHIM", "chromedriver")
            chrome_options.binary_location = chrome_exec_shim
            userAgent = "script:reddit bot rescrape method by u/" + USERNAME
            chrome_options.add_argument(f'user-agent={userAgent}')
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--incognito')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-prompt-on-repost')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument('--disable-dev-shm-usage')
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(self.timeout)  # 7 seconds timeout
            driver.get("https://old.reddit.com/login/")
            current_url = driver.current_url
            driver.find_element_by_id("user_login").send_keys(USERNAME)
            driver.find_element_by_id("passwd_login").send_keys(PASSWORD)
            driver.find_element_by_xpath('//button[text()="log in"]').click()
            WebDriverWait(driver, 7).until(EC.url_changes(current_url))
            current_url = driver.current_url
            xpath_val = "//a[text()='" + USERNAME + "']"
            driver.find_element_by_xpath(xpath_val).click()
            WebDriverWait(driver, 5).until(EC.url_changes(current_url))
            Webdriver.refreshWait()
            print("Finished!")
        except Exception as e:
            Error.msg(e)

    def refreshWait(self):
        self.get('https://old.reddit.com/user/' +
                 USERNAME + '/submitted/?sort=new')
        WebDriverWait(self, 5).until(EC.url_changes(self.current_url))

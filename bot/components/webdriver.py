import os
from bot.components.error import Error
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class Webdriver:
    def __init__(self, bot, timeout=7):
        self.timeout = timeout
        self.bot = bot
        self.current_url = None
        self.driver = None
        self.startDriver()

    def startDriver(self):
        print('Starting Google Chrome Webdriver...')
        try:
            chrome_options = Options()
            chrome_exec_shim = os.environ.get(
                "GOOGLE_CHROME_SHIM", "chromedriver")
            chrome_options.binary_location = chrome_exec_shim
            userAgent = "script:reddit bot rescrape method by u/" + self.bot.USERNAME
            chrome_options.add_argument(f'user-agent={userAgent}')
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--incognito')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-prompt-on-repost')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument('--disable-dev-shm-usage')
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(
                self.timeout)  # 7 seconds timeout
            self.driver.get("https://old.reddit.com/login/")
            self.current_url = self.driver.current_url
            self.driver.find_element_by_id(
                "user_login").send_keys(self.bot.USERNAME)
            self.driver.find_element_by_id(
                "passwd_login").send_keys(self.bot.PASSWORD)
            self.driver.find_element_by_xpath(
                '//button[text()="log in"]').click()
            WebDriverWait(self.driver, 7).until(
                EC.url_changes(self.current_url))
            self.current_url = self.driver.current_url
            xpath_val = "//a[text()='" + self.bot.USERNAME + "']"
            self.driver.find_element_by_xpath(xpath_val).click()
            WebDriverWait(self.driver, 5).until(
                EC.url_changes(self.current_url))
            self.refreshWait()
            print("Finished!")
        except Exception as e:
            Error.msg(e)

    def refreshWait(self):
        self.driver.get('https://old.reddit.com/user/' +
                        self.bot.USERNAME + '/submitted/?sort=new')
        WebDriverWait(self.driver, 5).until(EC.url_changes(self.current_url))

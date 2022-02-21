import time
import config.bot as bot
from bot.components.database import Database
from bot.components.webdriver import Webdriver
from bot.components.functions import Functions
from bot.sites.maplestory import MapleStory
from bot.sites.temtem import Temtem


def main():
    print('[!] Initializing Reddit Bot\nBot version: ' + bot.BOT_VERSION +
          ' - Private Sub: ' + bot.PRIVATE_SUB + ' - Log Thread: ' + bot.BOT_LOG_POST)
    Database.connect_to_db()
    bot.Login()
    bot.Session()
    bot.Session.refreshBearerToken()
    driver = Webdriver(timeout=7)
    driver.startDriver()
    print('Beginning bot loop...')
    time_TBNL_last_checked = time.time()
    time_bearer_last_checked = time.time()

    while True:
        MapleStory.checkSite()
        Temtem.checkSite()

        time_TBNL_last_checked = Functions.checkThumbnails(
            time_TBNL_last_checked, driver)

        # refresh bearer token // important for api/info.json check
        time_bearer_last_checked = Functions.bearerRefresh(
            time_bearer_last_checked)


if __name__ == '__main__':
    main()

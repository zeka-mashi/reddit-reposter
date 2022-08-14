import time
import asyncio
from config.bot import Bot
from bot.components.session import Session
from bot.components.database import Database
from bot.components.webdriver import Webdriver
from bot.sites.maplestory import MapleStory
#from bot.sites.temtem import Temtem


def main():
    bot = Bot()
    print('[!] Initializing Reddit Bot\nBot version: ' + bot.BOT_VERSION +
          ' - Private Sub: ' + bot.PRIVATE_SUB + ' - Log Thread: ' + bot.BOT_LOG_POST)
    bot.login()
    database = Database(bot.DATABASE_URL)
    database.connect_to_db()
    session = Session(bot)
    asyncio.run(session.refreshBearerToken())
    # driver = Webdriver(bot)  # default timeout in Webdriver is 7sec

    print('[!] Initialization complete. Starting bot loop!')
    time_TBNL_last_checked = time.time()
    time_bearer_last_checked = time.time()

    #sites = [MapleStory(bot, session, database)]

    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    # asyncio.ensure_future(function_1())
    # asyncio.ensure_future(function_2())
    loop.run_forever()

    """ while True:
        MapleStory.checkSite()
        Temtem.checkSite()

        time_TBNL_last_checked = Functions.checkThumbnails(
            time_TBNL_last_checked, driver)

        # refresh bearer token // important for api/info.json check
        time_bearer_last_checked = Functions.bearerRefresh(
            time_bearer_last_checked) """


if __name__ == '__main__':
    main()

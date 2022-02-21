import html2text
import time
import config.bot as bot
from bot.components.error import Error


class Functions:
    def findNth(haystack, needle, n):
        start = haystack.find(needle)
        while start >= 0 and n > 1:
            start = haystack.find(needle, start+len(needle))
            n -= 1
        return start

    def handleText(content):
        h = html2text.HTML2Text()
        h.ignore_images = True
        h.single_line_break = True
        h.wrap_list_items = True
        snip_text = h.handle(content)
        return snip_text.replace('%0A', '')

    def checkThumbnails(last, driver):
        if ((time.time() - last) >= bot.thumbnail_time_check_limit):
            print('<-> Checking for missing thumbnails')
            try:
                try:
                    driver.execute_script("location.reload(true);")  # refresh
                except Exception as e:
                    Error.msg(e, " at checkThumbnails driver execute")
                    # try this because of the timeout
                    driver.refreshWait()
                list = driver.find_elements_by_xpath(
                    "//form[@class='toggle rescrape-button ']/span[@class='option main active']/a[@class='togglebutton access-required']")
                if list:
                    bot.thumbnail_time_check_limit = 180
                    print('<!> ' + str(len(list)) +
                          ' missing thumbnails detected. Attempting to resolve... checking back in 3 mins')
                    for retry_thumb in list:
                        retry_thumb.click()
                        time.sleep(1)
                        driver.find_element_by_xpath(
                            "//form[@class='toggle rescrape-button ']/span[@class='option error active']/a[@class='yes']").click()
                else:
                    if bot.thumbnail_time_check_limit == 180:
                        print(
                            '<!> Missing thumbnails were resolved. Setting default check time (900).')
                    bot.thumbnail_time_check_limit = 900
            except Exception as e:
                Error.msg(e, " at bottom checkThumbnails")
            print('<-> Done checking')
            return time.time()  # update last_time_checked to now
        return last

    def bearerRefresh(last):
        if ((time.time() - last) >= bot.bearer_token_time_check_limit):
            try:
                bot.Session.refreshBearerToken()
                return time.time()
            except Exception as e:
                Error.msg(e, " at bearer refresh")
        return last

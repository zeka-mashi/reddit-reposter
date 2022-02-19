import praw
from prawcore.exceptions import PrawcoreException
import os
import time
import random
import requests
import requests.auth
import psycopg2
import lxml
import timeago
import datetime
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import html2text
import string
from ftfy import fix_text
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

#=============[SET UP]=============#
USERNAME = os.environ['USERNAME']
PASSWORD = os.environ['PASSWORD']
CLIENT_ID = os.environ['CLIENT_ID']
CLIENT_SECRET = os.environ['CLIENT_SECRET']
DATABASE_URL = os.environ['DATABASE_URL']

BOT_VERSION = 'v1.3'
USER_AGENT = 'script:reddit help and news bot ' + BOT_VERSION + ' by u/' + USERNAME

PRIVATE_SUB = os.environ['PRIVATE_SUB']
# Get the reddit thread ID for the bot's log (should be in your private sub!)
BOT_LOG_POST = os.environ['BOT_LOG']
#==================================#

ua = UserAgent()
db_connected = False
cur = None


def connect_to_db():
    global cur
    try:
        print('Connecting to database...')
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        conn.autocommit = True
        cur = conn.cursor()
        print('Successfully connected!')
    except Exception as e:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(e).__name__, e.args)
        print("An exception!... {}".format(message))


connect_to_db()

print("Authenticating Reddit account...")
reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    password=PASSWORD,
    user_agent=USER_AGENT,
    username=USERNAME)
print("Successfully authenticated as {}".format(reddit.user.me()))

# Init our request session (for Reddit only)
print('Starting a Reddit session...')
session = requests.Session()
ua_header = {'User-Agent': 'Reddit session bot for api/info by u/' + USERNAME}
client_auth = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
post_data = {"grant_type": "password",
             "username": USERNAME, "password": PASSWORD}
session_header = ''

# Init the webpage session
print('Starting a webpage request session...')
web = requests.Session()
c_obj = requests.cookies.create_cookie(domain=".pso2.com", name="pso2-age.verification",
                                       path="/", secure="False", value="true")  # create cookies for PSO2 age gate
web.cookies.set_cookie(c_obj)


def refresh_bearer_token():
    global session
    global session_header
    print('<!> Refreshing bearer token now...')
    session_response = session.post(
        "https://www.reddit.com/api/v1/access_token", auth=client_auth, data=post_data, headers=ua_header)
    session_header = {'Authorization': 'bearer ' + session_response.json(
    )['access_token'], 'User-Agent': 'Reddit session bot for api/info by u/' + USERNAME}


refresh_bearer_token()
print('Success!')

# Start our webdriver to check missing thumbnails
print('Starting Google Chrome Webdriver...')
try:
    chrome_options = Options()
    chrome_exec_shim = os.environ.get("GOOGLE_CHROME_SHIM", "chromedriver")
    chrome_options.binary_location = chrome_exec_shim
    userAgent = "script:reddit bot rescrape method by u/" + "USERNAME"
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
    driver.set_page_load_timeout(7)  # 7 seconds timeout
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
    current_url = driver.current_url
    driver.get('https://old.reddit.com/user/' +
               USERNAME + '/submitted/?sort=new')
    WebDriverWait(driver, 5).until(EC.url_changes(current_url))
    print("Finished!")
except Exception as e:
    template = '[!] An exception of type {0} occurred at webdriver startup with arguments: {1!r}'
    print(template.format(type(e).__name__, e.args))

# Init html2text general
h = html2text.HTML2Text()
h.ignore_images = True
h.single_line_break = True
h.wrap_list_items = True

# Init html2text valorant
vh = html2text.HTML2Text()
vh.ignore_images = False
vh.single_line_break = True
vh.wrap_list_items = True
vh.ignore_tables = False
vh.body_width = 3000

# Requests timeout
# 7 seconds; do (2, 5) for 2s connect to server and 5s read timeout
reqTimeout = 7

# Year variable for PSO2 database id's
db_year = datetime.datetime.now()
db_year = str(db_year.year)

websites = [
    'http://maplestory.nexon.net/news',
    'https://pso2.com/news?page=1',
    'https://crema.gg/temtem/',
    'https://playvalorant.com/en-us/news/'
]

maplestory_maint_matches = ['scheduled maintenance', 'unscheduled maintenance',
                            'game update', 'scheduled minor', 'unscheduled minor']
valorant_post_labels = ['dev', 'game-updates', 'announcements']

last_thumbnail_check = time.time()
# check after when? // default = 15 mins (900 sec)
thumbnail_time_check_limit = 900
last_bearer_token_time_check = time.time()
# refresh the token after 50 mins (3000 sec)
bearer_token_time_check_limit = 3000


def find_nth(haystack, needle, n):
    start = haystack.find(needle)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start+len(needle))
        n -= 1
    return start


def main():
    while True:
        try:
            for index, site in enumerate(websites):
                page_source = ''
                header = {'User-Agent': str(ua.chrome)}
                try:
                    webpage = web.get(site, headers=header, timeout=reqTimeout)
                except requests.exceptions.ReadTimeout as e:
                    print('ReadTimeout occurred with site ' +
                          str(site) + '... continuing...')
                    continue
                except requests.exceptions.ConnectTimeout as e:
                    print('ConnectTimeout occurred with site ' +
                          str(site) + '... continuing...')
                    continue
                except Exception as e:
                    template = '[!] An exception of type {0} occurred at webpage request with arguments: {1!r}'
                    print(template.format(type(e).__name__, e.args))
                    continue
                page_source = webpage.text
                if index == 0:  # maplestory
                    try:
                        page_source = page_source[page_source.find(
                            '<h2 class="title">NEWS</h2>'):page_source.find('<p class="button-container">')]
                        ms_soup = BeautifulSoup(page_source, 'lxml')
                        for newsItem in ms_soup.findAll('li', {'class': 'news-item'}):
                            need_commit = True
                            label = newsItem.find('div', {'class': 'label'})
                            newsDivs = newsItem.find('div', {'class': 'text'})
                            url = newsDivs.find('a', href=True)
                            newsID = str(url['href'])[
                                str(url['href']).find('news/')+5:11]
                            maint_time = ''
                            try:
                                cur.execute("SELECT id FROM ms1")
                                id_list = cur.fetchall()
                                for ids in id_list:
                                    if newsID in ids:
                                        need_commit = False
                                        break
                                if need_commit:
                                    if any(x in url.getText().lower() for x in maplestory_maint_matches):
                                        try:
                                            maint_time = newsDivs.find('p')
                                            maint_time = maint_time.getText()
                                            maint_time = " " + \
                                                maint_time[maint_time.find(
                                                    ' at ')+1:maint_time.find(').')+1]
                                        except Exception as e:
                                            print(
                                                'Exception at maint_time reading... ' + e)
                                            maint_time = ''
                                    try:
                                        cur.execute(
                                            "INSERT INTO ms1(id) VALUES(%s)", (newsID,))
                                    except (Exception, psycopg2.Error) as error:
                                        print(
                                            "PostgreSQL error at cur.execute:", error)
                                        print('Attempting to reconnect now...')
                                        connect_to_db()
                                        cur.execute(
                                            "INSERT INTO ms1(id) VALUES(%s)", (newsID,))
                                    print(
                                        '[MAPLESTORY] New post found! Adding id ' + newsID + ' to db...')

                                    # check if already submitted
                                    if str(label.getText()).lower() == "community":
                                        news_submission = reddit.subreddit(PRIVATE_SUB).submit(url.getText(
                                        ) + maint_time, url='http://maplestory.nexon.net' + url['href'], send_replies=False)
                                        BOT_LOG_POST.reply('Found r/MapleStory \'Community\' post  `' + url.getText(
                                        ) + '`. Ignoring post and posting to private sub with id https://redd.it/{}'.format(news_submission.id))
                                    else:
                                        page = session.get(
                                            'https://oauth.reddit.com/api/info.json?url=http://maplestory.nexon.net' + url['href'], headers=session_header, timeout=reqTimeout)
                                        is_posted_already = page.text
                                        if is_posted_already.count('"subreddit": "Maplestory"') >= 1:
                                            # already posted
                                            news_submission = reddit.subreddit(PRIVATE_SUB).submit(url.getText(
                                            ) + maint_time, url='http://maplestory.nexon.net' + url['href'], send_replies=False)
                                            BOT_LOG_POST.reply('Found r/MapleStory news `' + url.getText(
                                            ) + '` already posted... posting instead to private sub with id https://redd.it/{}'.format(news_submission.id))
                                        else:
                                            news_submission = reddit.subreddit('maplestory').submit(url.getText(
                                            ) + maint_time, url='http://maplestory.nexon.net' + url['href'], flair_id='a19e8bd0-b6c9-11e6-9867-0ea17315be16', send_replies=False)
                                            BOT_LOG_POST.reply('Found news `' + url.getText(
                                            ) + '` and posted to r/MapleStory with id https://redd.it/{}'.format(news_submission.id))
                                            if str(label.getText()).lower() == 'update':
                                                print(
                                                    'MapleStory update post... ignoring comment reply')
                                                # do nothing!
                                            elif str(label.getText()).lower() == 'sale' and 'cash shop' in str(url.getText()).lower():
                                                newsDesc = newsDivs.find('p')
                                                newsDesc = newsDesc.getText()
                                                newspage = web.get(
                                                    'http://maplestory.nexon.net' + url['href'], headers=header, timeout=reqTimeout)
                                                content = newspage.text
                                                try:
                                                    if 'DAILY DEALS' not in content:
                                                        contentNew = content[content.find(
                                                            '<!-- begin: article content -->'):content.find('ONGOING SALES')]
                                                        contentDD = ''
                                                    else:
                                                        contentNew = content[content.find(
                                                            '<!-- begin: article content -->'):content.find('DAILY DEALS')]
                                                        contentDD = content[content.find(
                                                            'DAILY DEALS'):content.find('ONGOING SALES')]
                                                    contentOngoing = content[content.find(
                                                        'ONGOING SALES'):content.find('<!-- end: article content -->')]
                                                    # get soups of different sale types
                                                    ms_soup_new = BeautifulSoup(
                                                        contentNew, 'lxml')
                                                    ms_soup_DD = BeautifulSoup(
                                                        contentDD, 'lxml')
                                                    ms_soup_Ongoing = BeautifulSoup(
                                                        contentOngoing, 'lxml')
                                                    sale_text = ''
                                                    new_list = ms_soup_new.findAll(
                                                        'h1', style=False)
                                                    if new_list:
                                                        sale_text = sale_text + '## New this update:\n'
                                                        for item in new_list:
                                                            sale_text = sale_text + '* **' + item.getText().strip() + '**\n'
                                                            if item.getText().lower() == 'gachapon update':  # expand on gachapon
                                                                newItems = ms_soup_new.findAll(
                                                                    'span', {'style': "text-decoration: underline;"})
                                                                for index, new_item in enumerate(newItems):
                                                                    gacha_item_name = new_item.find(
                                                                        'span', {'style': "font-size: 12pt;"})  # gachapon update
                                                                    if gacha_item_name:
                                                                        sale_text = sale_text + ' * **' + gacha_item_name.getText().strip() + ':**   \n'
                                                                        first_pos = find_nth(
                                                                            content, '<span style="text-decoration: underline;"><span style="font-size: 12pt;">', index)
                                                                        second_pos = find_nth(
                                                                            content, '<span style="text-decoration: underline;"><span style="font-size: 12pt;">', index + 1)
                                                                        if second_pos == -1:
                                                                            second_pos = find_nth(
                                                                                content, '<span style="text-decoration: underline;">', index + 2)
                                                                        src = BeautifulSoup(
                                                                            content[first_pos:second_pos], 'lxml')
                                                                        list = src.findAll(
                                                                            'li')
                                                                        for items in list:
                                                                            sale_text = sale_text + '     * ' + items.getText().strip() + '   \n'
                                                    dd_list = ms_soup_DD.findAll(
                                                        'span', {'style': "text-decoration: underline;"})
                                                    if dd_list:
                                                        sale_text = sale_text + '\n## Daily Deals:\n'
                                                        for item in dd_list:
                                                            # daily deal item header
                                                            item_name = item.find(
                                                                'span', {'style': "font-size: 14pt;"})
                                                            if item_name:
                                                                sale_text = sale_text + ' * **' + item_name.getText().strip() + '**   \n'
                                                    ongoing_list = ms_soup_Ongoing.findAll(
                                                        'h1', style=False)  # all ongoing are h1 elements
                                                    if ongoing_list:
                                                        sale_text = sale_text + '\n## Ongoing Sales:\n'
                                                        for item in ongoing_list:
                                                            sale_text = sale_text + ' * **' + item.getText().strip() + '**    \n'

                                                    write_text = sale_text + \
                                                        '...\n\n[See detailed sales info here](http://maplestory.nexon.net' + \
                                                        url['href'] + ')'
                                                    time.sleep(1)
                                                    news_reply = news_submission.reply(
                                                        '**' + url.getText() + '**\n>' + newsDesc + '\n\nRundown of this cash shop update:\n***\n' + write_text + '\n***\n^(I am a bot. Have a suggestion on how to improve me? Send a PM!)')
                                                    news_reply.disable_inbox_replies()
                                                except Exception as e:
                                                    template = '[!] A general exception of type {0} occurred at MapleStory sales snippet post with arguments: {1!r}'
                                                    print(template.format(
                                                        type(e).__name__, e.args))
                                            else:
                                                newsDesc = newsDivs.find('p')
                                                newsDesc = newsDesc.getText()
                                                newspage = web.get(
                                                    'http://maplestory.nexon.net' + url['href'], headers=header, timeout=reqTimeout)
                                                content = newspage.text
                                                content = content[content.find(
                                                    '<!-- begin: article content -->'):content.find('<!-- end: article content -->')]
                                                content = content.replace(
                                                    "<em>", "")
                                                content = content.replace(
                                                    "</em>", "")
                                                content = content.replace(
                                                    "</span>", "")
                                                content = content.replace(
                                                    " </strong>", "</strong>")
                                                content = content.replace(
                                                    " <br />", "<br />")
                                                content = content.replace(
                                                    "<br /></strong>", "</strong><br />")
                                                content = content.replace(
                                                    "<strong><strong>", "<strong>")
                                                content = content.replace(
                                                    "</strong></strong>", "</strong>")
                                                content = content.replace(
                                                    "<strong> ", " <strong>")
                                                content = content.replace(
                                                    "</strong>", "**")
                                                content = content.replace(
                                                    "<strong>", "**")
                                                snip_text = h.handle(content)
                                                snip_text = snip_text.replace(
                                                    '%0A', '')
                                                if len(snip_text) > 1500:
                                                    snip_text = snip_text[:(
                                                        snip_text[:1500].rfind(' '))]
                                                    snip_text = snip_text + \
                                                        '...\n\n[Read the full post here](http://maplestory.nexon.net' + \
                                                        url['href'] + ')'
                                                time.sleep(2)
                                                news_reply = news_submission.reply('**' + url.getText() + '**\n>' + newsDesc + '\n\nPreview snippet:\n***\n' +
                                                                                   snip_text + '\n***\n^(I am a bot. This was performed automatically. Suggestions? Send a PM.)')
                                                news_reply.disable_inbox_replies()
                                        is_posted_already = ''
                                        time.sleep(2)
                                url = ''
                                newsID = ''
                                maint_time = ''
                                label = ''
                            except (psycopg2.InterfaceError, psycopg2.DatabaseError) as error:
                                template = '[!] A psycopg2 exception of type {0} occurred at bottom MapleStory news check with args: {1!r}'
                                print(template.format(
                                    type(error).__name__, error.args))
                                print('Attempting to reconnect now...')
                                connect_to_db()
                            except (Exception, psycopg2.Error) as error:
                                template = '[!] An error while excecuting PostgreSQL of type {0} occurred at bottom MapleStory news check with args: {1!r}'
                                print(template.format(
                                    type(error).__name__, error.args))
                    except Exception as e:
                        template = '[!] A general exception of type {0} occurred at bottom MapleStory news check with arguments: {1!r}'
                        print(template.format(type(e).__name__, e.args))

                if index == 1:  # pso2
                    try:
                        # repeat due to potential landing page redirection
                        webpage = web.get(
                            site, headers=header, timeout=reqTimeout)
                    except requests.exceptions.ReadTimeout as e:
                        print(
                            'ReadTimeout occurred at PSO2 site check... continuing...')
                        continue
                    except requests.exceptions.ConnectTimeout as e:
                        print(
                            'ConnectTimeout occurred at PSO2 site check... continuing...')
                        continue
                    except Exception as e:
                        template = '[!] An exception of type {0} occurred at PSO2 site webpage request with arguments: {1!r}'
                        print(template.format(type(e).__name__, e.args))
                        continue
                    page_source = webpage.text
                    try:
                        page_source = page_source[page_source.find('<div class="all-news-section">'):page_source.find(
                            '<div class="load-more-wrapper announcement-pagination">')]
                        pso2_soup = BeautifulSoup(page_source, 'lxml')
                        for newsItem in pso2_soup.findAll('li', {'class': 'news-item all sr'}):
                            need_commit = True
                            label = newsItem.find('p', {'class': 'tag'})
                            label = label.getText().replace(' ', '-')
                            newsDivs = newsItem.find(
                                'div', {'class': 'content'})
                            title = newsDivs.find('h3', {'class': 'title'})
                            url = newsDivs.find('a', onclick=True)
                            newsID = str(url['onclick'])[str(url['onclick']).find(
                                'ShowDetails(')+13:str(url['onclick']).find(',')-1]
                            constructed_url = 'https://pso2.com/news/' + \
                                str(label).lower() + '/' + newsID
                            #print('https://pso2.com/news/' + str(label).lower() + '/' + newsID)
                            newsDB_ID = db_year + '-' + newsID
                            try:
                                cur.execute("SELECT id FROM pso2")
                                id_list = cur.fetchall()
                                for ids in id_list:
                                    if newsDB_ID in ids:
                                        need_commit = False
                                        break
                                if need_commit:
                                    try:
                                        cur.execute(
                                            "INSERT INTO pso2(id) VALUES(%s)", (newsDB_ID,))
                                    except (Exception, psycopg2.Error) as error:
                                        print(
                                            "PostgreSQL error at cur.execute:", error)
                                        print('Attempting to reconnect now...')
                                        connect_to_db()
                                        cur.execute(
                                            "INSERT INTO pso2(id) VALUES(%s)", (newsDB_ID,))
                                    print(
                                        '[PSO2] New post found! Adding id ' + newsDB_ID + ' to db...')

                                    # check if already submitted
                                    page = session.get('https://oauth.reddit.com/api/info.json?url=' +
                                                       constructed_url, headers=session_header, timeout=reqTimeout)
                                    is_posted_already = page.text
                                    if is_posted_already.count('"subreddit": "PSO2"') >= 1:
                                        # already posted
                                        news_submission = reddit.subreddit(PRIVATE_SUB).submit(
                                            title.getText().lstrip(), url=constructed_url, send_replies=False)
                                        BOT_LOG_POST.reply('Found r/PSO2 news `' + title.getText().lstrip(
                                        ) + '` already posted... posting instead to private sub with id https://redd.it/{}'.format(news_submission.id))
                                    else:
                                        news_submission = reddit.subreddit('PSO2').submit(title.getText().lstrip(
                                        ), url=constructed_url, flair_id='5cc615f0-ea16-11e3-8153-12313d19252b', send_replies=False)
                                        BOT_LOG_POST.reply('Found news `' + title.getText().lstrip(
                                        ) + '` and posted to r/PSO2 with id https://redd.it/{}'.format(news_submission.id))
                                        # news_submission.flair.select('5cc615f0-ea16-11e3-8153-12313d19252b') # NA News
                                    is_posted_already = ''
                                    time.sleep(2)
                                constructed_url = ''
                                url = ''
                            except (psycopg2.InterfaceError, psycopg2.DatabaseError) as error:
                                template = '[!] A psycopg2 exception of type {0} occurred at bottom PSO2 news check with args: {1!r}'
                                print(template.format(
                                    type(error).__name__, error.args))
                                print('Attempting to reconnect now...')
                                connect_to_db()
                            except (Exception, psycopg2.Error) as error:
                                template = '[!] An error while excecuting PostgreSQL of type {0} occurred at bottom PSO2 news check with args: {1!r}'
                                print(template.format(
                                    type(error).__name__, error.args))
                    except Exception as e:
                        template = '[!] A general exception of type {0} occurred at bottom PSO2 news check with arguments: {1!r}'
                        print(template.format(type(e).__name__, e.args))

                if index == 2:  # temtem
                    try:
                        page_source = page_source[page_source.find(
                            '<div id="primary" class="content-area">'):page_source.find('<nav class="navigation')]
                        temtem_soup = BeautifulSoup(page_source, 'lxml')
                        for temItem in temtem_soup.findAll('article', {'class': 'post'}):
                            need_commit = True
                            temlabel = temItem.find(
                                'a', {'rel': 'category tag'})
                            temlabel_text = str(temlabel.getText())
                            if temlabel_text.lower() != 'patch notes':
                                temlabel_text = ''
                            temHeader = temItem.find('h2')
                            temNewsStr = temHeader.getText()
                            temURL = temItem.find(
                                'a', {'rel': 'bookmark'}, href=True)
                            temID = str(temURL['href'])[str(temURL['href']).find(
                                'temtem/')+7:len(str(temURL['href']))-1]
                            try:
                                cur.execute("SELECT id FROM temtem")
                                id_list_temtem = cur.fetchall()
                                for ids in id_list_temtem:
                                    if temID in ids:
                                        need_commit = False
                                        break
                                if need_commit:
                                    try:
                                        cur.execute(
                                            "INSERT INTO temtem(id) VALUES(%s)", (temID,))
                                    except (Exception, psycopg2.Error) as error:
                                        print(
                                            "PostgreSQL error at cur.execute:", error)
                                        print('Attempting to reconnect now...')
                                        connect_to_db()
                                        cur.execute(
                                            "INSERT INTO temtem(id) VALUES(%s)", (temID,))
                                    print(
                                        '[TEMTEM] New post found! Adding id ' + temID + ' to db...')

                                    # check if already submitted
                                    page = session.get(
                                        'https://oauth.reddit.com/api/info.json?url=' + temURL['href'], headers=session_header, timeout=reqTimeout)
                                    is_posted_already = page.text
                                    if is_posted_already.count('"subreddit": "PlayTemtem"') >= 1:
                                        # already posted
                                        temnews_submission = reddit.subreddit(PRIVATE_SUB).submit(
                                            temNewsStr + " " + temlabel_text, url=temURL['href'], send_replies=False)
                                        BOT_LOG_POST.reply(
                                            'Found r/PlayTemtem news `' + temNewsStr + '` already posted... posting instead to private sub with id https://redd.it/{}'.format(temnews_submission.id))
                                    else:
                                        temnews_submission = reddit.subreddit('PlayTemtem').submit(
                                            temNewsStr + " " + temlabel_text, url=temURL['href'], flair_id='cc7518e0-31ae-11e8-aad8-0e9586a0d81c', send_replies=False)
                                        temnews_submission.flair.select(
                                            'cc7518e0-31ae-11e8-aad8-0e9586a0d81c')  # News
                                        BOT_LOG_POST.reply(
                                            'Found news `' + temNewsStr + '` and posted to r/PlayTemtem with id https://redd.it/{}'.format(temnews_submission.id))
                                    is_posted_already = ''
                                    time.sleep(2)
                                temlabel_text = ''
                                temNewsStr = ''
                            except (psycopg2.InterfaceError, psycopg2.DatabaseError) as error:
                                template = '[!] A psycopg2 exception of type {0} occurred at bottom Temtem news check with args: {1!r}'
                                print(template.format(type(e).__name__, e.args))
                                print('Attempting to reconnect now...')
                                connect_to_db()
                            except (Exception, psycopg2.Error) as error:
                                template = '[!] An error while excecuting PostgreSQL of type {0} occurred at bottom Temtem news check with args: {1!r}'
                                print(template.format(type(e).__name__, e.args))
                    except Exception as e:
                        template = '[!] A general exception of type {0} occurred at bottom Temtem news check with arguments: {1!r}'
                        print(template.format(type(e).__name__, e.args))

                if index == 3:  # valorant
                    try:
                        page_source = page_source[page_source.find(
                            '<span>Featured News</span>'):page_source.find('Scroll down</span>')]
                        val_soup = BeautifulSoup(page_source, 'lxml')
                        count_id_timeout = 0
                        for valItem in val_soup.findAll('div', {'class': 'news-card'}):
                            need_commit = True
                            valHeader = valItem.find('img', alt=True)
                            valNewsStr = valHeader['alt']
                            valNewsStr = fix_text(valNewsStr)
                            if valNewsStr.isupper():
                                valNewsStr = string.capwords(valNewsStr)
                            valURL = valItem.find('a', href=True)
                            valID = str(valURL['href'])[(str(valURL['href'])[
                                :-1]).rfind('/')+1:len(str(valURL['href']))-1]
                            valLabel = str(valURL['href'])[str(valURL['href']).find(
                                'news/')+5:str(valURL['href'])[:-1].rfind('/')]
                            try:
                                cur.execute("SELECT id FROM valorant")
                                id_list_val = cur.fetchall()
                                for ids in id_list_val:
                                    if valID in ids:
                                        need_commit = False
                                        count_id_timeout += 1
                                        if count_id_timeout > 4:
                                            break
                                if need_commit:
                                    try:
                                        cur.execute(
                                            "INSERT INTO valorant(id) VALUES(%s)", (valID,))
                                    except (Exception, psycopg2.Error) as error:
                                        print(
                                            "PostgreSQL error at cur.execute:", error)
                                        print('Attempting to reconnect now...')
                                        connect_to_db()
                                        cur.execute(
                                            "INSERT INTO valorant(id) VALUES(%s)", (valID,))
                                    print(
                                        '[VALORANT] New post found! Adding id ' + valID + ' to db...')

                                    if valLabel not in valorant_post_labels:
                                        print('<!> The post is a ' + valLabel +
                                              ' post. Not posting anywhere.')
                                    else:
                                        print('<!> The post is a ' + valLabel +
                                              ' post. Attempting to post...')
                                        # check if already submitted
                                        page = session.get('https://oauth.reddit.com/api/info.json?url=https://playvalorant.com' +
                                                           valURL['href'], headers=session_header, timeout=reqTimeout)
                                        is_posted_already = page.text
                                        if is_posted_already.count('"subreddit": "VALORANT"') >= 1:
                                            # already posted
                                            valnews_submission = reddit.subreddit(PRIVATE_SUB).submit(
                                                valNewsStr, url='https://playvalorant.com' + valURL['href'], send_replies=False)
                                            BOT_LOG_POST.reply(
                                                'Found r/VALORANT news `' + valNewsStr + '` already posted... posting instead to private sub with id https://redd.it/{}'.format(valnews_submission.id))
                                        else:
                                            #valnews_submission = reddit.subreddit('VALORANT').submit(valNewsStr, url='https://playvalorant.com/' + valURL['href'], send_replies=False)
                                            # valnews_submission.flair.select('') # News
                                            #BOT_LOG_POST.reply('Found news `' + valNewsStr + '` and posted to r/VALORANT with id https://redd.it/{}'.format(valnews_submission.id))

                                            try:
                                                webpage = web.get(
                                                    'https://playvalorant.com' + valURL['href'], headers=header, timeout=reqTimeout)
                                                page_source = webpage.text
                                                page_source = page_source[page_source.find('<div class="NewsArticleContent-module--articleTextContent--2yATc">'):page_source.find(
                                                    '<div class="NewsArticleContent-module--authorsWrapper--2gp9d">')]
                                                text = page_source.replace(
                                                    '<em></em>', '')
                                                text = text.replace(
                                                    '<strong><br/></strong>', '')
                                                text = text.replace(
                                                    '<strong></strong>', '')
                                                text = text.replace(
                                                    '<strong><strong>', '<strong>')
                                                text = text.replace(
                                                    '</strong><br/></strong>', '</strong>')
                                                text = text.replace(
                                                    '</strong></strong>', '</strong>')
                                                text = text.replace(
                                                    '<br/></em>', '</em>')
                                                bad_em_return = """<em>
											</em>"""
                                                text = text.replace(
                                                    bad_em_return, '')
                                                bad_strong_return = """<strong>
											</strong>"""
                                                text = text.replace(
                                                    bad_strong_return, '')
                                                text = text.replace(
                                                    '<br/></strong>', '</strong>')
                                                text = text.replace(
                                                    ' </p>', '</p>')
                                                text = text.replace(
                                                    '&#x27;', "'")
                                                text = vh.handle(text)
                                                text = fix_text(text)
                                                text = text.replace('![', '[')
                                                text = text.replace(
                                                    ')[[', ') [[')
                                                #text = text.replace('** _', '**_')
                                                text = text.replace('.Â', '.')
                                                text = text.replace('%0A', '')
                                                newsText = '####Via [playvalorant.com](https://playvalorant.com/' + \
                                                    valURL['href'] + \
                                                    '):\n\n' + text
                                                # temporarily post to private sub to test
                                                valnews_submission = reddit.subreddit(PRIVATE_SUB).submit(
                                                    valNewsStr, selftext=newsText, send_replies=False)
                                            except Exception as e:
                                                template = '[!] A general exception of type {0} occurred at bottom Valorant news html to text connection with arguments: {1!r}'
                                                print(template.format(
                                                    type(e).__name__, e.args))
                                                #valnews_submission = reddit.subreddit('VALORANT').submit(valNewsStr, url='https://playvalorant.com' + valURL['href'], send_replies=False)
                                            valnews_submission = reddit.subreddit(PRIVATE_SUB).submit(
                                                valNewsStr, url='https://playvalorant.com' + valURL['href'], flair_id='14bf41ce-90df-11eb-8261-0ed2bdacd8cd', send_replies=False)
                                            # REMOVE THE ABOVE LINE AND UNCOMMENT LINE 534 (ABOVE THE ABOVE LINE) WHEN TESTING IS OVER
                                            BOT_LOG_POST.reply(
                                                'Found news `' + valNewsStr + '` and posted to r/VALORANT with id https://redd.it/{}'.format(valnews_submission.id))
                                        is_posted_already = ''
                                        time.sleep(2)
                                valNewsStr = ''
                            except (psycopg2.InterfaceError, psycopg2.DatabaseError) as error:
                                template = '[!] A psycopg2 exception of type {0} occurred at bottom Valorant news check with args: {1!r}'
                                print(template.format(
                                    type(error).__name__, error.args))
                                print('Attempting to reconnect now...')
                                connect_to_db()
                            except (Exception, psycopg2.Error) as error:
                                template = '[!] An error while excecuting PostgreSQL of type {0} occurred at bottom Valorant news check with args: {1!r}'
                                print(template.format(
                                    type(error).__name__, error.args))
                    except Exception as e:
                        template = '[!] A general exception of type {0} occurred at bottom Valorant news check with arguments: {1!r}'
                        print(template.format(type(e).__name__, e.args))
        except Exception as e:
            template = '[!] An exception of type {0} occurred at outer loop with arguments: {1!r}'
            print(template.format(type(e).__name__, e.args))
            print('Running loop in 4s...')  # 4 + 0 secs
            time.sleep(4)
        # time.sleep(1)

        # check thumbnails
        if ((time.time() - last_thumbnail_check) >= thumbnail_time_check_limit):
            last_thumbnail_check = time.time()
            print('<-> Checking for missing thumbnails')
            try:
                try:
                    driver.execute_script(
                        "location.reload(true);")  # hard refresh?
                except Exception as e:
                    template = '[!] An exception of type {0} occurred at thumbnail driver reload with arguments: {1!r}... attempting to get original page'
                    print(template.format(type(e).__name__, e.args))
                    # try this because timeout
                    driver.get('https://old.reddit.com/user/' +
                               USERNAME + '/submitted/?sort=new')
                    WebDriverWait(driver, 5).until(EC.url_changes(current_url))
                list = driver.find_elements_by_xpath(
                    "//form[@class='toggle rescrape-button ']/span[@class='option main active']/a[@class='togglebutton access-required']")
                if list:
                    thumbnail_time_check_limit = 180
                    print('<!> ' + str(len(list)) +
                          ' missing thumbnails detected. Attempting to resolve... checking back in 3 mins')
                    for retry_thumb in list:
                        retry_thumb.click()
                        time.sleep(1)
                        driver.find_element_by_xpath(
                            "//form[@class='toggle rescrape-button ']/span[@class='option error active']/a[@class='yes']").click()
                else:
                    if thumbnail_time_check_limit == 180:
                        print(
                            '<!> Missing thumbnails were resolved. Setting default check time (900).')
                    thumbnail_time_check_limit = 900
            except Exception as e:
                template = '[!] An exception of type {0} occurred at thumbnail check with arguments: {1!r}'
                print(template.format(type(e).__name__, e.args))
            print('<-> Done checking')

        # refresh bearer token // important for api/info.json check
        if ((time.time() - last_bearer_token_time_check) >= bearer_token_time_check_limit):
            last_bearer_token_time_check = time.time()
            try:
                refresh_bearer_token()
            except Exception as e:
                template = '[!] An exception of type {0} occurred at refresh bearer token with arguments: {1!r}'
                print(template.format(type(e).__name__, e.args))


if __name__ == '__main__':
    main()

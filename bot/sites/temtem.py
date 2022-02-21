from bs4 import BeautifulSoup
import time
import config.bot as bot
from bot.components.database import Database
from bot.components.error import Error
from bot.components.functions import Functions

reddit = bot.Login.getReddit()
site_url = 'https://crema.gg/temtem/'
subreddit_name = 'PlayTemtem'


class Temtem:
    def checkSite():
        page_source = (bot.Session.getPage(site_url)).text
        if page_source == False:  # handle error with page_source by exiting
            return
        try:
            page_source = page_source[page_source.find(
                '<div id="primary" class="content-area">'):page_source.find('<nav class="navigation')]
            temtem_soup = BeautifulSoup(page_source, 'lxml')
            for tem_item in temtem_soup.findAll('article', {'class': 'post'}):
                tem_label = tem_item.find(
                    'a', {'rel': 'category tag'})
                tem_label_text = str(tem_label.getText())
                if tem_label_text.lower() != 'patch notes':
                    tem_label_text = ''
                tem_news = (tem_item.find('h2')).getText()
                temURL = tem_item.find(
                    'a', {'rel': 'bookmark'}, href=True)
                temID = str(temURL['href'])[str(temURL['href']).find(
                    'temtem/')+7:len(str(temURL['href']))-1]
                try:
                    id_list = Database.retrieve("temtem")
                    if temID not in id_list:
                        Database.insert("temtem", temID)

                        """ # check if already submitted
                        already_posted = (bot.Session.getPage(
                            'https://oauth.reddit.com/api/info.json?url=' + temURL['href'])).text
                        if already_posted.count('"subreddit": "' + subreddit_name + '"') >= 1:
                            # already posted
                            temnews_submission = reddit.subreddit(bot.PRIVATE_SUB).submit(
                                tem_news + " " + tem_label_text, url=temURL['href'], send_replies=False)
                            reddit.submission(bot.BOT_LOG_POST).reply(
                                'Found r/' + subreddit_name + ' news `' + tem_news + '` already posted... posting instead to private sub with id https://redd.it/{}'.format(temnews_submission.id))
                        else:
                            temnews_submission = reddit.subreddit(subreddit_name).submit(
                                tem_news + " " + tem_label_text, url=temURL['href'], flair_id='cc7518e0-31ae-11e8-aad8-0e9586a0d81c', send_replies=False)
                            temnews_submission.flair.select(
                                'cc7518e0-31ae-11e8-aad8-0e9586a0d81c')  # News
                            reddit.submission(bot.BOT_LOG_POST).reply(
                                'Found news `' + tem_news + '` and posted to r/' + subreddit_name + ' with id https://redd.it/{}'.format(temnews_submission.id)) """
                        already_posted = ''
                        time.sleep(2)
                    tem_label_text = ''
                    tem_news = ''
                except Exception as e:
                    Error.msg(e, " at bottom Temtem")
        except Exception as e:
            Error.msg(e, " at end Temtem")

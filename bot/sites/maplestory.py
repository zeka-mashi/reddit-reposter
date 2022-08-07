from bs4 import BeautifulSoup
import time
import asyncio
from bot.components.error import Error
from bot.components.functions import Functions


class MapleStory:
    def __init__(self, bot, session, database):
        self.site_url = 'http://maplestory.nexon.net/news'
        self.subreddit_name = 'Maplestory'
        self.bot = bot
        self.session = session
        self.database = database

    async def checkSite(self):
        page_source = asyncio.run(self.session.getPage(self.site_url))
        if page_source == False:  # handle error with page_source by exiting
            return
        try:
            page_source = page_source[page_source.find(
                '<h2 class="title">NEWS</h2>'):page_source.find('<p class="button-container">')]
            ms_soup = BeautifulSoup(page_source, 'lxml')
            for news_item in ms_soup.findAll('li', {'class': 'news-item'}):
                label = news_item.find('div', {'class': 'label'})
                news_divs = news_item.find('div', {'class': 'text'})
                url = news_divs.find('a', href=True)
                news_ID = str(url['href'])[str(url['href']).find('news/')+5:11]
                maint_time = ''
                try:
                    id_list = self.database.retrieve('ms1')
                    if news_ID not in id_list:
                        if any(x in url.getText().lower() for x in ['scheduled maintenance', 'unscheduled maintenance',
                                                                    'game update', 'scheduled minor', 'unscheduled minor']):
                            try:
                                maint_time = (news_divs.find('p')).getText()
                                maint_time = ' ' + \
                                    maint_time[maint_time.find(
                                        ' at ')+1:maint_time.find(').')+1]
                            except Exception as e:
                                Error.msg(e, ' at maintenance reading')
                                maint_time = ''
                        self.database.insert('ms1', news_ID)

                        # check if already submitted
                        if str(label.getText()).lower() == "community" and any(x in url.getText().lower() for x in ['community contests', 'art corner', 'livestream', 'your maplestory']):
                            news_submission = self.bot.reddit.subreddit(self.bot.PRIVATE_SUB).submit(url.getText(
                            ) + maint_time, url='http://maplestory.nexon.net' + url['href'], send_replies=False)
                            self.bot.reddit.submission(self.bot.BOT_LOG_POST).reply('Found r/' + self.subreddit_name + ' \'Community\' post  `' + url.getText(
                            ) + '`. Ignoring post and posting to private sub with id https://redd.it/{}'.format(news_submission.id))
                        else:
                            already_posted = asyncio.run(self.session.getPage(
                                'https://oauth.reddit.com/api/info.json?url=http://maplestory.nexon.net' + url['href']))
                            if already_posted.count('"subreddit": "' + self.subreddit_name + '"') >= 1:
                                # already posted
                                news_submission = self.bot.reddit.subreddit(self.bot.PRIVATE_SUB).submit(url.getText(
                                ) + maint_time, url='http://maplestory.nexon.net' + url['href'], send_replies=False)
                                self.bot.reddit.submission(self.bot.BOT_LOG_POST).reply('Found r/' + self.subreddit_name + ' news `' + url.getText(
                                ) + '` already posted... posting instead to private sub with id https://redd.it/{}'.format(news_submission.id))
                            else:
                                # replace this config.private_sub after all good
                                news_submission = self.bot.reddit.subreddit(self.subreddit_name).submit(url.getText(
                                ) + maint_time, url='http://maplestory.nexon.net' + url['href'], flair_id='a19e8bd0-b6c9-11e6-9867-0ea17315be16', send_replies=False)
                                self.bot.reddit.submission(self.bot.BOT_LOG_POST).reply('Found news `' + url.getText(
                                ) + '` and posted to r/' + self.subreddit_name + ' with id https://redd.it/{}'.format(news_submission.id))

                                # begin comment snippets
                                if str(label.getText()).lower() == 'update':
                                    print(
                                        self.subreddit_name + ' update post... ignoring comment reply')
                                    # do nothing!
                                elif str(label.getText()).lower() == 'sale' and 'cash shop' in str(url.getText()).lower():
                                    news_desc = (news_divs.find('p')).getText()
                                    content = asyncio.run(self.session.getPage(
                                        'http://maplestory.nexon.net' + url['href']))
                                    try:
                                        if 'DAILY DEALS' not in content:
                                            content_new = content[content.find(
                                                '<!-- begin: article content -->'):content.find('ONGOING SALES')]
                                            content_dd = ''
                                        else:
                                            content_new = content[content.find(
                                                '<!-- begin: article content -->'):content.find('DAILY DEALS')]
                                            content_dd = content[content.find(
                                                'DAILY DEALS'):content.find('ONGOING SALES')]
                                        content_ongoing = content[content.find(
                                            'ONGOING SALES'):content.find('<!-- end: article content -->')]
                                        # get soups of different sale types
                                        ms_soup_new = BeautifulSoup(
                                            content_new, 'lxml')
                                        ms_soup_dd = BeautifulSoup(
                                            content_dd, 'lxml')
                                        ms_soup_ongoing = BeautifulSoup(
                                            content_ongoing, 'lxml')
                                        sale_text = ''
                                        new_list = ms_soup_new.findAll(
                                            'h1', style=False)
                                        if new_list:
                                            sale_text = sale_text + '## New this update:\n'
                                            for item in new_list:
                                                sale_text = sale_text + '* **' + item.getText().strip() + '**\n'
                                                if item.getText().lower() == 'gachapon update':  # expand on gachapon
                                                    new_items = ms_soup_new.findAll(
                                                        'span', {'style': "text-decoration: underline;"})
                                                    for index, new_item in enumerate(new_items):
                                                        gacha_item_name = new_item.find(
                                                            'span', {'style': "font-size: 12pt;"})  # gachapon update
                                                        if gacha_item_name:
                                                            sale_text = sale_text + ' * **' + gacha_item_name.getText().strip() + ':**   \n'
                                                            first_pos = Functions.findNth(
                                                                content, '<span style="text-decoration: underline;"><span style="font-size: 12pt;">', index)
                                                            second_pos = Functions.findNth(
                                                                content, '<span style="text-decoration: underline;"><span style="font-size: 12pt;">', index + 1)
                                                            if second_pos == -1:
                                                                second_pos = Functions.findNth(
                                                                    content, '<span style="text-decoration: underline;">', index + 2)
                                                            src = BeautifulSoup(
                                                                content[first_pos:second_pos], 'lxml')
                                                            list = src.findAll(
                                                                'li')
                                                            for items in list:
                                                                sale_text = sale_text + '     * ' + items.getText().strip() + '   \n'
                                        dd_list = ms_soup_dd.findAll(
                                            'span', {'style': "text-decoration: underline;"})
                                        if dd_list:
                                            sale_text = sale_text + '\n## Daily Deals:\n'
                                            for item in dd_list:
                                                # daily deal item header
                                                item_name = item.find(
                                                    'span', {'style': "font-size: 14pt;"})
                                                if item_name:
                                                    sale_text = sale_text + ' * **' + item_name.getText().strip() + '**   \n'
                                        ongoing_list = ms_soup_ongoing.findAll(
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
                                            '**' + url.getText() + '**\n>' + news_desc + '\n\nRundown of this cash shop update:\n***\n' + write_text + '\n***\n^(' + self.bot.BOT_FOOTER + ')')
                                        news_reply.disable_inbox_replies()
                                    except Exception as e:
                                        Error.msg(e, " at cash shop update")
                                else:
                                    try:
                                        news_desc = (
                                            news_divs.find('p')).getText()
                                        content = asyncio.run(self.session.getPage(
                                            'http://maplestory.nexon.net' + url['href']))
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
                                        snip_text = Functions.handleText(
                                            content)
                                        # make sure we fall within character limit for replies
                                        if len(snip_text) > 1500:
                                            snip_text = snip_text[:(
                                                snip_text[:1500].rfind(' '))]
                                            snip_text = snip_text + \
                                                '...\n\n[Read the full post here](http://maplestory.nexon.net' + \
                                                url['href'] + ')'
                                        time.sleep(2)
                                        news_reply = news_submission.reply('**' + url.getText() + '**\n>' + news_desc + '\n\nPreview snippet:\n***\n' +
                                                                           snip_text + '\n***\n^(' + self.bot.BOT_FOOTER + ')')
                                        news_reply.disable_inbox_replies()
                                    except Exception as e:
                                        Error.msg(
                                            e, " at bottom inner MapleStory")
                            already_posted = ''
                            await asyncio.sleep(1)
                except Exception as e:
                    Error.msg(e, " at bottom MapleStory")
        except Exception as e:
            Error.msg(e, " at end MapleStory")

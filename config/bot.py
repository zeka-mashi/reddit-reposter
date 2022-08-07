import os
import praw


class Bot:
    def __init__(self):
        #========[BELOW CONFIG VARS]========#
        #=====[TO BE ENTERED IN HEROKU]=====#
        self.USERNAME = os.environ['USERNAME']
        self.PASSWORD = os.environ['PASSWORD']
        self.CLIENT_ID = os.environ['CLIENT_ID']
        self.CLIENT_SECRET = os.environ['CLIENT_SECRET']
        self.DATABASE_URL = os.environ['DATABASE_URL']
        self.PRIVATE_SUB = os.environ['PRIVATE_SUB']
        # Get the reddit thread ID for the bot's log (should be in your private sub!)
        self.BOT_LOG_POST = os.environ['BOT_LOG']

        #=============[SET UP]=============#
        self.BOT_VERSION = 'v1.5'
        self.USER_AGENT = 'script:reddit news bot ' + \
            self.BOT_VERSION + ' by u/' + self.USERNAME
        # the footer text for comments from the bot
        self.BOT_FOOTER = 'I am a bot and this was performed automatically.'

        self.req_timeout = 7

        # time to re-check thumbnails (default: 900 sec)
        self.thumbnail_time_check_limit = 900
        # time to refresh the token (default: 3000 sec)
        self.bearer_token_time_check_limit = 3000
        #==================================#

        self.reddit = None

    def login(self):
        self.reddit = praw.Reddit(
            client_id=self.CLIENT_ID,
            client_secret=self.CLIENT_SECRET,
            password=self.PASSWORD,
            user_agent=self.USER_AGENT,
            username=self.USERNAME)
        print("Successfully authenticated as {}".format(self.reddit.user.me()))

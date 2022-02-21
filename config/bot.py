import os
import praw
from pymysql import NULL
import requests
import requests.auth

#========[BELOW CONFIG VARS]========#
#=====[TO BE ENTERED IN HEROKU]=====#
USERNAME = os.environ['USERNAME']
PASSWORD = os.environ['PASSWORD']
CLIENT_ID = os.environ['CLIENT_ID']
CLIENT_SECRET = os.environ['CLIENT_SECRET']
DATABASE_URL = os.environ['DATABASE_URL']
PRIVATE_SUB = os.environ['PRIVATE_SUB']
# Get the reddit thread ID for the bot's log (should be in your private sub!)
BOT_LOG_POST = os.environ['BOT_LOG']

#=============[SET UP]=============#
BOT_VERSION = 'v1.3'
USER_AGENT = 'script:reddit help and news bot ' + BOT_VERSION + ' by u/' + USERNAME
# the footer text for comments from the bot
BOT_FOOTER = 'I am a bot and this was performed automatically. Got suggestions? Send a PM.'

req_timeout = 7

# time to re-check thumbnails (default: 900 sec)
thumbnail_time_check_limit = 900
# time to refresh the token (default: 3000 sec)
bearer_token_time_check_limit = 3000
#==================================#

reddit = NULL


class Login:
    def __init__(self):
        global reddit
        reddit = praw.Reddit(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            password=PASSWORD,
            user_agent=USER_AGENT,
            username=USERNAME)
        print("Successfully authenticated as {}".format(reddit.user.me()))

    def getReddit():
        return reddit


class Session:
    def __init__(self):
        global session, ua_header, client_auth, post_data, session_header
        session = requests.Session()
        ua_header = {
            'User-Agent': 'Reddit session bot for api/info by u/' + USERNAME}
        client_auth = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
        post_data = {"grant_type": "password",
                     "username": USERNAME, "password": PASSWORD}
        session_header = ''
        c_obj = requests.cookies.create_cookie(domain=".pso2.com", name="pso2-age.verification",
                                               path="/", secure="False", value="true")  # create cookies for PSO2 age gate
        session.cookies.set_cookie(c_obj)

    def getPage(url):
        try:
            page = session.get(url, headers=session_header,
                               timeout=req_timeout)
            return page
        except requests.exceptions.ReadTimeout as e:
            print('ReadTimeout occurred with site ' +
                  str(url) + '... continuing...')
            return False
        except requests.exceptions.ConnectTimeout as e:
            print('ConnectTimeout occurred with site ' +
                  str(url) + '... continuing...')
            return False

    def refreshBearerToken():
        global session, session_header
        print('<!> Refreshing bearer token now...')
        session_response = session.post(
            "https://www.reddit.com/api/v1/access_token", auth=client_auth, data=post_data, headers=ua_header)
        session_header = {'Authorization': 'bearer ' + session_response.json(
        )['access_token'], 'User-Agent': 'Reddit session bot for api/info by u/' + USERNAME}

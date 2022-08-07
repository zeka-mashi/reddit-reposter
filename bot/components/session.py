import aiohttp
import asyncio


class Session:
    def __init__(self, bot):
        self.bot = bot
        self.ua_header = {
            'User-Agent': 'Reddit session bot for api/info by u/' + self.bot.USERNAME}
        self.client_auth = aiohttp.BasicAuth(
            self.bot.CLIENT_ID, self.bot.CLIENT_SECRET)
        self.post_data = {"grant_type": "password",
                          "username": self.bot.USERNAME, "password": self.bot.PASSWORD}
        self.session_header = ''

    async def getPage(self, url):
        async with aiohttp.ClientSession() as session:
            timeout = aiohttp.ClientTimeout(total=self.bot.req_timeout)
            async with session.get(url, headers=self.session_header, timeout=timeout) as resp:
                if resp.status == 200:
                    return await resp.text()
                else:
                    err_message = await resp.text()
                    print(resp.status, err_message)
                    return False

    async def refreshBearerToken(self):
        print('<!> Refreshing bearer token now...')
        async with aiohttp.ClientSession() as session:
            async with session.post('https://www.reddit.com/api/v1/access_token', auth=self.client_auth, data=self.post_data, headers=self.ua_header) as resp:
                if resp.status == 200:
                    response = await resp.json()
                    print(response)
                    self.session_header = {
                        'Authorization': 'bearer ' + response['access_token'], 'User-Agent': 'Reddit session bot for api/info by u/' + self.bot.USERNAME}
                else:
                    err_message = await resp.text()
                    print(resp.status, err_message)

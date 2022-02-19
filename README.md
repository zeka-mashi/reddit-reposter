# Reddit Reposter Bot

A python bot that scans and scrapes new content on sites to post as link submissions on Reddit.

## Features

- Automatically scans and scrapes new content
- Built-in Reddit api/rescrape function with chromedriver
- Easily deployable to Heroku and other services
- Additionally posts text snippets for certain supported content

## Tech Stack

Python, PostgreSQL, Heroku

Libraries: PRAW, psycopg2, beautifulsoup, selenium, requests, etc.

## To-Do

- Modularize the bot to allow new sites to be added with ease

## Deployment

To deploy this project to Heroku:

#### Prerequisites
Heroku account with active dyno

#### Instructions
Clone this repository.

Create a new Heroku app and deploy via GitHub (under Deployment method) with automatic deploys.

Create a dyno worker of `python reddit-bot.py`

Configure the app framework with the following Buildpacks:    
- Python: heroku/python    
- Google Chrome: https://buildpack-registry.s3.amazonaws.com/buildpacks/heroku/google-chrome.tgz    
- chromedriver: https://buildpack-registry.s3.amazonaws.com/buildpacks/heroku/chromedriver.tgz    

Add your config vars:
- CLIENT_ID - your Reddit bot's client ID
- CLIENT_SECRET - your Reddit bot's secret
- DATABASE_URL - the PostgreSQL DB URL
- USERNAME - your Reddit account username
- PASSWORD - your Reddit account password
- PRIVATE_SUB - the subreddit (being private is optional) that the bot will fallback to post
- BOT_LOG - the thread ID that the bot will log its activities to (Note: Reddit threads automatically lock after 6 months, so this will need to be updated every 6 months with a new thread ID)

The below config vars are for the chromedriver:   
- GOOGLE_CHROME_BIN: /app/.apt/opt/google/chrome/chrome    
- GOOGLE_CHROME_SHIM: /app/.apt/opt/google/chrome/chrome

## License

[GNU General Public License v3.0](https://github.com/zeka-mashi/reddit-reposter/blob/main/LICENSE)
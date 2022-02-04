# Reddit Reposter Bot

A python bot that scans and scrapes new content on sites to post as link submissions on Reddit.

## Features

- Automatically scans and scrapes new content
- Built-in Reddit api/rescrape function with chromedriver
- Easily deployable to Heroku and other services

## Tech Stack

Python, PostgreSQL, Heroku

Libraries: PRAW, psycopg2, beautifulsoup, selenium, requests, etc.
## Deployment

To deploy this project to Heroku:

#### Prerequisites
Heroku account with active dyno

#### Instructions
Clone this repository.

Create a new Heroku app and deploy via GitHub (under Deployment method) with automatic deploys.

Create a dyno worker of `python reddit-bot.py`

Config the app framework with the following Buildpacks:    
Python: heroku/python    
Google Chrome: https://buildpack-registry.s3.amazonaws.com/buildpacks/heroku/google-chrome.tgz    
chromedriver: https://buildpack-registry.s3.amazonaws.com/buildpacks/heroku/chromedriver.tgz    

Add your config vars: CLIENT_ID, CLIENT_SECRET, DATABASE_URL, USERNAME, PASSWORD

Additional config vars for the chromedriver:   
GOOGLE_CHROME_BIN: /app/.apt/opt/google/chrome/chrome    
GOOGLE_CHROME_SHIM: /app/.apt/opt/google/chrome/chrome

## License

[GNU General Public License v3.0](https://github.com/zeka-mashi/reddit-reposter/blob/main/LICENSE)
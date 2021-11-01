import twitter
from time import sleep
import telegram
import html
from app import config
import re
from pprint import pprint
from datetime import datetime, date, timedelta
# import datetime
import urllib.request, urllib.error, urllib.parse
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as wait
from oddschecker import Oddschecker

print('Starting')


def process_tweet(tweet):
    bet_list = []
    print(str(tweet['id']) + ' - ' + tweet['created_at'])

    if len(tweet['user_mentions']) == 0:
        message = tweet['full_text'].splitlines()
 
        for line in message:
            regex=re.compile('^(([0-1]{0,1}[0-9]( )?[AaPp][Mm])|(([0]?[1-9]|1[0-2])(:|\.)[0-5][0-9]( )?(AM|am|aM|Am|PM|pm|pM|Pm))|(([0]?[0-9]|1[0-9]|2[0-3])(:|\.)[0-5][0-9]))')
            
            if re.match(regex, line.strip()): # line starts with the time
                bet_list.append(line)

        if len(bet_list) > 0:
            try:
                o = Oddschecker()
                bets = process_bets(o, bet_list)
                
                twitter_text = html.unescape(tweet['full_text'])
                send_olly_message(twitter_text)
                take_screenshots(o, bets)
            finally:
                o.close()


def take_screenshots(o, bets):
    try:
        for bet in bets:
            rdt = bet[6]
            rtime = rdt.strftime("%H:%M")
            rdate = rdt.strftime("%Y-%m-%d")
            o.url = 'https://www.oddschecker.com/horse-racing/' + rdate + '-' + bet[0] + '/' + rtime + '/winner'

            file_name = o.get_screenshot(bet)
            send_screenshot_message(file_name)
    except Exception as e:
        print(str(e))
        print(bet)
        print(o.url)


def process_bets(o, bet_list):
    race_info = get_race_info(o)

    olly_data = []

    for line in bet_list:
        line = line.split(' - ')
        ep = ''

        rtime = line[0].replace('.',':')
        if ' ' in rtime.strip():
            rtime = rtime.split(' ')[0]

        bet_text = line[1]
        ep_search = line[1].split('(')
        if len(ep_search) > 1:
            bet_text = ep_search[0].strip()
            ep = ep_search[1].strip()[0]          

        split_bet = bet_text.split(',')

        for bet in split_bet:
            split_bet = bet.strip().split(' ')
            horse = ' '.join(split_bet[:-1])
            odds = split_bet[-1]

            type = evaluate_type(odds.split('/')[0],odds.split('/')[1])
            course, race_dt = lookup_race_course(rtime, race_info)

            olly_bet = []
            olly_bet.append(course)
            olly_bet.append(rtime)
            olly_bet.append(horse.title())
            olly_bet.append(ep)
            olly_bet.append(type)
            olly_bet.append(odds)
            olly_bet.append(race_dt)

            olly_data.append(olly_bet)
    return olly_data


def get_race_info(o):
    race_info = o.get_race_tracks_and_timings()
    race_info = filter_race_info(race_info)
    return(race_info)


def filter_race_info(race_info):
    dat = date.today() + timedelta(days=2)
    dat = dat.strftime("%Y-%m-%d %H:%M:%S")
    dat = datetime.strptime(dat, "%Y-%m-%d %H:%M:%S")

    filtered_info = {}

    for k,v in race_info.items():
        filtered_values = []
        for race_date_time in v:
            tm = datetime.strptime(race_date_time, "%Y-%m-%d %H:%M:%S")
            if (tm > datetime.now()) and (tm < dat):
                filtered_values.append(tm)

            filtered_info[k] = filtered_values

    return filtered_info


def evaluate_type(odds1, odds2):
    type = 'EW'
    dec_odds = int(odds1)/int(odds2)
    if dec_odds <= 5:
        type = 'WIN'
    return type


def get_24_hour_time(rtime):
    hours = rtime.split(':')

    if int(hours[0]) in [1,2,3,4,5,6,7,8,9]:
        new_hours = str(int(hours[0]) + 12)
        rtime = new_hours + ':' + hours[1]

    new_tm = datetime.strptime(rtime, "%H:%M")

    return new_tm


def lookup_race_course(rtime, race_info):
    rtime = get_24_hour_time(rtime)
    k = None
    for k,v in race_info.items():
        for tm in v:
            # print(tm.time())
            if rtime.time() == tm.time():
                return k, tm 
    return k, rtime


def send_olly_message(message):
    sleep(1)
    bot = telegram.Bot(token=config.TELEGRAM_BOT_API_KEY)

    # Olly's Tips
    try:
        # Ollys Tips
        bot.send_message(chat_id='-1001517051837', text=message,
                        parse_mode=telegram.ParseMode.MARKDOWN)
        # Spanners Playground
        # bot.send_message(chat_id='-1001456379435', text=message,
        #                 parse_mode=telegram.ParseMode.MARKDOWN)
    except Exception as e:
        bot.send_message(chat_id='-1001517051837', text=message,
                         parse_mode=telegram.ParseMode.HTML)
        print(e)


def send_screenshot_message(file):
    sleep(1)
    bot = telegram.Bot(token=config.TELEGRAM_BOT_API_KEY)

    # Olly's Tips
    try:
        # Ollys Tips
        bot.send_photo(chat_id='-1001517051837', photo=open(file, 'rb'))
        # Spanners Playground
        # bot.send_photo(chat_id='-1001456379435', photo=open(file, 'rb'))
    except Exception as e:
        print('Error sending screenshot')
        print(e)


api = twitter.Api(consumer_key=config.API_KEY,
                  consumer_secret=config.API_SECRET,
                  access_token_key=config.ACCESS_TOKEN,
                  access_token_secret=config.ACCESS_TOKEN_SECRET,
                  cache=None,
                  tweet_mode='extended')

# try:
while True:
    try:
        ro = api.GetUserTimeline(screen_name="@Raceolly", count=3, trim_user=True, exclude_replies=True, include_rts=False)

        r_tweets = [i.AsDict() for i in ro]

        for r_tweet in reversed(r_tweets):
            # print(r_tweet)
            with open('r_ids.txt', 'r') as f:
                last_id = int(f.read())

            if r_tweet['id'] > last_id:
                r_results_list = process_tweet(r_tweet)

                with open('r_ids.txt', 'w') as f:
                    f.write(str(r_tweet['id']))

        # print('Sleeping at ' + strftime("%Y-%m-%d %H:%M:%S", gmtime()))
        sleep(10)

    except KeyboardInterrupt:
        print('Keyboard interrupt')
        break
    except Exception as e:
        sleep(2)
        print('General Exception', flush=True)
        print(str(e))
        print(r_tweet)
        continue

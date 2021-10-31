from os import remove
import twitter
from time import sleep
import telegram
import html
from app import config
import re
from pprint import pprint
import cloudscraper
from datetime import datetime, date, timedelta
# import datetime
import urllib.request, urllib.error, urllib.parse
import time
from selenium import webdriver
import undetected_chromedriver as uc
from webdriver_manager.chrome import ChromeDriverManager
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
    # pprint(tweet['full_text'])
    # pprint(tweet)

    if len(tweet['user_mentions']) == 0:
        message = tweet['full_text'].splitlines()
 
        for line in message:
            line = remove_URL(line)
            regex=re.compile('(([0-1]{0,1}[0-9]( )?[AaPp][Mm])|(([0]?[1-9]|1[0-2])(:|\.)[0-5][0-9]( )?(AM|am|aM|Am|PM|pm|pM|Pm))|(([0]?[0-9]|1[0-9]|2[0-3])(:|\.)[0-5][0-9]))')
            match = re.search(regex, line.strip())

            if match: # line contains the time
                bet_list.append(match.group(1))

        if len(bet_list) > 0:
            bets = process_bets(bet_list)

            twitter_text = html.unescape(tweet['full_text'])

            send_olly_message(twitter_text)
            take_screenshots(bets)
        else:
            try:
                twitter_text = html.unescape(tweet['full_text'])
                send_olly_message(twitter_text)
            except:
                send_olly_message('Unable to send tweet')
                print(tweet['full_text'])


def take_screenshots(bets):
    try:
        url = 'https://www.oddschecker.com/horse-racing'
        # options = webdriver.ChromeOptions()
        
        # # options.add_argument('--width=1024')
        # # options.add_argument('--height=768')
        # options.headless = True
        # # driver = webdriver.Chrome(options=options)
        # driver = webdriver.Chrome(executable_path=ChromeDriverManager().install(), options=options)
        # driver.execute_script("document.body.style.zoom='80%'")
        # driver.set_window_size(960, 240)
        # driver.get(url)
        # # driver.save_screenshot('test.png')

        # WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="promo-modal"]/div[1]/div/span'))).click()
        # try:
        #     WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CLASS_NAME, '_3mDe0u'))).click()
        # except:
        #     pass

        # from Screenshot import Screenshot_Clipping

        options = webdriver.ChromeOptions() 

        options.headless = True
        options.add_argument("start-maximized")
        options.add_argument("--window-size=1500x3800")
        driver = webdriver.Chrome(executable_path=ChromeDriverManager().install(), options=options)
        driver.execute_script("document.body.style.zoom='20%'")
        driver.maximize_window()
        # driver.set_window_size(960, 240)
        # options.add_argument("start-maximized")
        driver = uc.Chrome(options=options)
        driver.get(url)

        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="promo-modal"]/div[1]/div/span'))).click()
        try:
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CLASS_NAME, '_3mDe0u'))).click()
        except:
            pass

        for bet in bets:
            rdt = bet[2]
            rtime = rdt.strftime("%H:%M")
            rdate = rdt.strftime("%Y-%m-%d")
            url = 'https://www.oddschecker.com/horse-racing/' + rdate + '-' + bet[0] + '/' + rtime + '/winner'

            driver.get(url)
            sleep(2)
            if driver.current_url == 'https://www.oddschecker.com/horse-racing':
                # look ahead a day (date needs to be in url)
                tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d-")
                url = 'https://www.oddschecker.com/horse-racing/' + tomorrow + '-' + bet[0] + '/' + rtime + '/winner'
                driver.get(url)

            total_width = driver.execute_script("return document.body.offsetWidth")
            total_height = driver.execute_script("return document.body.scrollHeight")
            driver.set_window_size(total_width + 250, total_height/2)
            screenshot = 'screenshots/' + bet[0] + '_' + bet[1].replace('.', '_') + '.png'
            driver.save_screenshot(screenshot)
            send_screenshot_message(screenshot)
    except Exception as e:
        print(str(e))
        print(bet)
        print(url)

    driver.quit()


def process_bets(bet_list):
    race_info = get_race_info()
    olly_data = []

    for rtime in bet_list:
        course, race_dt = lookup_race_course(rtime, race_info)

        olly_bet = []
        olly_bet.append(course)
        olly_bet.append(rtime)
        olly_bet.append(race_dt)

        olly_data.append(olly_bet)
    return olly_data


def get_race_info():
    o = Oddschecker('https://www.oddschecker.com/horse-racing')

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


def remove_URL(text):
    """Remove URLs from a text string"""
    return re.sub(r"http\S+", "", text)


def evaluate_type(odds1, odds2):
    type = 'EW'
    dec_odds = int(odds1)/int(odds2)
    if dec_odds <= 5:
        type = 'WIN'
    return type


def get_24_hour_time(rtime):
    rtime = rtime.replace('.', ':')
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
        # ro = api.GetUserTimeline(screen_name="@betracingnation", count=10, trim_user=True, exclude_replies=True, include_rts=False)

        r_tweets = [i.AsDict() for i in ro]

        for r_tweet in reversed(r_tweets):
            with open('r_ids.txt', 'r') as f:
                last_id = int(f.read())

            if r_tweet['id'] > last_id:
                with open("tweets.txt", 'a') as file_object:
                    file_object.write(r_tweet['created_at'] + ' - ' + r_tweet['id_str'] + ' - ' + r_tweet['full_text'].replace('\n', ' ') + '\n')

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
        with open('r_ids.txt', 'w') as f:
            f.write(str(r_tweet['id']))
        continue

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


def process_text(text):
    bet_list = text.split('\n')
    bet_list = [x for x in bet_list if x]
    time_list = []

    for bet in bet_list:
        time_list.append(bet.split(' ')[0])

    bets = process_bets(time_list)

    send_olly_message(text)
    take_screenshots(bets)


def take_screenshots(bets):
    try:
        url = 'https://www.oddschecker.com/horse-racing'

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
            screenshot = 'man_sshots/' + bet[0] + '_' + bet[1].replace('.', '_') + '.png'
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

txt = """
1.20 - Brelan D'As 12/1
2.45 - Frero Banbou 4/1
3.40 - Haafapiece 7/1
"""

process_text(txt)

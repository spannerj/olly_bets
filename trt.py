import twitter
from time import sleep
import telegram
import html
from app import config
# from time import gmtime, strftime
from pprint import pprint
import re

print('Starting')


def process_tweet(tweet, account):
    print(account + str(tweet['id']) + ' - ' + tweet['created_at'])
    if 'retweet_count' not in tweet and len(tweet['user_mentions']) == 0:
        pprint(tweet)
        if 'media' in tweet:
            regex = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            get = re.compile(regex, re.IGNORECASE | re.DOTALL)
            text = get.sub('', tweet['full_text'])
            message = tweet['media'][0]['media_url'] + '\n\n' + text
        else:
            message = tweet['full_text']

        if 'quoted_status' in tweet:
            regex = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            get = re.compile(regex, re.IGNORECASE | re.DOTALL)
            message = get.sub('', message)
            message = message + '\n\n' + '```' + tweet['quoted_status']['full_text'] + '```'

            twitter_text = account + html.unescape(message)
            send_message(twitter_text)


def send_message(message):
    sleep(1)
    bot = telegram.Bot(token=config.TELEGRAM_BOT_API_KEY)

    # LR Jack's Tips
    bot.send_message(chat_id='-1001190331415', text=message,
                     parse_mode=telegram.ParseMode.MARKDOWN)

    # # Spanners Playground
    # bot.send_message(chat_id='-1001456379435', text=message,
    #                  parse_mode=telegram.ParseMode.MARKDOWN)


api = twitter.Api(consumer_key=config.API_KEY,
                  consumer_secret=config.API_SECRET,
                  access_token_key=config.ACCESS_TOKEN,
                  access_token_secret=config.ACCESS_TOKEN_SECRET,
                  cache=None,
                  tweet_mode='extended')

# try:
while True:
    try:
        # pt = api.GetUserTimeline(screen_name="@TopRacingTipsRP", count=200)
        tt = api.GetUserTimeline(screen_name="@spannerjago", count=1)
        pt = api.GetUserTimeline(screen_name="@TRTPremium", count=3)
        gt = api.GetUserTimeline(screen_name="@TRTGold", count=3)

        p_tweets = [i.AsDict() for i in pt]
        g_tweets = [i.AsDict() for i in gt]
        t_tweets = [i.AsDict() for i in tt]

        for p_tweet in reversed(p_tweets):
            with open('p_ids.txt', 'r') as f:
                last_id = int(f.read())

            if p_tweet['id'] > last_id:
                process_tweet(p_tweet, 'PREMIUM - ')

                with open('p_ids.txt', 'w') as f:
                    f.write(str(p_tweet['id']))

        for g_tweet in reversed(g_tweets):
            with open('g_ids.txt', 'r') as f:
                last_id = int(f.read())

            if g_tweet['id'] > last_id:
                g_results_list = process_tweet(g_tweet, 'GOLD - ')

                with open('g_ids.txt', 'w') as f:
                    f.write(str(g_tweet['id']))

        for t_tweet in reversed(t_tweets):
            with open('t_ids.txt', 'r') as f:
                last_id = int(f.read())

            if 'media' in t_tweet:
                get = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',re.IGNORECASE|re.DOTALL)
                text = get.sub('', t_tweet['full_text'])
                tweet = t_tweet['media'][0]['media_url'] + '\n\n' + text
            else:
                tweet = t_tweet['full_text']

            if t_tweet['id'] > last_id:
                print('TEST - ' + str(t_tweet['id']) + ' - ' + t_tweet['created_at'])
                token = config.TELEGRAM_BOT_API_KEY
                bot = telegram.Bot(token=token)
                # Spanners Playground
                bot.send_message(chat_id='-1001456379435',
                                 text=tweet,
                                 parse_mode=telegram.ParseMode.MARKDOWN)

                with open('t_ids.txt', 'w') as f:
                    f.write(str(t_tweet['id']))

        # print('Sleeping at ' + strftime("%Y-%m-%d %H:%M:%S", gmtime()))
        sleep(10)
    except KeyboardInterrupt:
        print('Keyboard interrupt')
        break
    except Exception as e:
        sleep(2)
        print('General Exception', flush=True)
        print(e)
        continue

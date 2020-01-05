# -*- coding: utf-8 -*-

from tweepy import OAuthHandler
from tweepy import Stream
import time
from app import config
from app.listener import Listener
from http.client import IncompleteRead

if __name__ == '__main__':

    listener = Listener()
    auth = OAuthHandler(config.API_KEY, config.API_SECRET)
    auth.set_access_token(config.ACCESS_TOKEN, config.ACCESS_TOKEN_SECRET)

    while True:
        try:
            stream = Stream(auth, listener)
            print('start streaming', flush=True)
            stream.filter(follow=['790318671608545280',
                                  '865166107522605058'])  # Premium/Gold
            # stream.filter(follow=['32771325'])  # Stupid count tweet a minute
        except IncompleteRead:
            print('Incomplete Read', flush=True)
            time.sleep(1)
            continue
        except KeyboardInterrupt:
            print('Keyboard interrupt')
            stream.disconnect()
            break
        except Exception as e:
            time.sleep(1)
            print('General Exception', flush=True)
            print(e)
            continue

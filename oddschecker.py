from collections import defaultdict, namedtuple
from operator import attrgetter

import requests
import cloudscraper
import time
from bs4 import BeautifulSoup, Comment


class Oddschecker:
    def __init__(self, url):
        self.url = url
        self._soup = None

    def get_prices(self, target_books=None):
        self._get_soup()

        all_books = self._get_books()

        if not target_books:
            target_books = all_books

        Book = namedtuple("Book", "name price")
        prices = defaultdict(list)

        for row in self._get_table_body():
            col = 0
            for elem in row:
                if not self._is_price(elem):
                    continue

                # price = self._get_decimal_odds(elem)
                price = self._get_fractional_odds(elem)
                book_name = all_books[col]
                selection = row["data-bname"]

                if self._price_open(elem) and book_name in target_books:
                    prices[selection].append(Book(book_name, price))

                col += 1

        return self._sorted(prices)

    def get_race_tracks_and_timings(self):
        self._get_soup()

        max_retries = 10
        retry_delay = 2
        n = 1
        ready = 0
        while n < max_retries:
            todays_divs = self._soup.find_all('div', attrs = {'class' : 'show-times'})

            objs = []
            for div in todays_divs:
                objs += div.find_all(['div', 'span'], attrs = {'class' : ['race-details', 'flag-wrap']})

            race_tracks = {}

            total = len(objs)
            for index, obj in enumerate(objs):
                if index == total - 1:
                    continue
                if index % 2 == 0:
                    country = objs[index + 1].text.strip()
                    if country in ('UK', 'IRE', 'Northern Ireland'):
                        try:
                            key = self._clean_name(obj.find('a', attrs = {'class' : 'venue'} ).text.strip())
                            val = obj.find_all('span', attrs = {'class' : 'time-to-race'})
                            race_times = []
                            for race in val:
                                race_times.append(race['data-time'])

                            if key in race_tracks:
                                race_tracks[key] = race_tracks[key] + race_times
                            else:
                                race_tracks[key] = race_times
                        except Exception as e:
                            print(str(e))
                            continue
            if len(race_tracks) > 0:
                return race_tracks
            else:
                print('No courses found so retry')
                time.sleep(retry_delay + n)
                self._get_soup()    

            n = n + 1

        print('No courses found and max retries completed')
        return race_tracks


    def _get_books(self):
        books = []
        for row in self._get_table_head():
            elem = row.find("a")
            if elem and elem.has_attr("title"):
                books.append(elem["title"])
        return books

    def _get_soup(self):
        scraper = cloudscraper.create_scraper()
        r = scraper.get(self.url)
        # print(r.status_code)
        # time.sleep(2)


        # max_retries = 3
        # retry_delay = 5
        # n = 1
        # ready = 0
        # scraper = cloudscraper.create_scraper()
        # while n < max_retries:
        #     try:
        #         r = scraper.get(self.url)
        #         print(r.ok)
        #         if r.ok:
        #             ready = 1
        #             break
        #     except requests.exceptions.RequestException:
        #         print("Website not availabe...")

        #     n += 1
        #     time.sleep(retry_delay)

        # if ready != 1:
        #     print("Problem")
        # else:
        #     print("All good")

        self._soup = BeautifulSoup(r.text, "html.parser")

    def _get_table_head(self):
        return self._soup.find("tr", {"class": "eventTableHeader"})

    def _get_table_body(self):
        table_body = self._soup.find("tbody", id="t1")
        for element in table_body(text=lambda it: isinstance(it, Comment)):
            element.extract()
        return table_body

    @staticmethod
    def _get_decimal_odds(elem):
        return float(elem["data-odig"])

    @staticmethod
    def _get_fractional_odds(elem):
        if '/' in elem["data-o"]:
            return elem["data-o"]
        else:
            return elem["data-o"] + '/1'

    @staticmethod
    def _is_price(elem):
        return "data-odig" in elem.attrs

    @staticmethod
    def _clean_name(val):
    	return val.lower().replace(' ','-')

    @staticmethod
    def _price_open(elem):
        return elem.findChild()

    @staticmethod
    def _sorted(prices):
        for market in prices:
            prices[market] = sorted(
                prices[market], key=attrgetter("price"), reverse=True
            )
        return prices

from collections import defaultdict, namedtuple
from operator import attrgetter

import requests
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
                if country in ('UK', 'IRE'):
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
        return race_tracks

    def _get_books(self):
        books = []
        for row in self._get_table_head():
            elem = row.find("a")
            if elem and elem.has_attr("title"):
                books.append(elem["title"])
        return books

    def _get_soup(self):
        r = requests.get(
            self.url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/72.0.3626.121 Safari/537.36"
            },
        )
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

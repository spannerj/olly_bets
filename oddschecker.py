from collections import defaultdict, namedtuple
from operator import attrgetter

from time import sleep
import datetime
import undetected_chromedriver as uc
from selenium import webdriver
from bs4 import Comment, BeautifulSoup as bs
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


class Oddschecker:
    def __init__(self, url='https://www.oddschecker.com/'):
        options = webdriver.ChromeOptions() 
        options.add_argument("--window-size=1500x3800")
        options.headless = True
        self.driver = uc.Chrome(options=options)
        self.driver.execute_script("document.body.style.zoom='50%'")
        self.url = url
        self.driver.get(self.url)
        WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//div[text()='OK']"))).click()
        WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="promo-modal"]/div[1]/div/span'))).click()
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
        self.url = 'https://www.oddschecker.com/horse-racing'
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
        self.driver.get(self.url)
        self._soup = bs(self.driver.page_source, 'html.parser')

    def close(self):
        self.driver.close()
        self.driver.quit()

    def get_screenshot(self, bet):
        split_url = self.url.split('/')
        file_name = 'screenshots/' + split_url[4] + split_url[5] + '.png'
        rtime = bet[6].strftime("%H:%M")

        try:
            self.driver.get(self.url)
            sleep(2)

            if self.driver.current_url == 'https://www.oddschecker.com/horse-racing':
                # look ahead a day (date needs to be in url)
                tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d-")
                url = 'https://www.oddschecker.com/horse-racing/' + tomorrow + '-' + bet[0] + '/' + rtime + '/winner'
                self.driver.get(url)

            element = WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="betting-odds"]')))
            element.screenshot(file_name)

            return file_name
        except Exception as e:
            print(str(e))
            self.driver.save_screenshot('error.png')

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

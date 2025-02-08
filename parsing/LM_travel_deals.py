import re

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import locale
from config import HEADERS

# url = 'https://kamernet.nl/huren/huurwoningen-enschede?searchview=1&maxRent=8&minSize=2&radius=4&pageNo=1&sort=1'
# url = 'https://www.accuweather.com/en/nl/enschede/250111/weather-forecast/250111'
# return self.soup.find('div', class_='temp-container').find('div', class_='temp').text

class LM_Parser:
    def __init__(self, max_price, min_review, dep_in=3, num_review=200, dep_loc=None, tour_len=None, headers=None):
        self.url = 'https://www.corendon.nl/vakanties/lastminutes?ppage='
        self.max_price = max_price
        self.min_review = min_review
        self.dep_in = dep_in
        self.num_review = num_review
        self.dep_loc = dep_loc
        self.headers = None

    def _safe_find(self, parent, *args):
        """Upgraded version of the bs find, which doesn't throw an error if it cannot find something"""
        for attribute in args:
            parent = parent.find(attribute[0], class_=attribute[1]) if parent else None
        return parent
    def _days_left(self, dep):
        locale.setlocale(locale.LC_TIME, "Dutch_Netherlands")        # needed to translate Dutch months
        data = datetime.strptime(dep.split(" (")[0], "%d %b %Y")
        return int((data - datetime.now()).days) + 1

    def set_the_hottest(self, max_price, min_review, num_review=330, dep_in=1, tour_len=None, destination=None):
        self.max_price_hot = max_price
        self.min_review_hot = min_review
        self.num_review_hot = num_review
        self.dep_in_hot = dep_in
        self.tour_len_hot = tour_len
        self.destination_hot = destination


    def parse(self):

        counter = 1
        while counter>0:
            # url = self.url+str(counter)
            # req = requests.get(url, headers=self.headers)
            # src = req.text
            with open('../data_storage/data/amazon.html') as file:
                src = file.read()

            soup = BeautifulSoup(src, 'lxml')

            all_tours = soup.find_all('article', class_='cor-sr-item')
            for tour in all_tours:
                tour_info = tour.find('div', class_="cor-sr-item__main row")
                review = self._safe_find(tour_info, ('div', 'cor-sr-item__usp-reviews col-3of8'), ('div', 'cor-reviews-statistics__summary cor-reviews-statistics__ref'), ('div', 'cor-reviews-statistics__score'))
                review = str(review.text).strip() if review else '0,0'
                review_num = self._safe_find(tour_info,  ('div', 'cor-sr-item__usp-reviews col-3of8'), ('div', 'cor-reviews-statistics__summary cor-reviews-statistics__ref'), ('div', 'cor-reviews-statistics__details'), ('div', ''))
                review_num = str(review_num.text).strip().replace('beoordelingen', 'reviews') if review_num else '0 reviews'
                price = self._safe_find(tour_info, ('div', re.compile('cor-sr-item__price col-2of8')), ('div', 'cor-price-element'), ('span', '')).text
                extra_info = self._safe_find(tour_info, ('div', re.compile('cor-sr-item__price col-2of8')), ('header', ''))
                departure, tour_len, dep_location =[i.strip() for i in extra_info.text.split('\n') if i.strip()!='']
                dep_in = self._days_left(departure)
                tour_len = tour_len[0] + ' days'
                dep_location = dep_location.split()[1]
                if int(price) > self.max_price:
                    counter = -1
                    break
                # print(tour)
                # print(review)
                # print(review_num)
                # print(price)
                print(dep_in, tour_len, dep_location)
                print('------------------------------------------------------------------------------------')
            # print(all_tours)
            break
            counter+=1



    def save_page(self, dir='.'):
        # print(self.req.text)
        with open(dir+'/amazon.html', 'w', encoding='utf-8') as file:
            file.write(self.req.text)

    def get_links(self):
        links = [div.find('a').get('href') for div in self.soup.find_all("div", class_="h1 cor-heading--branded")]
        # print(links)
        return "\n".join([link.split('#[filters]')[0] for link in links])

    def test(self):
        pass

if __name__ == '__main__':
    parser = LM_Parser(400, 20, headers=HEADERS)
    parser.parse()
    # print(parser.get_links())
    # parser.save_page('../data_storage/data')
    # print(parser.test())

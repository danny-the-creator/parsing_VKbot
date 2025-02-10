import re
import itertools

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import locale
from googletrans import Translator

from config import HEADERS

# url = 'https://kamernet.nl/huren/huurwoningen-enschede?searchview=1&maxRent=8&minSize=2&radius=4&pageNo=1&sort=1'
# url = 'https://www.accuweather.com/en/nl/enschede/250111/weather-forecast/250111'
# return self.soup.find('div', class_='temp-container').find('div', class_='temp').text

class LM_Parser:
    def __init__(self, max_price, min_review, num_review=200, dep_in=3, tour_len=0, dep_loc=None):
        self.url = 'https://www.corendon.nl/vakanties/lastminutes?ppag='
        self.max_price = max_price
        self.min_review = min_review
        self.dep_in = dep_in
        self.num_review = num_review
        self.tour_len = tour_len
        self.dep_loc = dep_loc
        self.headers = None
        self.directory = '.'
        self.translator = None
        self._hottest_set = False


    def _save_html(self, src, index=''):
        with open(f"{self.directory}/lm_tours_page{index}.html", "w", encoding="utf-8") as file:
            file.write(src)


    def _safe_find(self, parent, *args):
        """Upgraded version of the bs find, which doesn't throw an error if it cannot find something"""
        for attribute in args:
            if parent is None:
                return None
            parent = parent.find(attribute[0], class_=attribute[1])
        return parent
    def _update_data(self, deal):
        url = deal.get('link')
        req = requests.get(url, headers=self.headers)
        src = req.text
        soup = BeautifulSoup(src, 'lxml')

        flight = self._safe_find(soup, ('div', 'cor-acco-summary__fact-icons'), ('i', 'cor-icon icon-plane-up-right'))
        flight = flight.find_parent().find('span').text.strip() if flight else '**:**'
        weather = self._safe_find(soup, ('div', 'cor-acco-summary__fact-icons'), ('i', 'cor-icon icon-sun'))
        weather = weather.find_parent().find('span').text.split()[1] if weather else '?°C'
        # print(flight, weather)
        description = soup.find('div', class_='cor-acco-short-description')
        description = self._safe_find(description, ('p','')) if self._safe_find(description, ('p','')) else description
        description = self._translate(description.text.strip(), 'nl', 'en') if description else "<not_defined>"
        # print(description)

        location = soup.find('div', class_='cor-acco-info__description')
        try:
            location = location.find_all(string=re.compile(r"Ligging"), limit=2)[-1].find_parent().find_next_sibling().text
            location = self._translate('\n'.join([f"- {point}" for point in location.strip().split('\n')]), 'nl', 'en')
        except (AttributeError, IndexError) as e:
            location = "<not_defined>"
        # print(location)

        service = soup.find('div', class_='cor-acco-info__description')
        try:
            service = service.find_all(string=re.compile(r"Verzorging"), limit=2)[-1].find_parent().find_next_sibling().text
            service = self._translate('\n'.join([f"- {point}" for point in service.strip().split('\n') if len(point.strip())!=0]), 'nl', 'en')
        except (AttributeError, IndexError) as e:
            service = "<not_defined>"
        # print(service)

        deal['flight'] = flight
        deal['weather'] = weather
        deal['location'] = location
        deal['service'] = service
        deal['description'] = description

    def _days_left(self, dep):
        locale.setlocale(locale.LC_TIME, "Dutch_Netherlands")        # needed to translate Dutch months
        data = datetime.strptime(dep.split(" (")[0], "%d %b %Y")
        return int((data - datetime.now()).days) + 1
    def _translate(self, text, src, dest):
        if not self.translator:
            self.translator = Translator()
        try:
            return self.translator.translate(text, src=src, dest=dest).text
        except AttributeError as e:
            print(e)
            return text

    def set_hottest(self, max_price, min_review, num_review=330, dep_in=2, tour_len=0, destination=None, dep_loc=None):
        self.max_price_hot = max_price
        self.min_review_hot = min_review
        self.num_review_hot = num_review
        self.dep_in_hot = dep_in
        self.tour_len_hot = tour_len
        self.destination_hot = destination
        self.dep_loc_hot = dep_loc
        self._hottest_set = True

    def set_settings(self, directory, headers=None):
        self.headers = headers
        self.directory = directory

    def parse(self):
        good_deals = {}
        counter = 1
        while counter>0:
            url = self.url+str(counter)
            req = requests.get(url, headers=self.headers)
            src = req.text
            # self._save_html(src, str(counter))

            # with open(f'../data_storage/data/lm_tour_page{str(counter)}.html') as file:
            #     src = file.read()

            soup = BeautifulSoup(src, 'lxml')

            all_tours = soup.find_all('article', class_='cor-sr-item')
            if len(all_tours) == 0:
                break
            for tour in all_tours:
                tour_info = tour.find('div', class_="cor-sr-item__main row")

                review = self._safe_find(tour_info, ('div', 'cor-sr-item__usp-reviews col-3of8'), ('div', 'cor-reviews-statistics__summary cor-reviews-statistics__ref'), ('div', 'cor-reviews-statistics__score'))
                review = float(str(review.text).strip().replace(',', '.') if review else '0.0')

                review_num = self._safe_find(tour_info,  ('div', 'cor-sr-item__usp-reviews col-3of8'), ('div', 'cor-reviews-statistics__summary cor-reviews-statistics__ref'), ('div', 'cor-reviews-statistics__details'), ('div', ''))
                review_num = int(str(review_num.text).strip().replace('beoordelingen', '') if review_num else '0')

                price = self._safe_find(tour_info, ('div', re.compile('cor-sr-item__price col-2of8')), ('div', 'cor-price-element'), ('span', ''))
                price = int(price.text.strip())

                extra_info = self._safe_find(tour_info, ('div', re.compile('cor-sr-item__price col-2of8')), ('header', ''))
                departure, tour_len, dep_location =[i.strip() for i in extra_info.text.split('\n') if i.strip()!='']
                dep_in = self._days_left(departure)
                tour_len = int(tour_len[0])
                dep_location = dep_location.split()[1]

                link = self._safe_find(tour, ('header', 'row'), ('div', 'h1 cor-heading--branded'), ('a', ''))
                name = link.text.strip().replace(' ', '_')
                link = link.get('href').split("#[filters]")[0]

                country = link.split('https://www.corendon.nl/')[1].split('/', 1)[0].capitalize() # name of the country is used in the link
                hotel_type = self._safe_find(tour, ('header', 'row'), ('div', 'cor-sr-item__acco-rating'), ('span', 'h4 cor-heading--branded'))
                hotel_type = re.sub(r'\s+', '_', hotel_type.text.strip()).replace('_-_', '-')  # delete tabs, enters...
                stars = self._safe_find(tour, ('header', 'row'), ('div', 'cor-sr-item__acco-rating'), ('span', re.compile('cor-stars data-stars-')))
                stars = int(stars.get('class')[1][-2]) if stars else 0          # here we find star rating from class
                if price > self.max_price:                                        # ("data-stars-30" means 3 stars)
                    counter = -1
                    break
                if any([
                    review < self.min_review,
                    review_num < self.num_review,
                    dep_in < self.dep_in,
                    tour_len < self.tour_len,
                    self.dep_loc and dep_location not in self.dep_loc
                ]):
                    continue
                lm_tour = {
                    'name': name,
                    'stars': "★"*stars,
                    'hotel_type': hotel_type,
                    'country': country,
                    'departure': dep_location,
                    'price': price,
                    'review': review,
                    'quantity': review_num,
                    'days_left': dep_in,
                    'tour_length': tour_len,

                    'flight': None,
                    'weather': None,
                    'description': None,
                    'location': None,
                    'service': None,

                    'link': link

                }

                good_deals[name] = lm_tour

                # print("★"*stars)
                # print(hotel_type)
                # print(country)
                # print(review)
                # print(review_num)
                # print(price)
                # print(dep_in, tour_len, dep_location)
                # print(link)
                # print('------------------------------------------------------------------------------------')
            print(counter)
            counter+=1
        with open(f"{self.directory}/nice_deals.json", "w", encoding="utf-8") as file:
            json.dump(good_deals, file, indent=4, ensure_ascii=False)

    def fill_tours(self, num):
        """Fills N tours from json file with all the additional information"""
        with open(f"{self.directory}/nice_deals.json", "r", encoding="utf-8") as file:
            deals = json.load(file)
        first_deals = dict(itertools.islice(deals.items(), num))
        rest_deals = dict(itertools.islice(deals.items(), num, None))
        for deal in first_deals.values():
            if not any((
                    deal['flight'],
                    deal['weather'],
                    deal['location'],
                    deal['service'] ,
                    deal['description'])):
                self._update_data(deal)

        # print(first_deals)
        updated_deals = first_deals | rest_deals
        with open(f"{self.directory}/nice_deals.json", "w", encoding="utf-8") as file:
            json.dump(updated_deals, file, indent=4, ensure_ascii=False)

    def fill_hottest(self):
        if not self._hottest_set:
            raise AttributeError("You need to set filter for the hottest deals. Call 'set_hottest'!")
        hottest_deals = {}
        with open(f"{self.directory}/nice_deals.json", "r", encoding="utf-8") as file:
            deals = json.load(file)
        for deal in deals.values():
            if any((
                self.max_price_hot < deal['price'],
                self.tour_len_hot > deal['tour_length'],
                self.min_review_hot > deal['review'],
                self.dep_in_hot > deal['days_left'],
                self.num_review_hot > deal['quantity'],
                (self.destination_hot and deal['country'] in self.destination_hot),
                (self.dep_loc_hot and deal['departure'] in self.dep_loc_hot)
            )):
                continue
            if not any((deal['flight'], deal['weather'], deal['description'], deal['location'], deal['service'])):
                self._update_data(deal)
            hottest_deals[deal['name']] = deal

        with open(f"{self.directory}/hottest_deals.json", "w", encoding="utf-8") as file:
            json.dump(hottest_deals, file, indent=4, ensure_ascii=False)

    def prepare_message(self, num):
        with open(f"{self.directory}/hottest_deals.json", "r", encoding="utf-8") as file:
            hot_deals = json.load(file)
        hot_deals = dict(itertools.islice(hot_deals.items(), num))

        deal_str ="""My Sir, I’ve processed your request.  
Here’s the most promising option for your next adventure:  

🏨 **Accommodation:** {} ({})  
📍 **Destination:** {} — currently enjoying **{}**.  
⭐ Rated **{}/10**, based on **{} reviews**.

🛫 Your journey starts from **{}**, with **{} days** of relaxation and exploration ahead.
⏳ Attention, only {} days left. After that, this opportunity will be archived... permanently.

📌 **Location Highlights:**  
{}  

🍴 **Offered Services:**  
{}  

As always, I remain at your service. Just say the word, and the world will be min... I mean yours. 😅
"""

        hot_deal_str = "!!! ATTENTION VERY HOT DEAL 🥵🔥 !!!\n\n" + deal_str
        hot_deals_messages = [hot_deal_str.format(
            deal['name'], deal['stars'], deal['country'], deal['weather'], deal['review'], deal['quantity'],
            deal['departure'], deal['tour_length'], deal['days_left'], deal['location'], deal['service']
        ) for deal in hot_deals.values()]

        reg_deals_num = num - len(hot_deals)
        if reg_deals_num < 1:
            return hot_deals_messages
        with open(f"{self.directory}/nice_deals.json", "r", encoding="utf-8") as file:
            reg_deals = json.load(file)
        # self.fill_tours(num)          probably not needed
        rest_deals = {}
        for k, v in reg_deals.items():
            if k not in hot_deals:
                rest_deals[k] = v
                if len(rest_deals) >= reg_deals_num:
                    break
        reg_deals_messages = [deal_str.format(
            deal['name'], deal['stars'], deal['country'], deal['weather'], deal['review'], deal['quantity'],
            deal['departure'], deal['tour_length'], deal['days_left'], deal['location'], deal['service']
        ) for deal in rest_deals.values()]

        return hot_deals_messages + reg_deals_messages



    def test(self):
        pass

if __name__ == '__main__':
    parser = LM_Parser(500, -1, num_review=-1, dep_in=1)
    parser.set_settings(directory='../data_storage/data', headers=HEADERS)
    parser.set_hottest(max_price=500, min_review=8, num_review=350, dep_in=0)
    # parser.fill_hottest()
    # parser.parse()
    # parser.fill_tours(30)
    # print(len(parser.prepare_message(10)))
    # for i in parser.prepare_message(10):
    #     print(i)
    # print(parser.test())




import re
import itertools
import locale
from googletrans import Translator

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta

from config import HEADERS


class LM_Parser:
    def __init__(self, max_price, min_review, num_review=200, dep_in=3, tour_len=0, dep_loc=None):
        """Sets all the filters parameters for deals on the website"""
        self.url = 'https://www.corendon.nl/vakanties/lastminutes?ppag='    # link to the website with LM deals in netherlands
        self.max_price = max_price
        self.min_review = min_review
        self.dep_in = dep_in
        self.num_review = num_review
        self.tour_len = tour_len
        self.dep_loc = dep_loc

        # Initialize some special params needed for correct work
        self.directory = '.'
        self.headers = None
        self._translator = None
        self._hottest_set = False
        self._last_parse = None

    def set_settings(self, directory, headers=None):
        """Sets general settings"""
        self.headers = headers
        self.directory = directory

    def set_hottest(self, max_price, min_review, num_review=330, dep_in=2, tour_len=0, destination=None, dep_loc=None):
        """Sets filters for the HOTTEST deals"""
        self.max_price_hot = max_price
        self.min_review_hot = min_review
        self.num_review_hot = num_review
        self.dep_in_hot = dep_in
        self.tour_len_hot = tour_len
        self.destination_hot = destination
        self.dep_loc_hot = dep_loc
        self._hottest_set = True


    def _save_html(self, src, index=''):
        """Saves the current request (with the given index) as a html file if you have problems with internet"""
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
        """Parses the link of the deal for additional information: flight, weather, location, service, description"""

        url = deal.get('link')      # link to the website with the information regarding specific tour
        req = requests.get(url, headers=self.headers)
        src = req.text
        soup = BeautifulSoup(src, 'lxml')

        # Here all the additional information regarding a tour is calculated
        flight = self._safe_find(soup, ('div', 'cor-acco-summary__fact-icons'), ('i', 'cor-icon icon-plane-up-right'))
        flight = flight.find_parent().find('span').text.strip() if flight else '**:**'
        # print(flight)

        weather = self._safe_find(soup, ('div', 'cor-acco-summary__fact-icons'), ('i', 'cor-icon icon-sun'))
        weather = weather.find_parent().find('span').text.split()[1] if weather else '?°C'
        # print(weather)

        description = soup.find('div', class_='cor-acco-short-description')
        description = self._safe_find(description, ('p','')) if self._safe_find(description, ('p','')) else description
        description = self._translate(description.text.strip(), 'nl', 'en') if description else "<not_defined>"
        # print(description)

        # The following information can sometimes not be found, so it will be set as <not_defined> in this case
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

        # Set all the parameters to the found values
        deal['flight'] = flight
        deal['weather'] = weather
        deal['location'] = location
        deal['service'] = service
        deal['description'] = description

    def _days_left(self, dep):
        """Calculates how many days are left until departure"""
        locale.setlocale(locale.LC_TIME, "Dutch_Netherlands")        # needed to translate Dutch months
        data = datetime.strptime(dep.split(" (")[0], "%d %b %Y")
        return int((data - datetime.now()).days) + 1                # taking today into account

    def _translate(self, text, src, dest):
        """Translates given text, if some problems appears, returns text unchanged"""
        if not self._translator:
            self._translator = Translator()
        try:
            return self._translator.translate(text, src=src, dest=dest).text
        except AttributeError as e:
            print(e)
            return text


    def parse(self):
        """Parses all the deals which suit filters from all the pages of the website"""

        self._last_parse = datetime.now()       # set the time, when the deals were updated
        good_deals = {}     # deals which satisfy the filters

        counter = 1         # needed for pagination
        while counter > 0:
            url = self.url+str(counter)
            req = requests.get(url, headers=self.headers)
            src = req.text
            # self._save_html(src, str(counter))            # the html can be saved as 'lm_tour_page<counter>'

            # Instead of parsing the url we can take the source from the saved html files (mostly needed for testing)
                                                                                    # Too many requests == possible BAN
            # with open(f'../data_storage/data/lm_tour_page{str(counter)}.html') as file:
            #     src = file.read()

            soup = BeautifulSoup(src, 'lxml')
            all_tours = soup.find_all('article', class_='cor-sr-item')

            # If no tours can be found, it means ALL the tours are parsed and an empty page is parsed
            if len(all_tours) == 0:
                break

            # We go through all the tours, parsing general information
            for tour in all_tours:
                tour_info = tour.find('div', class_="cor-sr-item__main row")

                review = self._safe_find(tour_info, ('div', 'cor-sr-item__usp-reviews col-3of8'), ('div', 'cor-reviews-statistics__summary cor-reviews-statistics__ref'), ('div', 'cor-reviews-statistics__score'))
                review = float(str(review.text).strip().replace(',', '.') if review else '0.0') # if review doesn't exist, it gets 0

                review_num = self._safe_find(tour_info,  ('div', 'cor-sr-item__usp-reviews col-3of8'), ('div', 'cor-reviews-statistics__summary cor-reviews-statistics__ref'), ('div', 'cor-reviews-statistics__details'), ('div', ''))
                review_num = int(str(review_num.text).strip().replace('beoordelingen', '') if review_num else '0') # if review_num doesn't exist, it gets 0

                price = self._safe_find(tour_info, ('div', re.compile('cor-sr-item__price col-2of8')), ('div', 'cor-price-element'), ('span', ''))
                price = int(price.text.strip())

                # All the following information is located in one box on the website, so they are parsed together
                extra_info = self._safe_find(tour_info, ('div', re.compile('cor-sr-item__price col-2of8')), ('header', ''))
                departure, tour_len, dep_location =[i.strip() for i in extra_info.text.split('\n') if i.strip()!='']

                dep_in = self._days_left(departure)
                tour_len = int(tour_len[0])
                dep_location = dep_location.split()[1]

                # Finding link and extracting all the information from it
                link = self._safe_find(tour, ('header', 'row'), ('div', 'h1 cor-heading--branded'), ('a', ''))
                name = link.text.strip().replace(' ', '_')  # Name of the tour is stored inside the link
                link = link.get('href').split("#[filters]")[0]
                country = link.split('https://www.corendon.nl/')[1].split('/', 1)[0].capitalize() # name of the country is used in the link

                # Here the rest of the information is parsed (its location on the website differs from the other data)
                hotel_type = self._safe_find(tour, ('header', 'row'), ('div', 'cor-sr-item__acco-rating'), ('span', 'h4 cor-heading--branded'))
                hotel_type = re.sub(r'\s+', '_', hotel_type.text.strip()).replace('_-_', '-')  # delete tabs, enters...

                stars = self._safe_find(tour, ('header', 'row'), ('div', 'cor-sr-item__acco-rating'), ('span', re.compile('cor-stars data-stars-')))
                stars = int(stars.get('class')[1][-2]) if stars else 0          # here we find star rating from class
                                                                                      # ("data-stars-30" means 3 stars)

                # Tours we get are sorted by price, if we found the tour which exceeds max_price, we can stop here

                if price > self.max_price:
                    counter = -1            # stops the external loop (next page won't be parsed)
                    break

                # if given tour doesn't meet the requirements it is ignored and this iteration is skipped
                if any([
                    review < self.min_review,
                    review_num < self.num_review,
                    dep_in < self.dep_in,
                    tour_len < self.tour_len,
                    self.dep_loc and dep_location not in self.dep_loc
                ]):
                    continue

                # Gather all the information in one dictionary and assign it to good_deals
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
            counter += 1      # increase the counter -> go to the next page

        # Write all the good_deals in json file
        with open(f"{self.directory}/nice_deals.json", "w", encoding="utf-8") as file:
            json.dump(good_deals, file, indent=4, ensure_ascii=False)

    def fill_tours(self, num):
        """Fills N tours from json file with all the additional information"""
        with open(f"{self.directory}/nice_deals.json", "r", encoding="utf-8") as file:
            deals = json.load(file)

        first_deals = dict(itertools.islice(deals.items(), num))
        rest_deals = dict(itertools.islice(deals.items(), num, None))

        for deal in first_deals.values():
            # the data is updated only if these parameters have None value
            if not any((
                    deal['flight'],
                    deal['weather'],
                    deal['location'],
                    deal['service'] ,
                    deal['description'])):
                self._update_data(deal)

        updated_deals = first_deals | rest_deals        # rest_deals weren't changed, so they are writen back the same
        with open(f"{self.directory}/nice_deals.json", "w", encoding="utf-8") as file:
            json.dump(updated_deals, file, indent=4, ensure_ascii=False)

    def fill_hottest(self):
        """Finds all the hottest deals, fills them with all the information if needed and writes in json file"""
        if not self._hottest_set:   # if the filter params are not set
            raise AttributeError("You need to set filter for the hottest deals. Call 'set_hottest'!")

        with open(f"{self.directory}/nice_deals.json", "r", encoding="utf-8") as file:
            deals = json.load(file)

        hottest_deals = {}
        for deal in deals.values():
            # if deal is not so hot we skip the iteration
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

            # If this deal doesn't contain all the information, information in it is updated
            if not any((deal['flight'], deal['weather'], deal['description'], deal['location'], deal['service'])):
                self._update_data(deal)
            hottest_deals[deal['name']] = deal

        # Writing deals in json files
        with open(f"{self.directory}/nice_deals.json", "w", encoding="utf-8") as file:
            json.dump(deals, file, indent=4, ensure_ascii=False)    # needed to avoid double work

        with open(f"{self.directory}/hottest_deals.json", "w", encoding="utf-8") as file:
            json.dump(hottest_deals, file, indent=4, ensure_ascii=False)

    def prepare_message(self, num):
        """Returns a list with a length of <num> of the messages which need to be sent by chatbot"""
        with open(f"{self.directory}/hottest_deals.json", "r", encoding="utf-8") as file:
            hot_deals = json.load(file)
        hot_deals = dict(itertools.islice(hot_deals.items(), num))

        deal_str ="""My Sir, I’ve processed your request.  
Here’s the most promising option for your next adventure:  

🏨 **Accommodation:** {} ({})  
📍 **Destination:** {} — currently enjoying *{}*.  
💸 **Estimated Cost:** {}€ — worth every moment and every mile.
⭐ Rated *{}/10*, based on **{} reviews**.

🛫 Your journey starts from **{}**, with *{} days* of relaxation and exploration ahead.
⏳ Attention, only *{} days* left. After that, this opportunity will be archived... permanently.

📌 **Location Highlights:**  
{}  

🍴 **Offered Services:**  
{}  

As always, I remain at your service. Just say the word, and the world will be min... I mean yours. 😅

Psss... if you want to know more about this deal, just click here: 
{}
"""

        hot_deal_str = "!!! ATTENTION VERY HOT DEAL 🥵🔥 !!!\n\n" + deal_str
        hot_deals_messages = [hot_deal_str.format(
            deal['name'], deal['stars'], deal['country'], deal['weather'], deal['price'], deal['review'], deal['quantity'],
            deal['departure'], deal['tour_length'], deal['days_left'], deal['location'], deal['service'], deal['link']
        ) for deal in hot_deals.values()]

        reg_deals_num = num - len(hot_deals)
        if reg_deals_num < 1:           # if we don't need to send anything apart from hot deals
            return hot_deals_messages

        with open(f"{self.directory}/nice_deals.json", "r", encoding="utf-8") as file:
            reg_deals = json.load(file)

        rest_deals = {}     # filled with the deals which are not the hottest, but needed to return needed num of deals
        for k, v in reg_deals.items():
            if k not in hot_deals:
                rest_deals[k] = v
                if len(rest_deals) >= reg_deals_num:
                    break

        reg_deals_messages = [deal_str.format(
            deal['name'], deal['stars'], deal['country'], deal['weather'], deal['price'], deal['review'], deal['quantity'],
            deal['departure'], deal['tour_length'], deal['days_left'], deal['location'], deal['service'], deal['link']
        ) for deal in rest_deals.values()]

        return hot_deals_messages + reg_deals_messages

    def update_needed(self, hours):
        """Checks if more than N hours have passed since the last tours update """
        if self._last_parse is None or (datetime.now() - self._last_parse) > timedelta(hours=hours):
            return True
        return False


if __name__ == '__main__':
    parser = LM_Parser(500, -1, num_review=-1, dep_in=1)
    parser.set_settings(directory='../data_storage/data', headers=HEADERS)
    parser.set_hottest(max_price=500, min_review=8, num_review=350, dep_in=0)

    # parser.parse()

    # parser.fill_tours(30)
    # parser.fill_hottest()

    # print(len(parser.prepare_message(10)))
    # for i in parser.prepare_message(10):
    #     print(i)




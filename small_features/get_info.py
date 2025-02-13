import requests
from bs4 import BeautifulSoup
from currency_converter import CurrencyConverter
from pycoingecko import CoinGeckoAPI

from config import HEADERS


def get_weather():
    response = requests.get('https://www.accuweather.com/en/nl/enschede/250111/weather-forecast/250111', headers=HEADERS)
    soup = BeautifulSoup(response.text, 'lxml')
    temp = soup.find('div', class_='temp-container').find('div', class_='temp').text
    state = soup.find('div', class_= 'cur-con-weather-card__panel').find('div', class_='').find('span', class_='phrase').text
    return temp, state

def get_currency():
    cg = CoinGeckoAPI()
    cr = CurrencyConverter()

    usd = cr.convert(1, 'EUR', 'GBP')
    gbp = cr.convert(1, 'EUR', 'GBP')
    bitcoin = cg.get_price(ids='bitcoin', vs_currencies='eur')
    return {'usd': round(usd, 3),
            'gbd': round(gbp, 3),
            'bitcoin': bitcoin['bitcoin'].get('eur')}


if __name__ == '__main__':
    print(get_weather())
    print(get_currency())

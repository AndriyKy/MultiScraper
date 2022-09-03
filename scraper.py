from datetime import date
import re
import json
import requests
import fake_useragent as FU
import pretty_errors
from prettytable import PrettyTable as PT
from bs4 import BeautifulSoup as BS

# Generation of a random "user-agent"
_UA = FU.UserAgent()

# Get HTML response
_headers = {
    "User-Agent": _UA.random,
}

with open("data.json", "r") as json_file:
    _coll = json.load(json_file)

_regions = _coll['_regions']
_currencies = _coll['_currencies']
_headlines = _coll['_headlines']

def price_of_fuel(region=str, fuel_type=str):
    """
    region: e.g.: "Волинська", "Івано-Франківська" etc.\n
    fuel_type: "95+", "95", "92", "ДП", "Газ"
    """

    _auto_ria = f'https://auto.ria.com/uk/toplivo/{_regions[region]}/#refuel'      

    # Sending a request and receiving a response
    _auto_ria_resp = requests.get(_auto_ria, headers=_headers)
    _ria_html = _auto_ria_resp.text

    # Parsing of a received response 
    __soup = BS(_ria_html, 'lxml')

    # Searching of all possible data by tag and class name
    _fuel = {
        'name': __soup.find_all('td', class_='refuel'),
        '95+': __soup.find_all('td', class_='a95p'),
        '95': __soup.find_all('td', class_='a95'),
        '92': __soup.find_all('td', class_='a92'),
        'ДП': __soup.find_all('td', class_='dt'),
        'Газ': __soup.find_all('td', class_='gaz'),
    }

    # PrettyTable initialization
    _pt = PT()
    _pt.field_names = ['Заправка', fuel_type]

    for (name_val, _fuel_type_val) in zip(_fuel['name'], _fuel[fuel_type]):
        _pt.add_row([name_val.text, _fuel_type_val.text])
    _pt.add_row(['Середня вартість', _fuel[fuel_type][-1].text])

    return _pt


class Currency:
    """
    currency: e.g.: "Долар", "Євро", "Польський злотий" etc.\n
    date: format - "YYYY-MM-DD"
    """

    def __init__(self, currency=str, date=date.today()) -> None:
        self.__currency = currency
        self.__date = date

        self.__minfin = f'https://minfin.com.ua/ua/currency/banks/{_currencies[self.__currency]}/{self.__date}'
        self.__minfin_resp = requests.get(self.__minfin, headers=_headers)
        self.__soup = BS(self.__minfin_resp.text, 'lxml')

    def average_exchange_rate(self):
        # Initialization of the pattern for extracting a number
        _pattern = re.compile('[0-9]?[0-9][.,][0-9][0-9]')
        _titles = []

        # Obtaining data for each column of the average exchange rate
        for headline in _headlines:
            temp_var = self.__soup.find(
                'td', attrs={'data-title': headline}).text
            search_rez = _pattern.findall(str(temp_var))

            if len(search_rez)==0:
                search_rez.append('-')
                _titles.append(search_rez)

            else: _titles.append(search_rez)

        _pt = PT()
        _pt.add_column('Валюта', _headlines)
        _pt.add_column(
            self.__currency, [f'{_titles[0][0]} / {_titles[0][-1]}',
                              _titles[1][0], f'{_titles[2][0]} / {_titles[2][-1]}']
        )
        return _pt

    def banks(self):
        """
        return: a list of available banks that operate in the specified currency
        """
        return [name.text.replace('\n', '')
                for name in self.__soup.find_all('td', class_="mfcur-table-bankname")]


    def bank_rate(self, bank_name=str):
        """
        bank_name: e.g.: "Приватбанк", "Ощадбанк", "monobank" etc.\n\n
        To correctly specify the bank, you should first run the "banks" method!
        """
        _specific_bank = [link for link in self.__soup.find_all('a', class_='mfm-black-link')
                          if bank_name in link.text][0].parent.parent

        _cash_reg_purch = _specific_bank.find('td',
                                              attrs={'data-title': 'У касах банків',
                                                     'data-small': 'Покупка'}).text
        _cash_reg_sale = _specific_bank.find('td',
                                             attrs={'data-title': 'У касах банків',
                                                    'data-small': 'Продаж'}).text
        _card_purch = _specific_bank.find('td',
                                          attrs={'data-card-title': 'У касах банків'}).text
        _card_sale = _specific_bank.find('td',
                                         attrs={'data-title': 'При оплаті карткою',
                                                'data-small': 'Продаж'}).text

        _pt = PT(['Валюта', 'Банк', 'У касах банків', 'При оплаті карткою'])
        _pt.add_row([self.__currency, bank_name,
                    f'{_cash_reg_purch} / {_cash_reg_sale}', f'{_card_purch} / {_card_sale}'])

        return _pt

# reg = input("Область: ")
# fuel = input("Пальте: ")
# print(f'\n{reg} область пропонує пальте {fuel} за такими цінами\n', 
#         price_of_fuel(reg, fuel))

# for reg in _regions:
#     for fuel in ["95+", "95", "92", "ДП", "Газ"]:
#         print(f'\n{reg} область пропонує пальте {fuel} за такими цінами\n', 
#                 price_of_fuel(reg, fuel))

curr = Currency("Євро")
av_rate = curr.average_exchange_rate()
banks = curr.banks()
rate = curr.bank_rate('Приватбанк')

# print(av_rate)
# print(banks)
print(rate)
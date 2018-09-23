import requests
import urllib
import re
import json

class Robinhood:

    endpoints = {
            "token": "https://robinhood.com/login",
            "login": "https://api.robinhood.com/oauth2/token/",
            "investment_profile": "https://api.robinhood.com/user/investment_profile/",
            "accounts":"https://api.robinhood.com/accounts/",
            "ach_iav_auth":"https://api.robinhood.com/ach/iav/auth/",
            "ach_relationships":"https://api.robinhood.com/ach/relationships/",
            "ach_transfers":"https://api.robinhood.com/ach/transfers/",
            "applications":"https://api.robinhood.com/applications/",
            "dividends":"https://api.robinhood.com/dividends/",
            "edocuments":"https://api.robinhood.com/documents/",
            "instruments":"https://api.robinhood.com/instruments/",
            "margin_upgrades":"https://api.robinhood.com/margin/upgrades/",
            "markets":"https://api.robinhood.com/markets/",
            "notifications":"https://api.robinhood.com/notifications/",
            "orders":"https://api.robinhood.com/orders/",
            "password_reset":"https://api.robinhood.com/password_reset/request/",
            "quotes":"https://api.robinhood.com/quotes/",
            "document_requests":"https://api.robinhood.com/upload/document_requests/",
            "user":"https://api.robinhood.com/user/",
            "watchlists":"https://api.robinhood.com/watchlists/",
    }

    session = None

    username = None

    password = None

    headers = None

    auth_token = None

    account_url = None

    client_id = None

    def __init__(self, username, password):
        self.session = requests.session()
        self.session.proxies = urllib.getproxies()
        self.username = username
        self.password = password
        self.headers = {
            "accept": "*/*",
            "referer": "https://robinhood.com/login",
            "content-type": "application/json"
        }
        
        self.session.headers = self.headers
        self.gettoken()
        self.login()
        
        ## set account url
        acc = self.get_account_number()
        self.account_url = self.endpoints['accounts'] + acc + "/"

    def gettoken(self):
        headers = {
            'cache-control': "no-cache"
        }
        response = requests.request("GET", self.endpoints['token'], headers=headers)
        items=re.findall("^.*oauthClientId.*$",response.text,re.MULTILINE)
        clientid = items[0][items[0].index("'") + 1:len(items[0])]
        clientid = clientid[0:clientid.index("'")]
        self.client_id = clientid


    def login(self):
        data = {}
        data['grant_type'] = 'password'
        data['scope'] = 'internal'
        data['client_id'] = self.client_id
        data['expires_in'] = 86400
        data['username'] = self.username
        data['password'] = self.password
        json_data = json.dumps(data)
        response = requests.request("POST", self.endpoints['login'], data=str(json_data), headers=self.headers)
        res = response.json()
        self.auth_token = res['access_token']
        self.headers['Authorization'] = 'Bearer '+self.auth_token

    def get_account_number(self):
        res = self.session.get(self.endpoints['ach_relationships'])
        res =  res.json()['results'][0]
        account_number = res['account'].split('accounts/', 1)[1][:-1]
        return account_number

    def investment_profile(self):
        self.session.get(self.endpoints['investment_profile'])

    def instruments(self, stock=None):
        res = self.session.get(self.endpoints['instruments'], params={'query':stock.upper()})
        res = res.json()
        return res['results']

    def quote_data(self, stock):
        params = { 'symbols': stock }
        res = self.session.get(self.endpoints['quotes'], params=params)
        res = res.json()
        return res['results']

    def place_order(self, instrument, quantity=1, bid_price = None, transaction=None):
        if bid_price == None:
            bid_price = self.quote_data(instrument['symbol'])[0]['bid_price']
        data = 'account=%s&instrument=%s&price=%f&quantity=%d&side=%s&symbol=%s&time_in_force=gfd&trigger=immediate&type=market' % (urllib.quote(self.account_url), urllib.unquote(instrument['url']), float(bid_price), quantity, transaction, instrument['symbol']) 
        res = self.session.post(self.endpoints['orders'], data=data)
        return res

    def place_buy_order(self, instrument, quantity, bid_price=None):
        transaction = "buy"
        return self.place_order(instrument, quantity, bid_price, transaction)

    def place_sell_order(self, instrument, quantity, bid_price=None):
        transaction = "sell"
        return self.place_order(instrument, quantity, bid_price, transaction)


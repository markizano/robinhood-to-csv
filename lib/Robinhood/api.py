
import sys
import requests
from kizano import getLogger
log = getLogger(__name__)

try:
    from urllib.parse import urlencode #py3
except ImportError:
    from urllib import urlencode  #py2

try:
    from urllib.request import getproxies #py3
except ImportError:
    from urllib import getproxies #py2

class Client(object):
    endpoints = {
        "accounts":               "https://api.robinhood.com/accounts/",
        "achIAVAuth":             "https://api.robinhood.com/ach/iav/auth/",
        "achRelationships":       "https://api.robinhood.com/ach/relationships/",
        "achTransfers":           "https://api.robinhood.com/ach/transfers/",
        "applications":           "https://api.robinhood.com/applications/",
        "document_requests":      "https://api.robinhood.com/upload/document_requests/",
        "dividends":              "https://api.robinhood.com/dividends/",
        "edocuments":             "https://api.robinhood.com/documents/",
        "employment":             "https://api.robinhood.com/user/employment",
        "investment_profile":     "https://api.robinhood.com/user/investment_profile/",
        "instruments":            "https://api.robinhood.com/instruments/",
        "login":                  "https://api.robinhood.com/oauth2/token/",
        "margin_upgrades":        "https://api.robinhood.com/margin/upgrades/",
        "markets":                "https://api.robinhood.com/markets/",
        "notification_settings":  "https://api.robinhood.com/settings/notifications/",
        "notifications":          "https://api.robinhood.com/notifications/",
        "orders":                 "https://api.robinhood.com/orders/",
        "password_reset":         "https://api.robinhood.com/password_reset/request/",
        "portfolios":             "https://api.robinhood.com/portfolios/",
        "positions":              "https://api.robinhood.com/positions/",
        "quotes":                 "https://api.robinhood.com/quotes/",
        "user":                   "https://api.robinhood.com/user/",
        "watchlists":             "https://api.robinhood.com/watchlists/",
        "optionsOrders":          "https://api.robinhood.com/options/orders/",
        "optionsPositions":       "https://api.robinhood.com/options/positions/"
    }

    client_id = "c82SH0WZOsabOXGP2sxqcj34FxkvfnWRZBKlBjFS"

    def __init__(self, cfg={}):
        self.username = cfg.get('username')
        self.password = cfg.get('password')
        self.auth_token = None
        self.cached_instruments = {}
        self.session = requests.session()
        self.session.proxies = getproxies()
        self.headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en;q=1, fr;q=0.9, de;q=0.8, ja;q=0.7, nl;q=0.6, it;q=0.5",
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
            #"X-Robinhood-API-Version": "brokeback/1.433.103-1656710961-ge1566519d9156179dc522e0d2f98a6a3aa0128df",
            "Connection": "keep-alive",
            "User-Agent": "libRobinhood/1.0 (Python-%d.%d.%d-%s)" % sys.version_info[0:4]
        }
        self.session.headers = self.headers

    def __getattr__(self, name):
        '''
        If any of the endpoints are called as methods, return the HTTP response to it.
        '''
        if name in Client.endpoints:
            return lambda *args: self.get(name, *args)
        raise AttributeError(f'{self.__class__} has no attribute {name}')

    def get(self, endpoint, params):
        '''
        Private method to enable us to publish to the end point and not have to worry
        about encoding/escaping before output.
        Central point of control for all requests for data of this class object.
        @param endpoint {enum:string} one of the endpoints as described above in {Robinhood.endpoints}.
        @param params {object} Query-string arguments we want to send to Robinhood that will be URL-encoded
          accordingly before sending.
        @returns {object} JSON parsed response.
        '''
        qsa = urlencode(params)
        url = f'{Client.endpoints[endpoint]}?{qsa}'
        return self.session.get(url)

    def post(self, endpoint, params, data={}):
        '''
        Private method to enable us to publish to the end point and not have to worry
        about encoding/escaping before output.
        Central point of control for all requests for data of this class object.
        @param endpoint {enum:string} one of the endpoints as described above in {Robinhood.endpoints}.
        @param params {object} Query-string arguments we want to send to Robinhood that will be URL-encoded
          accordingly before sending.
        @param data {object} Data we want to send to Robinhood API's.
        @returns {object} JSON parsed response.
        '''
        qsa = urlencode(params)
        payload = urlencode(data)
        url = f'{Client.endpoints[endpoint]}?{qsa}'
        return self.session.post(url, payload)

    def login(self, mfa_code):
        '''
        Implementation of the login function with the expected POST data.
        @param mfa_code {str} Multi-factor code from Authy, Google Authenticator, MS Authenticator
          or <insert-MFA-auth-app-here>.
        @returns {bool} TRUE if passed. FALSE on failed login and will log the error.
        '''
        data = {
            'password' : self.password,
            'username' : self.username,
            'grant_type': 'password',
            'client_id': Client.client_id,
            'mfa_code': mfa_code
        }
        res = self.post('login', {}, data).json()
        try:
            self.auth_token = res['access_token']
        except KeyError:
            log.error('Login failed!')
            log.debug(res)
            return False
        self.headers['Authorization'] = f'Bearer {self.auth_token}'
        return True

    def __getattr__(self, name):
        '''
        If the method is not defined, try to assume a HTTP:GET request for one of the endpoints
        described in @{Robinhood.endpoints}.
        @return {object} JSON decoded response from the server.
        '''
        if name in Client.endpoints:
            return lambda *args: self.get(name, *args)
        raise AttributeError(f'{self.__class__} has no attribute {name}')

    def instruments(self, stock, cached=True):
        '''
        Gets the 
        '''
        stock = stock.upper()
        if not cached and stock in self.cached_instruments:
            del self.cached_instruments[stock]
        if stock not in self.cached_instruments:
            res = self.session.get(self.endpoints['instruments'], params={'query': stock})
            self.cached_instruments[stock] = res.json()['results']
        return self.cached_instruments[stock]

    def quote_data(self, stock):
        url = f"{Client.endpoints['quotes']}/{stock.upper()}/"
        # Check for validity of symbol
        try:
            response = self.session.get(url)
            if len(res) > 0:
                return res
            else:
                raise NameError("Invalid Symbol: " + stock)
        except (ValueError):
            raise NameError("Invalid Symbol: " + stock)

    def get_quote(self, stock):
        data = self.quote_data(stock)
        return data["symbol"]

    def print_quote(self, stock):
        data = self.quote_data(stock)
        print(data["symbol"] + ": $" + data["last_trade_price"])

    def print_quotes(self, stocks):
        for i in range(len(stocks)):
            self.print_quote(stocks[i]);

    ##############################
    #PLACE ORDER
    ##############################

    def place_order(self, instrument, quantity=1, bid_price=None, transaction=None):
        # cache the account ID that's needed for placing orders
        if self.positions == None:
            self.positions = self.get_endpoint("positions")['results']
        if bid_price == None:
            bid_price = self.quote_data(instrument['symbol'])[0]['bid_price']
        datapoints = {
            'account': self.positions[0]['account'],
            'instrument': instrument['url'],
            'price': bid_price,
            'quantity': quantity,
            'side': transaction,
            'symbol': instrument['symbol'],
            'time_in_force': 'gfd',
            'trigger': 'immediate',
            'type': 'market'
        }
        res = self.post('orders', {}, datapoints)
        return res

    def place_buy_order(self, instrument, quantity, bid_price=None):
        transaction = "buy"
        return self.place_order(instrument, quantity, bid_price, transaction)

    def place_sell_order(self, instrument, quantity, bid_price=None):
        transaction = "sell"
        return self.place_order(instrument, quantity, bid_price, transaction)


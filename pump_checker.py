from numpy.core.numeric import False_
import pandas as pd
import os.path
import ccxt
import time
import requests
import ta
import pprint

from pprint import pprint
from os import path
from datetime import datetime as dt
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import MACD
from datetime import datetime

if __name__ == '__main__':
    f = open('key.txt', 'r')
    data = f.read()
    f.close()

    # first & second line of key.txt = binance key
    binance = ccxt.binance(config={'apiKey': data.split('\n')[
        0], 'secret': data.split('\n')[1]})

    # second line of key.txt = slack token
    slack_token = data.split('\n')[2]

    # third line of key.txt = coins to trade
    coin_to_trade = []
    temp = ''
    for i in data.split('\n')[3]:
        if i != ',':
            temp = temp + i
        else:
            temp = temp[:-4] + '/' + temp[-4:]
            coin_to_trade.append(temp)
            temp = ''
    temp = temp[:-4] + '/' + temp[-4:]
    coin_to_trade.append(temp)

    # interval check
    interval = data.split('\n')[3]

    all_binance_market = binance.fetch_markets()
    usdt_volume_checker = []
    for i in all_binance_market:
        if i['symbol'][-4:] == 'USDT':
            if i['symbol'][0:2] != 'USD':
                if 'MARKET' in i['info']['orderTypes']:
                    pprint(i)

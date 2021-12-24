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
    last_bought = open('last_bought.txt', 'r')
    last_bought_coin = str(last_bought.readline())
    last_bought.close()

    print(last_bought_coin)
    # usdt_volume_checker = []
    # for i in all_binance_market:
    #     # pprint(i['limits']['amount']['min'])
    #     if i['symbol'][-4:] == 'USDT':
    #         if i['symbol'][0:2] != 'USD':
    #             temp = binance.fetch_ohlcv(i['symbol'], '12h', limit=3)
    #             print('Checking ' + str(i['symbol']))
    #             if temp[1][5] >= temp[0][5]:
    #                 if temp[2][1] >= temp[1][1] >= temp[0][1]:
    #                     symbol_volume = (i['symbol'], 100-100 /
    #                                      temp[1][5]*temp[0][5])
    #                     usdt_volume_checker.append(symbol_volume)

    # usdt_volume_checker.sort(key=lambda x: x[1], reverse=True)
    # trading_coins = []

    # if len(usdt_volume_checker) >= 30:
    #     for i in range(30):
    #         trading_coins.append(usdt_volume_checker[i][0])
    #     print(trading_coins)
    # else:
    #     for i in usdt_volume_checker:
    #         trading_coins.append(usdt_volume_checker[i][0])
    #     print(trading_coins)

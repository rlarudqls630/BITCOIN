from numpy.core.numeric import False_
import pandas as pd
import os.path
import ccxt
import time
import requests
import ta

from os import path
from datetime import datetime as dt
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import MACD
from datetime import datetime


def sell_check(coin_name):
    swing_low = open('swing_low.txt', 'rt')
    stop_lose = float(swing_low.readline())
    swing_low.close()
    profit_sell_val = stop_lose * 1.5

    balance = binance.fetch_balance()

    while balance['free']['USDT'] <= 10:
        sell_book = binance.fetch_order_book(coin_name)
        bars = binance.fetch_ohlcv(i, interval, limit=200)
        df = pd.DataFrame(
            bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

        rsi_indicator = RSIIndicator(df['close'])
        rsi_val = rsi_indicator.rsi()

        stochast_indicator = StochasticOscillator(
            df['high'], df['low'], df['close'])
        stochast_k = stochast_indicator.stoch()
        stochast_d = stochast_indicator.stoch_signal()

        print('---------------------------------------')
        print(dt.now().strftime('%Y-%m-%d %H:%M:%S'))
        print('%s__TRADING' % coin_name)
        print('')
        print('Current ask : $' + str(sell_book['asks'][0][0]))
        print('')
        print('Stop lose   : $' + str(stop_lose))
        print('RSI_Val     : ' + str(rsi_val.iloc[-1]))
        print('Stochast_k  : ' + str(stochast_k.iloc[-1]))
        print('Stochast_b  : ' + str(stochast_d.iloc[-1]))
        print('')
        print('Profit_sell : $' + str(profit_sell_val))
        print('---------------------------------------')
        
        if rsi_val.iloc[-1] >= 75:
            if stochast_k.iloc[-1] >= 80:
                if stochast_d.iloc[-1] >= 80:
                    sell(coin_name)
        elif sell_book['asks'][0][0] >= profit_sell_val:
            sell(coin_name)
        elif sell_book['asks'][0][0] <= stop_lose:
            sell(coin_name)
        balance = binance.fetch_balance()


def buy(coin_name):
    # 잔고를 보고 매수 할 수 있으면 호가 매수
    balance = binance.fetch_balance()
    if balance['free']['USDT'] >= 10:
        bal = balance['free']['USDT']

        orderbook = binance.fetch_order_book(coin_name)

        binance.create_market_buy_order(
            coin_name, bal / orderbook['bids'][0][0])

        time.sleep(2)

        if len(binance.fetch_open_orders(coin_name)) != 0:
            buy_cancel(coin_name)

        text = coin_name + '\n매수: $' + \
            str(round(bal, 2)) + '\n매수 가격: $' + str(orderbook['bids'][0][0])
        post_message(slack_token, "#bitcoin", text)

        sell_check(coin_name)


def buy_cancel(coin_name):
    order_id = binance.fetch_open_orders(coin_name)
    order_id = order_id[0]['info']['orderId']
    binance.cancel_order(int(order_id), coin_name)
    buy(coin_name)


def sell(coin_name):
    sell_coin = coin_name[:-5]

    minimum_trade_file = pd.read_csv('minimum_trade.csv')
    amount = float(
        minimum_trade_file.loc[minimum_trade_file['coin'] == sell_coin, 'minimum'])

    # 발랜스 보고 코인으로 잔고가 있으면 호가 매도
    balance = binance.fetch_balance()

    if balance['free'][sell_coin] >= amount:
        binance.create_market_sell_order(
            coin_name, balance['free'][sell_coin])

        time.sleep(5)

        if len(binance.fetch_open_orders(coin_name)) != 0:
            sell_cancel(coin_name)

        bal = binance.fetch_balance()
        bal = bal['free']['USDT']
        text = coin_name + '\n매도: $' + str(round(bal, 2))
        post_message(slack_token, "#bitcoin", text)
        
        post_message(slack_token, "#bitcoin", 'Profit made, sleeping for 30m')
        time.sleep(1800)


def sell_cancel(coin_name):
    order_id = binance.fetch_open_orders(coin_name)
    order_id = order_id[0]['info']['orderId']
    binance.cancel_order(int(order_id), coin_name)
    sell(coin_name)


def post_message(token, channel, text):
    response = requests.post("https://slack.com/api/chat.postMessage",
                             headers={"Authorization": "Bearer " + token},
                             data={"channel": channel, "text": text}
                             )


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
    interval = data.split('\n')[4]

    # when error occured and restarted program use this to go to con_trade
    for i in coin_to_trade:
        balance = binance.fetch_balance()
        price_data = binance.fetch_ohlcv(i, interval, limit=1)
        free_coin = balance['free'][i[:-5]]
        if (price_data[0][4] * free_coin >= 10):
            sell_check(i)

    while True:
        for i in coin_to_trade:
            bars = binance.fetch_ohlcv(i, interval, limit=200)
            df = pd.DataFrame(
                bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

            rsi_indicator = RSIIndicator(df['close'])
            rsi_val = rsi_indicator.rsi()

            MACD_indicator = MACD(
                df['close'], window_slow=21, window_fast=8, window_sign=5)
            MACD_signal_val = MACD_indicator.macd_signal()
            MACD_diff_val = MACD_indicator.macd_diff()

            stochast_indicator = StochasticOscillator(
                df['high'], df['low'], df['close'])
            stochast_k = stochast_indicator.stoch()
            stochast_d = stochast_indicator.stoch_signal()

            print('---------------------------------------')
            print(dt.now().strftime('%Y-%m-%d %H:%M:%S'))
            print('%s__TRADING' % i)
            print('')
            print('Stochast_K : ' + str(stochast_k.iloc[-1]))
            print('Stochast_D : ' + str(stochast_d.iloc[-1]))
            print('RSI        : ' + str(rsi_val.iloc[-1]))
            print('MACD_Diff  : ' + str(MACD_diff_val.iloc[-1]))
            print('MACD_Signal: ' + str(MACD_signal_val.iloc[-1]))

            # entry signal
            if rsi_val.iloc[-1] >= 50:
                print('')
                print('CASE 1: RSI OVER 50')
                if MACD_diff_val.iloc[-1] >= MACD_signal_val.iloc[-1]:
                    print('CASE 2: MACD_D > MACD_S')
                    if stochast_k.iloc[-1] <= 80 and stochast_d.iloc[-1] <= 80:
                        print('CASEE 3: STOCHASTIC < 80')
                        swing_low_price = min(
                            df.iloc[-2]['close'], df.iloc[-2]['open'])
                        for j in range(30):
                            if swing_low_price >= min(df.iloc[(j + 2) * -1]['close'], df.iloc[(j + 2) * -1]['open']):
                                swing_low_price = min(
                                    df.iloc[(j + 2) * -1]['close'], df.iloc[(j + 2) * -1]['open'])
                            else:
                                break
                        swing_low = open('swing_low.txt', 'w')
                        swing_low.write(str(swing_low_price))
                        swing_low.close()
                        buy(i)
            print('---------------------------------------')
            print('')

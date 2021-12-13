import pandas as pd
import os.path
import ccxt
import time
import requests
from os import path
from datetime import datetime as dt


# Data storage of coins
def candle_data_storage(file, time_frame, coin):
    new_coin_name = coin_name(coin)

    if os.stat(file).st_size == 0:
        btc_ohlcv = binance.fetch_ohlcv(new_coin_name, interval, limit=300)
        df = pd.DataFrame(btc_ohlcv, columns=[
                          'datetime', 'open', 'high', 'low', 'close', 'volume'])

        df['heikin_ashi_open'] = ''
        df['heikin_ashi_close'] = ''

        df.drop(df.tail(1).index, inplace=True)
        df.to_csv(file, index=False)
        heikin_ashi_calc(file)

    else:
        csvfile = pd.read_csv(file)

        if (binance.fetch_time() - int(csvfile.iloc[-1]['datetime'])) >= (time_frame*60*1000):
            btc_ohlcv = binance.fetch_ohlcv(new_coin_name, interval, int(
                csvfile.iloc[-1]['datetime']), limit=300)
            df = pd.DataFrame(btc_ohlcv, columns=[
                              'datetime', 'open', 'high', 'low', 'close', 'volume'])

            df['heikin_ashi_open'] = ''
            df['heikin_ashi_close'] = ''

            df.drop(df.index[0], axis=0, inplace=True)
            df.drop(df.tail(1).index, inplace=True)
            df.to_csv(file, mode='a', header=False, index=False)
            heikin_ashi_calc(file)

    live_heikin_ashi_calc(file, new_coin_name)


# Heikin ashi calculation and store
def heikin_ashi_calc(file):
    csvfile = pd.read_csv(file)
    length = len(csvfile)

    csvfile.iat[0, 6] = csvfile.iloc[0]['open']
    csvfile.iat[0, 7] = csvfile.iloc[0]['close']

    for i in range(length):
        # first heikin ashi value calculation
        if i >= 1:
            # close = 1/2(open + high + low + close)
            heikin_ashi_close = (csvfile.iloc[i]['open'] + csvfile.iloc[i]['high'] + csvfile.iloc[i]['low']
                                 + csvfile.iloc[i]['close']) / 4
            csvfile.iat[i, 7] = heikin_ashi_close

            # open = 1/2(prev open + prev close)
            heikin_ashi_open = (
                csvfile.iloc[i - 1]['heikin_ashi_open'] + csvfile.iloc[i - 1]['heikin_ashi_close']) / 2
            csvfile.iat[i, 6] = heikin_ashi_open

    csvfile.to_csv(file, index=False)


def live_heikin_ashi_calc(file, new_coin_name):
    sell_coin = new_coin_name[:-5]
    csvfile = pd.read_csv(file)

    # Read current OHLCV values
    btc_ohlcv = binance.fetch_ohlcv(new_coin_name, interval, limit=1)

    # Calculating heikin ashi using current values
    live_heikin_ashi_close = (
        btc_ohlcv[0][1] + btc_ohlcv[0][2] + btc_ohlcv[0][3] + btc_ohlcv[0][4]) / 4
    live_heikin_ashi_open = (
        csvfile.iloc[-1]['heikin_ashi_open'] + csvfile.iloc[-1]['heikin_ashi_close']) / 2

    # Get minimum trading amount for given coin
    minimum_trade_file = pd.read_csv('minimum_trade.csv')
    amount = float(
        minimum_trade_file.loc[minimum_trade_file['coin'] == sell_coin, 'minimum'])

    balance = binance.fetch_balance()

    # If coin was bought, go to trading
    if balance['free'][new_coin_name[:-5]] >= amount:
        if binance.fetch_ticker(new_coin_name)['ask'] * balance['free'][new_coin_name[:-5]] >= 10:
            coin_trader(file, new_coin_name)

    # 5 Bearish candle and 1 bullish candle appear
    print('----------------------------')
    print('---------- CASE 1 ----------')
    if csvfile.iloc[-1]['heikin_ashi_open'] < csvfile.iloc[-1]['heikin_ashi_close']:
        print('1: -1 BULL')
        if csvfile.iloc[-2]['heikin_ashi_open'] > csvfile.iloc[-2]['heikin_ashi_close']:
            print('2: -2 BEAR')
            if csvfile.iloc[-3]['heikin_ashi_open'] > csvfile.iloc[-3]['heikin_ashi_close']:
                print('3: -3 BEAR')
                if csvfile.iloc[-4]['heikin_ashi_open'] > csvfile.iloc[-4]['heikin_ashi_close']:
                    print('4: -4 BEAR')
                    if csvfile.iloc[-5]['heikin_ashi_open'] > csvfile.iloc[-5]['heikin_ashi_close']:
                        print('5: -5 BEAR')
                        if csvfile.iloc[-6]['heikin_ashi_open'] > csvfile.iloc[-6]['heikin_ashi_close']:
                            print('6: -6 BEAR')
                            if live_heikin_ashi_close > live_heikin_ashi_open:
                                print('7: CURRENT BULL')
                                file3 = open('last_coin.txt', 'rt')
                                last_coin = str(file3.readline())
                                file4 = open('last_time.txt', 'rt')
                                last_time = int(file4.readline())
                                if new_coin_name != last_coin:
                                    print('CRITERIA 1 MET!! BUY!!')
                                    buy(new_coin_name)
                                    coin_trader(file, new_coin_name)
                                else:
                                    if last_time != int(dt.now().strftime('%d')):
                                        print('CRITERIA 1 MET!! BUY!!')
                                        buy(new_coin_name)
                                        coin_trader(file, new_coin_name)
                            else:
                                print('FALSE ALARM!!!!')
                        else:
                            print('FALSE ALARM!!!!')
                    else:
                        print('FALSE ALARM!!!!')
                else:
                    print('FALSE ALARM!!!!')
            else:
                print('FALSE ALARM!!!!')
        else:
            print('FALSE ALARM!!!!')
    else:
        print('NO CRIETRIA MET!!')
    print('----------------------------')
    print('---------- CASE 2 ----------')
    if csvfile.iloc[-1]['heikin_ashi_open'] < csvfile.iloc[-1]['heikin_ashi_close']:
        print('1: -1 BULL')
        if csvfile.iloc[-2]['heikin_ashi_open'] < csvfile.iloc[-2]['heikin_ashi_close']:
            print('2: -2 BULL')
            if csvfile.iloc[-3]['heikin_ashi_open'] < csvfile.iloc[-3]['heikin_ashi_close']:
                print('3: -3 BULL')
                first_candle_check = csvfile.iloc[-1]['heikin_ashi_close'] - \
                    csvfile.iloc[-1]['heikin_ashi_open']
                second_candle_check = csvfile.iloc[-2]['heikin_ashi_close'] - \
                    csvfile.iloc[-2]['heikin_ashi_open']
                third_candle_check = csvfile.iloc[-3]['heikin_ashi_close'] - \
                    csvfile.iloc[-3]['heikin_ashi_open']
                if third_candle_check < second_candle_check < first_candle_check:
                    print('4: CANDLE INCREASING')
                    if live_heikin_ashi_close > live_heikin_ashi_open:
                        print('5: CURRENT BULL')
                        file3 = open('last_coin.txt', 'rt')
                        last_coin = str(file3.readline())
                        file4 = open('last_time.txt', 'rt')
                        last_time = int(file4.readline())
                        if new_coin_name != last_coin:
                            print('CRITERIA 2 MET!! BUY!!')
                            buy(new_coin_name)
                            coin_trader(file, new_coin_name)
                        else:
                            if last_time != int(dt.now().strftime('%d')):
                                print('CRITERIA 2 MET!! BUY!!')
                                buy(new_coin_name)
                                coin_trader(file, new_coin_name)
                    else:
                        print('FALSE ALARM!!!!')
                else:
                    print('FALSE ALARM!!!!')
            else:
                print('FALSE ALARM!!!!')
        else:
            print('FALSE ALARM!!!!')
    else:
        print('NO CRIETRIA MET!!')
    print('----------------------------')


def coin_trader(file, new_coin_name):
    csvfile = pd.read_csv(file)
    file2 = open('bought_at.txt', 'rt')
    bought = float(file2.readline())

    sell_point = csvfile.iloc[-1]['heikin_ashi_open']
    profit_sell = bought * 1.003

    while True:
        print('----------------------------')
        print(dt.now().strftime('%Y-%m-%d %H:%M:%S'))
        print('%s__TRADING' % new_coin_name)
        print('')

        btc_ohlcv = binance.fetch_ohlcv(new_coin_name, interval, int(
            csvfile.iloc[-1]['datetime']), limit=2)
        current_close = (btc_ohlcv[-1][1] + btc_ohlcv[-1]
                         [2] + btc_ohlcv[-1][3] + btc_ohlcv[-1][4]) / 4
        sell_book = binance.fetch_order_book(new_coin_name)

        print('Heikin Close : $' + str(round(current_close, 5)))
        print('Lost Point   : $' + str(round(sell_point, 5)))
        print('Profit Sell  : $' + str(round(profit_sell, 5)))
        print('Real Close   : $' + str(round(btc_ohlcv[-1][4], 5)))

        if current_close < sell_point:
            print('----------------------------')
            print('CURRENT CLOSE < PREVIOUS OPEN')
            sell(new_coin_name)
            print('SOLD!!!!')
            break
        elif csvfile.iloc[-1]['heikin_ashi_close'] - csvfile.iloc[-1]['heikin_ashi_open'] < csvfile.iloc[-2]['heikin_ashi_close'] - csvfile.iloc[-2]['heikin_ashi_open'] < csvfile.iloc[-3]['heikin_ashi_close'] - csvfile.iloc[-3]['heikin_ashi_open']:
            print('----------------------------')
            print('CANDLE SHRINKING')
            current_open = (
                csvfile.iloc[-1]['heikin_ashi_open'] + csvfile.iloc[-1]['heikin_ashi_close']) / 2
            if current_open > current_close:
                print('CANDLE REVERSED')
                sell(new_coin_name)
                print('SOLD!!!!')
                break
        elif profit_sell <= sell_book['asks'][0][0]:
            print('----------------------------')
            print('0.3% PROFIT MADE')
            sell(new_coin_name)
            print('SOLD!!!!')
            break

        balance = binance.fetch_balance()
        if balance['free']['USDT'] >= 10:
            break
        if (binance.fetch_time() - int(csvfile.iloc[-1]['datetime']))/1000/60 > time_frame * 2:
            print('----------------------------')
            print('NEW CANDLE MADE!!!!')
            btc_ohlcv = binance.fetch_ohlcv(new_coin_name, interval, int(
                csvfile.iloc[-1]['datetime']), limit=300)
            df = pd.DataFrame(btc_ohlcv, columns=[
                'datetime', 'open', 'high', 'low', 'close', 'volume'])

            df['heikin_ashi_open'] = ''
            df['heikin_ashi_close'] = ''

            df.drop(df.index[0], axis=0, inplace=True)
            df.drop(df.tail(1).index, inplace=True)
            df.to_csv(file, mode='a', header=False, index=False)
            heikin_ashi_calc(file)

            csvfile = pd.read_csv(file)
            sell_point = csvfile.iloc[-1]['heikin_ashi_open']
        print('----------------------------\n')


def buy(new_coin_name):
    # 잔고를 보고 매수 할 수 있으면 호가 매수
    balance = binance.fetch_balance()
    if balance['free']['USDT'] >= 10:
        bal = balance['free']['USDT']

        orderbook = binance.fetch_order_book(new_coin_name)

        binance.create_market_buy_order(
            new_coin_name, bal / orderbook['bids'][0][0])

        time.sleep(2)

        if len(binance.fetch_open_orders(new_coin_name)) != 0:
            buy_cancel(new_coin_name)

        text = new_coin_name + '\n매수: $' + \
            str(round(bal, 2)) + '\n매수 가격: $' + str(orderbook['bids'][0][0])
        post_message(slack_token, "#bitcoin", text)

        bought_at = open('bought_at.txt', 'w')
        bought_at.write(str(orderbook['bids'][0][0]))
        bought_at.close()

        last_bought_coin = open('last_coin.txt', 'w')
        last_bought_coin.write(str(new_coin_name))
        last_bought_coin.close()

        last_bought_time = open('last_time.txt', 'w')
        last_bought_time.write(str(dt.now().strftime('%d')))
        last_bought_time.close()


def buy_cancel(new_coin_name):
    order_id = binance.fetch_open_orders(new_coin_name)
    order_id = order_id[0]['info']['orderId']
    binance.cancel_order(int(order_id), new_coin_name)
    buy(new_coin_name)


def sell(new_coin_name):
    sell_coin = new_coin_name[:-5]

    minimum_trade_file = pd.read_csv('minimum_trade.csv')
    amount = float(
        minimum_trade_file.loc[minimum_trade_file['coin'] == sell_coin, 'minimum'])

    # 발랜스 보고 코인으로 잔고가 있으면 호가 매도
    balance = binance.fetch_balance()

    if balance['free'][sell_coin] >= amount:
        binance.create_market_sell_order(
            new_coin_name, balance['free'][sell_coin])

        bal = binance.fetch_balance()
        bal = bal['free'][sell_coin]

        time.sleep(2)

        if bal >= amount:
            sell_cancel(new_coin_name)

        bal = binance.fetch_balance()
        bal = bal['free']['USDT']
        text = new_coin_name + '\n매도: $' + str(round(bal, 2))
        post_message(slack_token, "#bitcoin", text)


def sell_cancel(new_coin_name):
    order_id = binance.fetch_open_orders(new_coin_name)
    order_id = order_id[0]['info']['orderId']
    binance.cancel_order(int(order_id), new_coin_name)
    sell(new_coin_name)


# coin name split
def coin_name(coin):
    coin = i[:-4] + '/' + i[-4:]
    return coin


# posting messages to slack
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
            coin_to_trade.append(temp)
            temp = ''

    coin_to_trade.append(temp)

    # interval check
    interval = data.split('\n')[4]
    time_equal = {'1m': 1, '3m': 3, '5m': 5, '15m': 15,
                  '30m': 30, '1h': 60, '4h': 240, '12h': 720, '1d': 1440}
    time_frame = time_equal[interval]

    # when error occured and restarted program use this to go to con_trade
    for i in coin_to_trade:
        new_coin_name = coin_name(i)
        balance = binance.fetch_balance()
        if (binance.fetch_ticker(new_coin_name)['ask'] * balance[new_coin_name[:-5]]['free']) >= 10:
            coin_trader('%s_DATA_%s.csv' % (i, interval), new_coin_name)

    while True:
        for i in coin_to_trade:
            new_coin_name = coin_name(i)
            # If file does not exist for given time frame and coin make new file
            if not path.exists('%s_DATA_%s.csv' % (i, interval)):
                file_name = '%s_DATA_%s.csv' % (i, interval)
                file = open(file_name, 'w')

            print('\n----------------------------')
            print(dt.now().strftime('%Y-%m-%d %H:%M:%S'))
            print('%s__TRADING' % new_coin_name)
            balance = binance.fetch_balance()
            # when program is running normally use this function
            minimum_trade_file = pd.read_csv('minimum_trade.csv')
            amount = float(
                minimum_trade_file.loc[minimum_trade_file['coin'] == new_coin_name[:-5], 'minimum'])

            candle_data_storage('%s_DATA_%s.csv' %
                                (i, interval), time_frame, i)

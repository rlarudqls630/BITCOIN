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
        df['heikin_ashi_high'] = ''
        df['heikin_ashi_low'] = ''
        df['ema8'] = ''
        df['sma20'] = ''

        df.drop(df.tail(1).index, inplace=True)
        df.to_csv(file, index=False)

    else:
        csvfile = pd.read_csv(file)

        if (binance.fetch_time() - int(csvfile.iloc[-1]['datetime'])) >= (time_frame*60*1000):
            btc_ohlcv = binance.fetch_ohlcv(new_coin_name, interval, int(
                csvfile.iloc[-1]['datetime']), limit=300)
            df = pd.DataFrame(btc_ohlcv, columns=[
                              'datetime', 'open', 'high', 'low', 'close', 'volume'])

            df['heikin_ashi_open'] = ''
            df['heikin_ashi_close'] = ''
            df['heikin_ashi_high'] = ''
            df['heikin_ashi_low'] = ''
            df['ema8'] = ''
            df['sma20'] = ''

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
    csvfile.iat[0, 7] = csvfile.iloc[0]['high']
    csvfile.iat[0, 8] = csvfile.iloc[0]['low']
    csvfile.iat[0, 9] = csvfile.iloc[0]['close']

    for i in range(length):
        # if ema8 is empty
        if pd.isnull(csvfile.loc[i, 'ema8']):
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

                # High = max(high, open, close)
                heikin_ashi_high = max(
                    csvfile.iloc[i]['high'], csvfile.iloc[i]['open'], csvfile.iloc[i]['close'])
                csvfile.iat[i, 8] = heikin_ashi_high

                # low = min(low, open, close)
                heikin_ashi_low = min(
                    csvfile.iloc[i]['low'], csvfile.iloc[i]['open'], csvfile.iloc[i]['close'])
                csvfile.iat[i, 9] = heikin_ashi_low
            # first EMA8 calculation
            if i == 7:
                calc = 0
                calc = csvfile.iloc[0]['heikin_ashi_close'] + csvfile.iloc[1]['heikin_ashi_close']\
                    + csvfile.iloc[2]['heikin_ashi_close'] + csvfile.iloc[3]['heikin_ashi_close']\
                    + csvfile.iloc[4]['heikin_ashi_close'] + csvfile.iloc[5]['heikin_ashi_close']\
                    + csvfile.iloc[6]['heikin_ashi_close'] + \
                    csvfile.iloc[7]['heikin_ashi_close']
                csvfile.iat[i, 10] = calc / 8
            # EMA8 calculation
            if i >= 8:
                calc = (csvfile.iloc[i]['heikin_ashi_close'] - csvfile.iloc[i - 1]
                        ['ema8']) * 0.22 + csvfile.iloc[i - 1]['ema8']
                csvfile.iat[i, 10] = calc
            # SMA 20 calculation
            if i >= 20:
                calc = 0
                for j in range(20):
                    calc = calc + csvfile.iloc[i - j]['heikin_ashi_close']
                csvfile.iat[i, 11] = calc / 20

    csvfile.to_csv(file, index=False)


def live_heikin_ashi_calc(file, new_coin_name):
    csvfile = pd.read_csv(file)

    # Read current OHLCV values
    btc_ohlcv = binance.fetch_ohlcv(new_coin_name, interval, limit=1)

    # Calculating heikin ashi using current values
    heikin_ashi_close = (btc_ohlcv[0][1] + btc_ohlcv[0]
                         [2] + btc_ohlcv[0][3] + btc_ohlcv[0][4]) / 4
    heikin_ashi_open = (
        csvfile.iloc[-1]['heikin_ashi_open'] + csvfile.iloc[-1]['heikin_ashi_close']) / 2
    heikin_ashi_low = min(btc_ohlcv[0][1], btc_ohlcv[0][3], btc_ohlcv[0][4])

    # Caculating EMA and SMA using current values
    ema8 = heikin_ashi_close * 2 / 9 + csvfile.iloc[-1]['ema8'] * 0.78

    calc = 0
    temp = 0
    for i in range(20):
        temp = temp * -1
        calc = calc + csvfile.iloc[temp]['heikin_ashi_open']
    sma20 = (calc + heikin_ashi_close) / 20

    # What coin to trade
    sell_coin = new_coin_name[:-5]

    # Get minimum trading amount for given coin
    minimum_trade_file = pd.read_csv('minimum_trade.csv')
    amount = float(
        minimum_trade_file.loc[minimum_trade_file['coin'] == sell_coin, 'minimum'])

    balance = binance.fetch_balance()

    # If coin was bought, go to trading
    if balance['free'][new_coin_name[:-5]] >= amount:
        if binance.fetch_ticker(new_coin_name)['ask'] * balance['free'][new_coin_name[:-5]] >= 10:
            coin_trader(file, new_coin_name)

    to_buy = False
    print('----------------------------')
    print('BUY CRITERIAS CHECKING......')
    # Buy or not to buy calculation
    if balance['free']['USDT'] >= 10:
        # 양봉 확인
        if heikin_ashi_open < heikin_ashi_close:
            print('POSSIBLE BULL MARKET!!!!')
            if ema8 >= sma20:
                print('-----------CASE 1-----------')
                print('1: EMA8 >= SMA20')
                # current heikin_ashi_close is higher than ema8
                final_calc = binance.fetch_ohlcv(
                    new_coin_name, '1m', limit=3)
                counter = 0
                for j in range(3):
                    minute_heikin_ashi_close = (
                        final_calc[j][1] + final_calc[j][2] + final_calc[j][3] + final_calc[j][4]) / 4
                    if j == 0:
                        minute_heikin_ashi_open = (
                            final_calc[j][1] + final_calc[j][4]) / 2
                    elif j >= 1:
                        minute_heikin_ashi_open = (
                            memorize_open + memorize_close) / 2
                    memorize_open = minute_heikin_ashi_open
                    memorize_close = minute_heikin_ashi_close
                    if memorize_close >= memorize_open:
                        counter = counter + 1
                # 분봉 3개 연속 양봉 확인
                if counter == 3:
                    print('2: 1m BULL MARKET')
                    if final_calc[2][1] < final_calc[2][4]:
                        print('3: ACUTAL PRICE BULL')
                        previous_difference_1 = csvfile.iloc[-1]['heikin_ashi_close'] - \
                            csvfile.iloc[-1]['heikin_ashi_open']
                        previous_difference_2 = csvfile.iloc[-2]['heikin_ashi_close'] - \
                            csvfile.iloc[-2]['heikin_ashi_open']
                        if previous_difference_1 > previous_difference_2:
                            print('4: CANDLES GETTING BIGGER')
                            to_buy = True
                        else:
                            print('FALSE ALARM!!!!')
                    else:
                        print('FALSE ALARM!!!!')
                else:
                    print('FALSE ALARM!!!!')
            else:
                print('-----------CASE 2-----------')
                if csvfile.iloc[-1]['heikin_ashi_open'] >= csvfile.iloc[-1]['heikin_ashi_close']:
                    if csvfile.iloc[-2]['heikin_ashi_open'] >= csvfile.iloc[-2]['heikin_ashi_close']:
                        if csvfile.iloc[-3]['heikin_ashi_open'] >= csvfile.iloc[-3]['heikin_ashi_close']:
                            print('1: THREE BEAR CANDLES')
                            bear_market_check_1 = csvfile.iloc[-1]['heikin_ashi_open'] - \
                                csvfile.iloc[-1]['heikin_ashi_close']
                            bear_market_check_2 = csvfile.iloc[-2]['heikin_ashi_open'] - \
                                csvfile.iloc[-2]['heikin_ashi_close']
                            bear_market_check_3 = csvfile.iloc[-3]['heikin_ashi_open'] - \
                                csvfile.iloc[-3]['heikin_ashi_close']
                            if bear_market_check_3 >= bear_market_check_2 >= bear_market_check_1:
                                print('2: BEAR CANDLE SIZE SHRINKING')
                                if heikin_ashi_open < heikin_ashi_close:
                                    print('3: POSSIBLE BULL MARKET')
                                    final_calc = binance.fetch_ohlcv(
                                        new_coin_name, '1m', limit=3)
                                    counter = 0
                                    for j in range(3):
                                        minute_heikin_ashi_close = (
                                            final_calc[j][1] + final_calc[j][2] + final_calc[j][3] + final_calc[j][4]) / 4
                                        if j == 0:
                                            minute_heikin_ashi_open = (
                                                final_calc[j][1] + final_calc[j][4]) / 2
                                        elif j >= 1:
                                            minute_heikin_ashi_open = (
                                                memorize_open + memorize_close) / 2
                                        memorize_open = minute_heikin_ashi_open
                                        memorize_close = minute_heikin_ashi_close
                                        if memorize_close >= memorize_open:
                                            counter = counter + 1
                                    if counter == 3:
                                        print('4: THREE CONSECUTIVE BULL (1m)')
                                        if final_calc[2][1] < final_calc[2][4]:
                                            print('5: ACUTAL PRICE BULL')
                                            to_buy = True
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
                    print('FALSE ALARM!!!!')
        else:
            print('NOT BULL MARKET')
    print('----------------------------')
    # Final buy check
    if to_buy:
        print('CRITERIAS MET!! BUY!!')
        # sell limit lost (last bearish cancle close value)
        to_sell = True
        count = 1
        while to_sell:
            if csvfile.iloc[-1 * count]['heikin_ashi_close'] < csvfile.iloc[-1 * count]['heikin_ashi_open']:
                sell_at = open('sell_at.txt', 'w')
                sell_at.write(
                    str(csvfile.iloc[-1 * count]['heikin_ashi_close']))
                sell_at.close()
                to_sell = False
            count = count + 1
        buy(new_coin_name)
        coin_trader(file, new_coin_name)


def coin_trader(file, new_coin_name):
    trader = True
    file2 = open('sell_at.txt', 'rt')
    to_sell = float(file2.readline())
    file3 = open('bought_at.txt', 'rt')
    bought = float(file3.readline())

    while trader:
        csvfile = pd.read_csv(file)

        balance = binance.fetch_balance()
        btc_ohlcv = binance.fetch_ohlcv(new_coin_name, interval, limit=1)

        minute_safe_guard = binance.fetch_ohlcv(new_coin_name, '1m', limit=3)
        safe_guard = (max(minute_safe_guard[1][1], minute_safe_guard[1][4]) - (
            abs(minute_safe_guard[1][4] - minute_safe_guard[1][1]) / 10 * 3))
        one_min_bear_or_bull = minute_safe_guard[1][4] - \
            minute_safe_guard[1][1]

        minute_heikin_ashi_open = (
            minute_safe_guard[0][1] + minute_safe_guard[0][4]) / 2
        minute_heikin_ashi_open = (minute_heikin_ashi_open + (
            (minute_safe_guard[1][1] + minute_safe_guard[1][2] + minute_safe_guard[1][3] + minute_safe_guard[1][4]) / 4)) / 2
        minute_heikin_ashi_open = (minute_heikin_ashi_open + (
            (minute_safe_guard[2][1] + minute_safe_guard[2][2] + minute_safe_guard[2][3] + minute_safe_guard[2][4]) / 4)) / 2
        minute_heikin_ashi_close = (
            minute_safe_guard[2][1] + minute_safe_guard[2][2] + minute_safe_guard[2][3] + minute_safe_guard[2][4]) / 4

        print('----------------------------')
        # Status check and show
        print('Trading  :' + new_coin_name)
        print(dt.now().strftime('%Y/%m/%d %H:%M:%S'))
        print('Current     : $' + str(btc_ohlcv[0][4]))
        print('Safe Guard  : $' + str(safe_guard))

        # This code is here to check if there is coin
        # in case user manually sold the coin
        if balance['free']['USDT'] >= 10:
            trader = False

        # get current ohlcv
        btc_ohlcv = binance.fetch_ohlcv(new_coin_name, interval, limit=1)

        # live heikin_ashi_close calc
        heikin_ashi_close = 0.25 * \
            (btc_ohlcv[0][1] + btc_ohlcv[0][2] +
             btc_ohlcv[0][3] + btc_ohlcv[0][4])
        heikin_ashi_open = (
            csvfile.iloc[-1]['heikin_ashi_open'] + csvfile.iloc[-1]['heikin_ashi_close']) / 2

        # previous two candles check
        previous_difference_1 = csvfile.iloc[-1]['heikin_ashi_close'] - \
            csvfile.iloc[-1]['heikin_ashi_open']
        previous_difference_2 = csvfile.iloc[-2]['heikin_ashi_close'] - \
            csvfile.iloc[-2]['heikin_ashi_open']

        print('---------SELL CHECK---------')
        sell_book = binance.fetch_order_book(new_coin_name)
        difference = 100 / bought * sell_book['asks'][0][0] - 100
        if difference >= 0.2:
            print('--------PROFIT CASE --------')
            print('0.2% PROFIT MADE')
            sell(new_coin_name)
            print('SOLD!!!!')
            break
        elif difference > 0.1:
            print('--------PROFIT CASE 2-------')
            print('1: PRICE HIGHER THAN BOUGHT')
            if sell_book['asks'][0][0] > heikin_ashi_close:
                print('2: PRICE HIGHER HEIKIN')
                sell(new_coin_name)
                print('SOLD!!!!')
                break
        # when live heikin_ashi_close is lower than last bearish candle close sell
        if heikin_ashi_close < to_sell:
            print('---------LOSE CASE 1---------')
            print('LOWEST POINT MET')
            sell(new_coin_name)
            print('SOLD!!!!!')
            break
        elif previous_difference_2 < previous_difference_1:
            print('TWO CANDLES SHRINKIKING')
            print('---------LOSE CASE 2---------')
            if heikin_ashi_open > heikin_ashi_close:
                print('1: HEIKIN_ASHI BEARISH')
                btc_ohlcv = binance.fetch_ohlcv(new_coin_name, '1m', limit=3)
                # First candle check
                min_close_1 = 0.25 * \
                    (btc_ohlcv[1][1] + btc_ohlcv[1][2] +
                     btc_ohlcv[1][3] + btc_ohlcv[1][4])
                min_open_1 = 0.5 * (btc_ohlcv[0][1] + btc_ohlcv[0][4])
                # Second candle check
                min_close_2 = 0.25 * \
                    (btc_ohlcv[2][1] + btc_ohlcv[2][2] +
                     btc_ohlcv[2][3] + btc_ohlcv[2][4])
                min_open_2 = 0.5 * (min_close_1 + min_open_1)
                if min_close_1 < min_open_1:
                    if min_close_2 < min_close_2:
                        print('2: 1m TWO CONSECUTIVE LOW')
                        if btc_ohlcv[0][4] < safe_guard:
                            print('3: LOWER THAN SAFE GUARD')
                            sell(new_coin_name)
                            print('SOLD!!!!!')
                            break
                        else:
                            print('FALSE ALARM!!!!')
                    else:
                        print('FALSE ALARM!!!!')
                else:
                    print('FALSE ALARM!!!!')
            else:
                print('FALSE ALARM!!!!')
        else:
            print('NO CRITERIAS MET!!!!')
    print('----------------------------')

    # While checking if new candle has been made go to calculation
    if (binance.fetch_time() - int(csvfile.iloc[-1]['datetime'])) >= (time_frame*60*1000):
        btc_ohlcv = binance.fetch_ohlcv(new_coin_name, interval, int(
            csvfile.iloc[-1]['datetime']), limit=300)
        df = pd.DataFrame(btc_ohlcv, columns=[
            'datetime', 'open', 'high', 'low', 'close', 'volume'])

        df['heikin_ashi_open'] = ''
        df['heikin_ashi_close'] = ''
        df['heikin_ashi_high'] = ''
        df['heikin_ashi_low'] = ''
        df['ema8'] = ''
        df['sma20'] = ''

        df.drop(df.index[0], axis=0, inplace=True)
        df.drop(df.tail(1).index, inplace=True)
        df.to_csv(file, mode='a', header=False, index=False)

        heikin_ashi_calc(file)


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

        time.sleep(2)

        bal = binance.fetch_balance()
        bal = bal['free'][sell_coin]

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
                  '30m': 30, '1h': 60, '4h': 240, '1d': 1440}
    time_frame = time_equal[interval]

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
            # when error occured and restarted program use this to go to con_trade
            if (binance.fetch_ticker(new_coin_name)['ask'] * balance[new_coin_name[:-5]]['free']) >= 10:
                coin_trader('%s_DATA_%s.csv' %
                            (i, interval), new_coin_name)
            # when program is running normally use this function
            else:
                minimum_trade_file = pd.read_csv('minimum_trade.csv')
                amount = float(
                    minimum_trade_file.loc[minimum_trade_file['coin'] == new_coin_name[:-5], 'minimum'])

                candle_data_storage('%s_DATA_%s.csv' %
                                    (i, interval), time_frame, i)

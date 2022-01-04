# Automated Crypto Currency Trader
___
## Introduction
This program is devloped due to high interest in crypto currency market around the globe. It is possible to trade crypto currency manualy using apps, web GUI. However, human hand cannot match the speed of how fast crypto currencies are traded. Also, there are over 100 crypto currencies being traded and it is impossible to track all of them. This is why this program was written.

## Background of how this program was written. 
As it was mentioned in the introduction thare are thousands of crypto currenies being traded and it is not possible to track all of them. Therefore, this program is using several indecators to predict price change of the crypto currencies.
Also, this program is not storing any crypto currency data to your personally pc in order to conserve spaces in your pc and with currenty internet speed, it takes less than a second to fetch and calculate 200 ohlcv(open, high, low, close, volume of crypto currencies) datas. 

## What Does Each File Do
1. Key.txt
    - First line: Binance API key
    - Second line: Secret Binance API key
        * Make sure these two lines are PRIVATE, since using this keys anyone can empty your balance
    - Third line: Slack API key
    - Fourth line: Interval you want to trade in
2. last_bought.txt
    - This file should be empty when you first run the program. Crypto currenty that is written inside this will not be traded and last crypto currency that was exchaned will be updated to the file.
3. swing_low.txt
    - This file contains your crypto crrencies last swing low value.
4. restart.py
    - Since this program is using several repositories and using Binace crypto currency data to process, unexpected error might be raised and progrmam might terminate and we do not want that. This python file restarts main python file(Stocastic_RSI_MACD.py) to restart the program.
5. Stocastic_RSI_MACD.py
    - This is the main program to find and trade crypto currencies. It uses two momentum indicator (RSI, Stocastic) and trend indecator (MACD). In crypto currency market, people tend to hope on to trad to gain profit. Momentum and trend indecator shows this very well. Therefore this program is using mentioned indecators.
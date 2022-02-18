import os
import requests

while True:
    try:
        response = self.conn.getresponse().read()
    except:
        os.system("pip3 install --upgrade pandas")
        os.system("pip3 install ccxt")
        os.system("pip3 install --upgrade ta")
        requests.post("https://slack.com/api/chat.postMessage", headers={"Authorization": "Bearer " + 'xoxb-2099767973728-2069221524710-7gx1Hx2jEzlyV03HEuVKCWsc'}, data={"channel": '#bitcoin', "text": 'Starting........'})
        os.system("python3 /Users/bill_server/Desktop/BITCOIN/Stocastic_RSI_MACD.py")

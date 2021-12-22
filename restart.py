import os
import requests

while True:
    try:
        response = self.conn.getresponse().read()
        print("Trading Program Running!!!!")
    except:
        requests.post("https://slack.com/api/chat.postMessage", headers={"Authorization": "Bearer " + 'xoxb-2099767973728-2069221524710-7gx1Hx2jEzlyV03HEuVKCWsc'}, data={"channel": '#bitcoin', "text": 'Starting........'})
        os.system("python3 /root/code_anywhere/BITCOIN/Stocastic_RSI_MACD.py")
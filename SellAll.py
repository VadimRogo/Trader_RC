import pandas as pd
from binance.client import Client
import re
import time
import json 
import requests 
from datetime import datetime
import matplotlib.pyplot as plt
import math

api_key = 'z7Ltgm7gB1OBsvRiSPCuYOIq7CHMXEVT1ch4vnGuuxZ4I9kaKc7gwLbmd6n3HBJ2'
api_secret = '3h3ylP3VtH6Rtvm83aoHrcI8erMjZfNeX6MAgRGnSHL1srkvu2WcJlUnH1fq59LX'

client = Client(api_key, api_secret)

whitelist = ['COMPUSDT', 'EGLDUSDT', 'BAKEUSDT', 'KEYUSDT', 'RLCUSDT', 'CRVUSDT', 'AVAXUSDT', 'ATOMUSDT', 'GASUSDT', 'SHIBUSDT']
info = client.futures_exchange_info()
precision = 1
def get_precision(symbol):
   for x in info['symbols']:
    if x['symbol'] == symbol:
        precision = x['quantityPrecision']
        if precision == 0 or precision == None:
            precision = 1
        else:
            precision = int(precision)
        return precision

def sell(coin, balance, precision):
    try:
        order = client.order_market_sell(
        symbol = coin,
        quantity = balance
        )
        print(f'Sold  {coin}')
    except Exception as E:
        counter = 0
        quantity = balance
        while quantity >= balance:
            counter += 1
            quantity = quantity * 0.98
            print(coin, quantity, balance, counter)
            math.floor(quantity)
        quantity = round(quantity, precision)
        sell(coin, quantity, precision)

def appendPrices(coin):
    try:
        key = f"https://api.binance.com/api/v3/ticker/price?symbol={coin}"
        data = requests.get(key)   
        data = data.json() 
        price = float(data['price'])
        return price
    except Exception as E:
        print(E)

for coin in whitelist:
    balance = float(client.get_asset_balance(asset=f"{coin.replace('USDT', '')}")['free'])
    balance_usdt = balance * appendPrices(coin)
    if balance_usdt > 5:
        sell(coin, balance, get_precision(coin))

import math




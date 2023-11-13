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

whitelist = ['SOLUSDT', 'ADAUSDT', 'DOGEUSDT', 'TRXUSDT', 'LINKUSDT', 'MATICUSDT', 'DOTUSDT', 'AVAXUSDT', 'LTCUSDT', 'DAIUSDT', 'SHIBUSDT', 'ATOMUSDT', 'XLMUSDT', 'UNIUSDT', 'FILUSDT', 'XMRUSDT', 'LDOUSDT', 'RUNEUSDT', 'QNTUSDT']
info = client.futures_exchange_info()
precision = 1
def get_precision(symbol):
   for x in info['symbols']:
    if x['symbol'] == symbol:
        precision = x['quantityPrecision']
        if precision == 0 or precision == None:
            precision = 0
        else:
            precision = int(precision)
        return precision

def sell(coin, balance, precision):
    try:
        order = client.order_market_sell(
        symbol = coin,
        quantity = round(balance, precision)
        )
        print(f'Sold  {coin}')
    except Exception as E:
        print(E)
        balance = float(client.get_asset_balance(asset=f"{coin.replace('USDT', '')}")['free'])
        quantity = balance
        while quantity >= balance:
            quantity = math.floor(quantity * 10 ** precision) / 10 ** precision
            print(coin, quantity, balance)
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



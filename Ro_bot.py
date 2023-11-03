import pandas as pd
from binance.client import Client
import re
import time
import json 
import requests 
from datetime import datetime
import matplotlib.pyplot as plt
api_key = 'z7Ltgm7gB1OBsvRiSPCuYOIq7CHMXEVT1ch4vnGuuxZ4I9kaKc7gwLbmd6n3HBJ2'
api_secret = '3h3ylP3VtH6Rtvm83aoHrcI8erMjZfNeX6MAgRGnSHL1srkvu2WcJlUnH1fq59LX'

client = Client(api_key, api_secret)

tickers = client.get_all_tickers()
tickers = pd.DataFrame(tickers)
whitelist = ['SNTUSDT', 'BAKEUSDT', 'KEYUSDT', 'RLCUSDT', 'APEUSDT', 'CRVUSDT', 'FILUSDT', 'DEGOUSDT', 'KLAYUSDT', 'PENDLEUSDT', 'YFIUSDT', 'PAXGUSDT', 'WBETHUSDT', 'ETHUSDT', 'MKRUSDT', 'BIFIUSDT', 'BCHUSDT', 'SOLUSDT', 'DASHUSDT', 'ZECUSDT', 'AVAXUSDT', 'ATOMUSDT', 'GASUSDT', 'MANAUSDT', 'SHIBUSDT']
balances, tickets, info = [], [], []
balance = float(client.get_asset_balance(asset='USDT')['free'])
partOfBalance = 11
signalCounter = 0
info = client.futures_exchange_info()
coinInfos = []
counterRsi = 0

def checkTrend(coinInfo):
    if coinInfo['prices'][-1] > coinInfo['prices'][-15]:
        coinInfo['trend'] = True
    else:
        coinInfo['trend'] = False

def checkVolatility(coinInfo):
    deviations = []
    EMA = sum(coinInfo['prices'][:-15:-1]) / 15
    for i in coinInfo['prices'][:-15:-1]:
        deviations.append(abs(EMA - i))
    standartDeviations = sum(deviations) / len(deviations)
    if standartDeviations >= coinInfo['prices'][-1] * 0.002:
        coinInfo['volatility'] = True
    else:
        coinInfo['volatility'] = False
def get_precision(symbol):
   for x in info['symbols']:
    if x['symbol'] == symbol:
        return x['quantityPrecision']
def supportAndDefence(coinInfo):
    support = coinInfo['mins'][-1]
    defence = coinInfo['maxs'][-1]
    if coinInfo['prices'][-1] >= support:
        coinInfo['buySignal'][5] = True
    elif coinInfo['prices'][-1] <= defence:
        coinInfo['buySingnal'][5] = False


def CCIs(coinInfo):
    typicalPrice = coinInfo['prices'][-1]
    MA = sum(coinInfo['prices'][:-15:-1]) / len(coinInfo['prices'][:-15:-1])
    coinInfo['mas'].append(MA)
    if len(coinInfo['mas']) > 15:
        meanDeviation = abs(sum(coinInfo['prices'][:-15:-1]) - sum(coinInfo['mas'][:-15:-1])) / 15
        if meanDeviation != 0:
            CCI = (typicalPrice - MA) / (0.015 * meanDeviation)
            coinInfo['ccis'].append(CCI)
            if coinInfo['ccis'][-1] < -100:
                coinInfo['buySignal'][4] = True
            elif coinInfo['ccis'][-1] > 100:
                coinInfo['buySignal'][4] = False

def Fibo(coinInfo):
    maximum = max(coinInfo['prices'][:-15:-1])
    fibo = [0.786 * maximum, 0.618 * maximum, 0.382 * maximum, 0.236 * maximum]
    percents = 0.02
    lastPrice = coinInfo['prices'][-1]
    if lastPrice < fibo[0] + fibo[0] * percents and lastPrice > fibo[0] - fibo[0] * percents:
        coinInfo['buySignal'][3] = True
    if lastPrice < fibo[1] + fibo[1] * percents and lastPrice > fibo[1] - fibo[1] * percents:
        coinInfo['buySignal'][3] = True
    if lastPrice < fibo[2] + fibo[2] * percents and lastPrice > fibo[2] - fibo[2] * percents:
        coinInfo['buySignal'][3] = True
    if lastPrice < fibo[3] + fibo[3] * percents and lastPrice > fibo[3] - fibo[3] * percents:
        coinInfo['buySignal'][3] = True
    
def Stochastic(coinInfo):
    priceLock = coinInfo['prices'][-1]
    minimum = min(coinInfo['prices'][:15])
    maximum = max(coinInfo['prices'][:15])
    if minimum - maximum != 0:
        Stoch = (priceLock - minimum) / (maximum - minimum) * 100
        coinInfo['stoch'].append(Stoch)
        if len(coinInfo['stoch']) > 10 and Stoch < 20:
            coinInfo['buySignal'][2] = True
        elif Stoch > 70:
            coinInfo['buySignal'][2] = False

def Mcds(coinInfo):
    if len(coinInfo['prices']) > 26:
        long_EMA = sum(coinInfo['prices'][:-26:-1]) / len(coinInfo['prices'][:-26:-1])
        short_EMA = sum(coinInfo['prices'][:-12:-1]) / len(coinInfo['prices'][:-12:-1])
        short_diff_EMA = sum(coinInfo['prices'][:-9:-1]) / len(coinInfo['prices'][:-9:-1])
        coinInfo['long_EMA'].append(long_EMA)
        coinInfo['short_EMA'].append(short_EMA)
        coinInfo['short_diff_EMA'].append(short_diff_EMA)
        MACD = round(coinInfo['short_EMA'][-1] - coinInfo['long_EMA'][-1], 3)
        signal = short_diff_EMA * (short_EMA - long_EMA)
        coinInfo['macds'].append(MACD)
        if len(coinInfo['macds']) > 10 and MACD - signal > -0.6 and MACD - signal < 0.6:
            coinInfo['buySignal'][1] = True
        elif len(coinInfo['macds']) > 10 and MACD - signal > 0.6 and MACD - signal < -0.6:
            coinInfo['buySignal'][1] = False
            
def Rsis(coinInfo):
    global counterRsi
    counterRsi += 1
    difference = coinInfo['prices'][-2] - coinInfo['prices'][-1]
    if (len(coinInfo['prices']) > 2) and difference > 0:
        coinInfo['avg_gain'] += difference
    elif (len(coinInfo['prices']) > 2) and difference < 0:
        difference = abs(difference)
        coinInfo['avg_loss'] += difference
    
    if counterRsi > 25:
        coinInfo['avg_gain'] = 1
        coinInfo['avg_loss'] = 1

    if coinInfo['avg_loss'] > 0 and coinInfo['avg_gain'] > 1:
        RS = coinInfo['avg_gain'] / coinInfo['avg_loss']
        RSI = 100 - (100 / (1 + RS))
        coinInfo['rsis'].append(RSI)
        if RSI < 30 and RSI > 20:
            coinInfo['buySignal'][0] = True
        elif RSI > 70 and RSI < 90:
            coinInfo['buySignal'][0] = False
    

def checkPrecision(coinInfo, precision):
    if precision == 0 or precision == None:
        precision = 1
    else:
        precision = int(precision)
    x = round(coinInfo['prices'][-1], precision)
    return x
def buy(coinInfo, signals):
    try:
        balance = float(client.get_asset_balance(asset='USDT')['free'])
        if float(balance) > partOfBalance:
            now = datetime.now()
            precision = get_precision(coinInfo['symbol'])
            x = checkPrecision(coinInfo, precision)
            if x > 0:
                qty = partOfBalance / x
                qty = round(qty, precision)
                print(qty)
                order = client.create_order(
                    symbol=coinInfo['symbol'],
                    side=Client.SIDE_BUY,
                    type=Client.ORDER_TYPE_MARKET,
                    quantity=qty
                )
                print("Bouth ", coinInfo['symbol'], ' price ', coinInfo['prices'][-1])
                Ticket = {
                    'symbol' : coinInfo['symbol'],
                    'price' : coinInfo['prices'][-1],
                    'takeprofit' : coinInfo['prices'][-1] + coinInfo['prices'][-1] * 0.035,
                    'stoploss' : coinInfo['prices'][-1] - coinInfo['prices'][-1]  * 0.05,
                    'qty' : qty,
                    'time' : now,
                    'sold' : False,
                    'status' : '',
                    'signals' : signals
                }
                tickets.append(Ticket)
    except Exception as E:
        print(E)
        print(coinInfo['symbol'])


def sell(ticket):
    try:
        order = client.order_market_sell(
            symbol=ticket['symbol'],
            quantity=ticket['qty']
            )
        print('Sold ', ticket['symbol'])
        ticket['sold'] = True
        balance = float(client.get_asset_balance(asset='USDT')['free'])
        balances.append(balance)
    except Exception as E:
        print(E)
def appendPrices(coinInfo):
    try:
        key = f"https://api.binance.com/api/v3/ticker/price?symbol={coinInfo['symbol']}"
        data = requests.get(key)   
        data = data.json() 
        price = float(data['price'])
        if len(coinInfo['prices']) > 11:
            coinInfo['mins'].append(min(coinInfo['prices'][:-10:-1]))
            coinInfo['maxs'].append(max(coinInfo['prices'][:-10:-1]))
        coinInfo['prices'].append(price)
    except Exception as E:
        print(E)
def makeCoinsJson(symbol):
    precision = get_precision(symbol)
    if precision == 0 or precision == None:
        precision = 1
    else:
        precision = int(precision)

    coinInfo = {
        'symbol' : symbol,
        'prices' : [],
        'avg_gain' : 1,
        'avg_loss' : 1,
        'rsis' : [],
        'macds' : [],
        'long_EMA' : [],
        'short_EMA' : [],
        'short_diff_EMA' : [],
        'stoch' : [],
        'max' : 1,
        'mas' : [],
        'ccis' : [],
        'volatility' : [],
        'mins' : [],
        'maxs' : [],
        'buySignal' : [False, False, False, False, False, False],
        'precision' : precision,
        'trend' : False
    }
    coinInfos.append(coinInfo)
def parseSignals(coinInfo):
    signals = []
    if coinInfo['buySignal'][0] == True:
        signals.append('RSI')
    if coinInfo['buySignal'][1] == True:
        signals.append('MCDS')
    if coinInfo['buySignal'][2] == True:
        signals.append('STOCH')
    if coinInfo['buySignal'][3] == True:
        signals.append('FIBO')
    if coinInfo['buySignal'][4] == True:
        signals.append('CCI')
    if coinInfo['buySignal'][5] == True:
        signals.append('SUPDEF')
    return signals
def checkIndicators(coinInfo):
    try:
        global signalCounter
        Rsis(coinInfo)
        Mcds(coinInfo)
        Fibo(coinInfo)
        Stochastic(coinInfo)
        CCIs(coinInfo)
        supportAndDefence(coinInfo)
        checkTrend(coinInfo)
        checkVolatility(coinInfo)
        
        for i in coinInfo['buySignal']:
            if i == True:
                signalCounter += 1
            if signalCounter >= 2:
                buy(coinInfo, parseSignals(coinInfo))
                signalCounter = 0
                coinInfo['buySignal'] = [False, False, False, False, False, False]            
    except Exception as E:
        print(E)
def makeStatistic(tickets):
    counterLoss = 1
    counterGain = 1
    for i in tickets:
        if i['status'] == 'loss':
            counterLoss += 1
        elif i['status'] == 'gain':
            counterGain += 1
        statistic = counterGain / counterLoss * 100
        print('Statistic - ', statistic)
    
for coin in whitelist:
    makeCoinsJson(coin)
def checkTicketsToSell(tickets, price, symbol):
    for ticket in tickets:
        if ticket['symbol'] == symbol:
            print('We waiting ', ticket['price'] + ticket['price'] * 0.005)
            if price > ticket['takeprofit']:
                sell(ticket)
                ticket['status'] = 'gain'
            elif price < ticket['stoploss']:
                sell(ticket)
                ticket['status'] = 'loss'

for i in range(1440):
    if i % 10 == 0:
        print('cycle ', i)
    for coinInfo in coinInfos:
        appendPrices(coinInfo)
        balance = float(client.get_asset_balance(asset='USDT')['free'])
        if len(coinInfo['prices']) > 15:
            checkIndicators(coinInfo)
            checkTicketsToSell(tickets, coinInfo['prices'][-1], coinInfo['symbol'][-1])
    time.sleep(30)
        
for ticket in tickets:
    sell(ticket)
makeStatistic(tickets)
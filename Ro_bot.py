import pandas as pd
from binance.client import Client
import re
import time
import json 
import requests 
from datetime import datetime
import matplotlib.pyplot as plt
import math
import telebot
from telebot import types
bot = telebot.TeleBot('6312689394:AAE0wejoCqGdUDprRpXjIc401zCmN21SVl4')


api_key = 'z7Ltgm7gB1OBsvRiSPCuYOIq7CHMXEVT1ch4vnGuuxZ4I9kaKc7gwLbmd6n3HBJ2'
api_secret = '3h3ylP3VtH6Rtvm83aoHrcI8erMjZfNeX6MAgRGnSHL1srkvu2WcJlUnH1fq59LX'

client = Client(api_key, api_secret)

tickers = client.get_all_tickers()
tickers = pd.DataFrame(tickers)

whitelist = ['SOLUSDT', 'ADAUSDT', 'DOGEUSDT', 'TRXUSDT', 'LINKUSDT', 'MATICUSDT', 'DOTUSDT', 'AVAXUSDT', 'LTCUSDT', 'DAIUSDT', 'SHIBUSDT', 'ATOMUSDT', 'XLMUSDT', 'UNIUSDT', 'FILUSDT', 'XMRUSDT', 'LDOUSDT', 'RUNEUSDT', 'QNTUSDT']
balances, tickets, info = [], [], []
balance = float(client.get_asset_balance(asset='USDT')['free'])
partOfBalance = 12
signalCounter = 0
info = client.futures_exchange_info()
coinInfos = []
id = 1660691311
counterRsi = 0
takeProfitPercents = 0.007
stopLossPercents = 0.025

def startTelebot():
    bot.send_message(id, "We start a work, let's see what statistic will be", parse_mode='Markdown')
    

def sendStatistic(statistic, sumt, cycle):
    bot.send_message(id, f' Statistic is {str(statistic)}, num of tickets is {str(len(tickets))}, all income is {sumt}, cycle num {cycle}', parse_mode='Markdown')
def sendLose(symbol):
    bot.send_message(id, f'We need to sell this coin {symbol}')
def carefulMode(Mode):
    global takeProfitPercents, stopLossPercents
    if Mode == True:
        takeProfitPercents = 0.009
        stopLossPercents = 0.025
    else:
        takeProfitPercents = 0.017
        stopLossPercents = 0.045
def checkTrend(coinInfo):
    if coinInfo['prices'][-1] > coinInfo['prices'][-100]:
        coinInfo['trend'] = True
        coinInfo['carefulmode'] = False
        carefulMode(False)
    elif coinInfo['prices'][-1]  > coinInfo['prices'][-15]:
        coinInfo['carefulmode'] = True
        coinInfo['trend'] = True
        carefulMode(True)
    else:
        coinInfo['carefulmode'] = False
        coinInfo['trend'] = False

def checkVolatility(coinInfo):
    deviations = []
    EMA = sum(coinInfo['prices'][:-15:-1]) / 15
    for i in coinInfo['prices'][:-15:-1]:
        deviations.append(abs(EMA - i))
    standartDeviations = sum(deviations) / len(deviations)
    if standartDeviations >= coinInfo['prices'][-1] * 0.022:
        coinInfo['volatility'] = True
    else:
        coinInfo['volatility'] = False
def get_precision(symbol):
   for x in info['symbols']:
    if x['symbol'] == symbol:
        precision = x['quantityPrecision']
        if precision == 0 or precision == None:
            precision = 1
        else:
            precision = int(precision)
        return precision
def checkPrecision(coinInfo, precision):
    if precision == 0 or precision == None:
        precision = 1
    else:
        precision = int(precision)
    x = round(coinInfo['prices'][-1], precision)
    return x
def supportAndDefence(coinInfo):
    support = coinInfo['mins'][-1]
    defence = coinInfo['maxs'][-1]
    if coinInfo['prices'][-1] >= support:
        coinInfo['buySignal'][5] = True
    elif coinInfo['prices'][-1] <= defence:
        coinInfo['buySignal'][5] = False


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
    if len(coinInfo['prices']) > 46:
        maximum = max(coinInfo['prices'][:-45:-1])
        fibo = [0.786 * maximum, 0.618 * maximum, 0.382 * maximum, 0.236 * maximum]
        percents = 0.05
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
    difference = coinInfo['prices'][-2] - coinInfo['prices'][-1]
    if (len(coinInfo['prices']) > 2) and difference > 0:
        coinInfo['avg_gain'] += difference
    elif (len(coinInfo['prices']) > 2) and difference < 0:
        difference = abs(difference)
        coinInfo['avg_loss'] += difference
    
    if len(coinInfo['rsis']) > 75:
        coinInfo['avg_gain'] = 1
        coinInfo['avg_loss'] = 1

    if coinInfo['avg_loss'] > 0 and coinInfo['avg_gain'] > 1:
        RS = coinInfo['avg_gain'] / coinInfo['avg_loss']
        RSI = 100 - (100 / (1 + RS))
        coinInfo['rsis'].append(RSI)
        if RSI < 40 and RSI > 20:
            coinInfo['buySignal'][0] = True
        elif RSI > 60 and RSI < 90:
            coinInfo['buySignal'][0] = False
    

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
                # print(qty)
                order = client.create_order(
                    symbol=coinInfo['symbol'],
                    side=Client.SIDE_BUY,
                    type=Client.ORDER_TYPE_MARKET,
                    quantity=qty
                )
                print("Bouth ", coinInfo['symbol'], ' price ', coinInfo['prices'][-1], 'because', signals)
                Ticket = {
                    'symbol' : coinInfo['symbol'],
                    'price' : coinInfo['prices'][-1],
                    'takeprofit' : coinInfo['prices'][-1] + coinInfo['prices'][-1] * takeProfitPercents,
                    'stoploss' : coinInfo['prices'][-1] - coinInfo['prices'][-1]  * stopLossPercents,
                    'qty' : qty,
                    'time' : now,
                    'sold' : False,
                    'income' : 0,
                    'status' : '',
                    'signals' : signals,
                    'precision' : coinInfo['precision'],
                    'carefulmode' : coinInfo['carefulmode'],
                    'lifeofticket' : 0
                }

                tickets.append(Ticket)
    except Exception as E:
        print(E)
        print(coinInfo['symbol'])


def sell(ticket):
    try:
        balance_coin = float(client.get_asset_balance(asset=f"{ticket['symbol'].replace('USDT', '')}")['free'])
        balance_usdt = balance_coin * ticket['price']
        if balance_usdt > 10:
            order = client.order_market_sell(
                symbol=ticket['symbol'],
                quantity=ticket['qty']
                )
            print('Sold ', ticket['symbol'])
            ticket['sold'] = True 
            balance = float(client.get_asset_balance(asset='USDT')['free'])
            balances.append(balance)
        else:
            sendLose(ticket['symbol'])
            ticket['sold'] = True
    except Exception as E:
        balance_coin = float(client.get_asset_balance(asset=f"{ticket['symbol'].replace('USDT', '')}")['free'])
        balance_usdt = balance_coin * ticket['price']
        if balance_usdt > 10:
            quantity = math.floor(balance_coin * (10 ** ticket['precision']) * 0.999) / (10 ** ticket['precision'])
            qunatity = round(ticket['qty'], ticket['precision'])
            errorSell(ticket, quantity)
            balance = float(client.get_asset_balance(asset='USDT')['free'])
            balances.append(balance)

def errorSell(ticket, quantity):
    try:
        order = client.order_market_sell(
            symbol=ticket['symbol'],
            quantity=quantity
            )
        print('Sold before error', ticket['symbol'])
        ticket['sold'] = True
        balance = float(client.get_asset_balance(asset='USDT')['free'])
        balances.append(balance)
    except Exception as E:
        print(ticket['symbol'])
        print("Okey it doesn't work")
        counter = 0 
        while True:
            try:
                quantity = math.floor(quantity * (10 ** ticket['precision']) * 0.99) / (10 ** ticket['precision'])
                quantity = round(ticket['qty'], ticket['precision'])
                order = client.order_market_sell(
                    symbol=ticket['symbol'],
                    quantity=quantity
                )
                print('sold before error error')
                break
            except:
                counter += 1
                if counter == 5:
                    print('We lose all')
                    sendLose(ticket['symbol'])
                    ticket['sold'] = True
                    break


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
        signalCounter = 0
        Rsis(coinInfo)
        Mcds(coinInfo)
        Fibo(coinInfo)
        Stochastic(coinInfo)
        CCIs(coinInfo)
        # supportAndDefence(coinInfo)
        if len(coinInfo['prices']) >= 100: 
            checkTrend(coinInfo)
        checkVolatility(coinInfo)
        
        for i in coinInfo['buySignal']:
            if i == True:
                signalCounter += 1
            if signalCounter >= 3 and coinInfo['trend'] and coinInfo['volatility']:
                buy(coinInfo, parseSignals(coinInfo))
                signalCounter = 0
                coinInfo['buySignal'] = [False, False, False, False, False, False]            
    except Exception as E:
        print(E)
def makeStatistic(tickets, cycle):
    counterLoss = 1
    counterGain = 1
    sumt = 0
    for i in tickets:
        if i['status'] == 'loss':
            counterLoss += 1
        elif i['status'] == 'gain':
            counterGain += 1
    statistic = counterGain / counterLoss
    for ticket in tickets:
        if ticket['sold'] == True:
            sumt += ticket['income']
    sendStatistic(statistic, sumt, cycle)
    print('Statistic - ', statistic)
    
for coin in whitelist:
    makeCoinsJson(coin)
def checkTicketsToSell(tickets, price, symbol):
    for ticket in tickets:
        if ticket['symbol'] == symbol and ticket['sold'] == False:
            ticket['lifeofticket'] += 1
            if ticket['lifeofticket'] == 50:
                ticket['takeprofit'] =  ticket['takeprofit'] - ticket['takeprofit'] * 0.0045
            if price > ticket['takeprofit']:
                ticket['income'] = ticket['qty'] * ticket['takeprofit'] - ticket['qty'] * ticket['price']
                sell(ticket)
                ticket['status'] = 'gain'
            elif price < ticket['stoploss']:
                ticket['income'] = ticket['qty'] * ticket['stoploss'] - ticket['qty'] * ticket['price']
                sell(ticket)
                ticket['status'] = 'loss'
startTelebot()
for i in range(2880):
    try:
        if i % 10 == 0:
            print('cycle ', i)
        if i % 100 == 0:
            makeStatistic(tickets, i)
        for coinInfo in coinInfos:
            appendPrices(coinInfo)
            balance = float(client.get_asset_balance(asset='USDT')['free'])
            if len(coinInfo['prices']) > 15:
                checkIndicators(coinInfo)
                checkTicketsToSell(tickets, coinInfo['prices'][-1], coinInfo['symbol'])
        time.sleep(30)
    except Exception as E:
        print(E)
        client = Client(api_key, api_secret)

        
for ticket in tickets:
    sell(ticket)
bot.polling(none_stop=True, interval=0)
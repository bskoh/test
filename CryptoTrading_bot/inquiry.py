import pandas as pd
import pyupbit
from coinbase.wallet.client import Client
from time import sleep
import requests
import CONFIG as cfg
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
import time


Tickers_Filted = []

def Filter(tickers):
    result = UnderMBB(tickers)
    Tickers_Filted = Zigzag(result)
    return Tickers_Filted

def Zigzag(tickers):
    w = 20  # 기준 이동평균일
    k = 2
    count = 40
    cnt = 0
    test_arr = []
    #tickers = pyupbit.get_tickers(fiat="KRW")
    for i in range(len(tickers)):
        try:
            df = pyupbit.get_ohlcv(ticker="KRW-CBK", interval="day", count=count) #모든 원화마켓 코인 값 가져온다
            df["mbb"] = df["close"].rolling(w).mean() # 20일 이동평균 금액 가져온다
            df["MA20_std"] = df["close"].rolling(w).std()
            df["ubb"] = df.apply(lambda x: x["mbb"] + k * x["MA20_std"], 1)
            for j in range(w-1, count):# 20일동안의 고가,저가,중간값 가져온다
                high = df.iloc[j][1]
                low = df.iloc[j][2]
                mbb = df.iloc[j][5]
                ubb = df.iloc[j][6]
                #print(high, mbb, low)
                if (mbb < low) and (mbb < high):# 고가와 저가 사이에 중간값이 있으면 배열에 카운팅 한다.
                    cnt += 1
                    if cnt > 15:
                        cnt = 0
                        test_arr.append(tickers[i])
                        break
        except Exception as e:
            print(e)
        print(test_arr)
        time.sleep(0.07)
    return test_arr

def UnderMBB(tickers):
    count = 20
    result = []
    cnt = 0
    for i in range(len(tickers)):
        df = pyupbit.get_ohlcv(ticker=tickers[i], interval="day", count=40)
        df["mbb"] = df["close"].rolling(count).mean()
        df = df.dropna()
        if len(df) < 21:
            continue
        for j in range(0, 5):
            tmp_pre = df.iloc[count - j][3]
            tmp_mbb = df.iloc[count - j][5]
            if (tmp_pre - tmp_mbb) < 0:
                cnt = 0
                break
            else:
                cnt += 1
                if cnt >= 5:
                    result.append(tickers[i])
                    cnt = 0
        time.sleep(0.07)
        print(result)
    return result

def InquiryPriceByTicker(ticker):
    df = pyupbit.get_ohlcv(ticker=ticker, interval="day", count=40)

    w = 20  # 기준 이동평균일
    k = 2  # 기준 상수

    # 중심선 (MBB) : n일 이동평균선
    df["mbb"] = df["close"].rolling(w).mean()
    df["MA20_std"] = df["close"].rolling(w).std()

    # 상한선 (UBB) : 중심선 + (표준편차 × K)
    # 하한선 (LBB) : 중심선 - (표준편차 × K)
    df["ubb"] = df.apply(lambda x: x["mbb"] + k * x["MA20_std"], 1)
    df["lbb"] = df.apply(lambda x: x["mbb"] - k * x["MA20_std"], 1)

    lbb = df["lbb"].tail(1).item()
    mbb = df["mbb"].tail(1).item()
    ubb = df["ubb"].tail(1).item()
    close_price = df["close"].tail(1).item()

    # print('{} 가격: {}원'.format(it['market'], it['trade_price']))
    if close_price >= ubb:
        result = "급등종목 : " + ticker + "가격 : " + str(close_price)
    elif close_price >= mbb:
        result = "사야할 종목 : " + ticker + "가격 : " + str(close_price)
    elif close_price <= lbb:
        result = "급락종목 : " + ticker + "가격 : " + str(close_price)
    else:
        result = "쓰레기 : " + ticker + "가격 : " + str(close_price)
    return result

def GetDominance():
    url = 'https://pro-api.coinmarketcap.com/v1/global-metrics/quotes/latest'
    parameters = {
        'convert': 'BTC'
    }
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': cfg.APIKEY,
    }

    session = Session()
    session.headers.update(headers)

    try:
        response = session.get(url, params=parameters)
        Dominance = json.loads(response.text)['data']['btc_dominance']
        if abs(float(Dominance) - float(cfg.Dominance_pre)) > cfg.DOMINANCE_GAP:
            cfg.Dominance_pre = float(Dominance)
            return Dominance
        else:
            cfg.Dominance_calc += float(cfg.Dominance_pre) - float(Dominance)
            if abs(cfg.Dominance_calc) >= 0.01:
                print(cfg.Dominance_calc)
                Dominance = 'Bitcoin 도미넌스 : ' + str(Dominance) + '%'
                cfg.Dominance_calc = 0
                return Dominance

    except (ConnectionError, Timeout, TooManyRedirects) as e:
        return e

def get_premium():
    #print('start')
    #start = time.time()
    premium = ''        ##return 값 최초 초기화(조건에 안걸릴경우 대비)
    price_gap = 0       ##return 값 최초 초기화(조건에 안걸릴경우 대비)
    #원달러 환율 구하기
    url = 'https://quotation-api-cdn.dunamu.com/v1/forex/recent?codes=FRX.KRWUSD'
    exchange = requests.get(url).json()
    exchange = exchange[0]['basePrice']

    #업비트 BTC 가격 가져오기
    df = pyupbit.get_ohlcv("KRW-BTC",interval="day", count=1)
    UB_price_to_won = int(df.iloc[0][3]) #현재 UPBIT BTC가격(원화)

    #coinbase BTC 가격 가져오기
    client = Client("null", "null")
    price = float(client.get_spot_price(currency_pair="BTC-USD").amount) #현재 coinbase가격(달러)
    CB_price_to_won = round(int(price * exchange),-3) #현재 coinbase가격(원화)

    CB_UB_Premium = round(((CB_price_to_won / UB_price_to_won) - 1) * 100, 2)
    UB_CB_Premium = round(((UB_price_to_won / CB_price_to_won) - 1) * 100, 2)


    #김프, 역프 판별기
    #####################
    ### else 부분이 없어서 premium_calc이 0.01보다 작은경우 선언되지 않은 값을 return해서 에러남
    ### get_dominance 상단에 premium 과 price_gap의 초기값을 선언해줘서 모든 조건에 해당 안될 시 초기값을 return 하게 함
    #####################
    if CB_price_to_won > UB_price_to_won:#역프
        if abs(CB_UB_Premium - cfg.CB_UB_Premium_pre) > cfg.PREMIUM_GAP:
            premium = '역프 : ' + str(CB_UB_Premium) + '%'
            price_gap = CB_price_to_won-UB_price_to_won
            print('역프:',CB_UB_Premium,'%,','현재 BTC 금액은 coinbase기준:',CB_price_to_won,'원, upbit기준:',UB_price_to_won,'원, 차이는',CB_price_to_won-UB_price_to_won,'원')
        else:
            cfg.Premium_calc += cfg.CB_UB_Premium_pre - CB_UB_Premium
            if abs(cfg.Premium_calc) >= 0.01:
                print(cfg.Premium_calc)
                premium = '역프 : ' + str(CB_UB_Premium) + '%'
                price_gap = UB_price_to_won - CB_price_to_won
                cfg.Premium_calc = 0

    else:#김프
        if abs(UB_CB_Premium - cfg.UB_CB_Premium_pre) > cfg.PREMIUM_GAP:
            premium = '김프 : ' + str(UB_CB_Premium) + '%'
            price_gap = UB_price_to_won - CB_price_to_won
            print('김프:',UB_CB_Premium,'%,','현재 BTC 금액은 coinbase기준:',CB_price_to_won,'원, upbit기준:',UB_price_to_won,'원, 차이는',UB_price_to_won-CB_price_to_won,'원')
        else:
            cfg.Premium_calc += cfg.UB_CB_Premium_pre - UB_CB_Premium
            if abs(cfg.Premium_calc) >= 0.01:
                print(cfg.Premium_calc)
                premium = '김프 : ' + str(UB_CB_Premium) + '%'
                price_gap = CB_price_to_won - UB_price_to_won
                cfg.Premium_calc = 0



    #print('end')
    #print(time.time()-start)

    cfg.CB_UB_Premium_pre = CB_UB_Premium
    cfg.UB_CB_Premium_pre = UB_CB_Premium
    return premium, str(price_gap)




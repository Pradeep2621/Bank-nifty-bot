import requests
from datetime import datetime, timedelta
import pandas as pd
import database
import time
from SmartApi import SmartConnect
from logzero import logger
from config import *
import sqlite3
import pyotp
import pandas_ta as ta
import math
import random
from dateutil.relativedelta import relativedelta

Pivot_values = {}


def symbol_token():
    url = "	https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    response = requests.get(url=url)
    df = pd.DataFrame(response.json())
    df.to_csv("Database/instruments_list.csv")
    current_month = (datetime.now().strftime("%b")).upper()

    filtered_df = df[(df["instrumenttype"] == "FUTIDX") & (df["name"] == INDEX)]
    print(filtered_df)
    try:
        symbol_token_bank = filtered_df[filtered_df['symbol'].str.contains(current_month)]['token'].iloc[0]
    except Exception:

        print(Exception)
        next_month = (datetime.now() + relativedelta(months=1)).strftime("%b").upper()
        symbol_token_bank = filtered_df[filtered_df['symbol'].str.contains(next_month)]['token'].iloc[0]

    print(symbol_token_bank)

    return symbol_token_bank


def update_historic_data(symbol_token):
    inter = INTERVAL[CANDLE_TIME]
    obj = SmartConnect(api_key=apikey)
    obj.generateSession(username, pwd, pyotp.TOTP(token).now())

    time.sleep(1)

    date = generate_dates()

    print(f"{str(date)} 09:15")

    print("Symbol Token:", symbol_token)

    try:
        historicParam = {
            "exchange": EXCHANGE,
            "symboltoken": str(symbol_token),
            "interval": inter,
            "fromdate": f"{str(date)} 09:15",
            "todate": f"{str(date)} 15:25"
        }
        yesterday_data = obj.getCandleData(historicParam)['data']
        print(yesterday_data)

        # Convert timestamps to the desired format
        formatted_data = [[datetime.strptime(item[0], "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%dT%H:%M"), *item[1:]]
                          for item in yesterday_data]

        # Create a DataFrame
        df = pd.DataFrame(formatted_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['instrument'] = symbol_token

        # Connect to the SQLite database
        conn = sqlite3.connect("Database/market_data.db")

        # Append the DataFrame to the database table
        df.to_sql('ohlc_data', conn, if_exists='append', index=False)

        # Close the connection
        conn.close()

        # Calculate Pivot points

        filtered_list = [num for sublist in [inner_list[1:-1] for inner_list in yesterday_data] for num in sublist]
        Close_y = yesterday_data[-1][-2]
        High_y = max(filtered_list)
        Low_y = min(filtered_list)

        PP = (High_y + Low_y + Close_y) / 3
        S1 = (2 * PP) - High_y
        R1 = (2 * PP) - Low_y

        Pivot_values[symbol_token] = {
            "PP": PP,
            "S1": S1,
            "R1": R1
        }

        time.sleep(1)

        print(df)

    except Exception as e:
        logger.exception(f"Historic Api failed: {e}")


def createIndicators(instru):
    conn = sqlite3.connect('Database/market_data.db')

    query = f'SELECT * FROM ohlc_data WHERE instrument = "{instru}"'
    dfP = pd.read_sql_query(query, conn)
    timestamp = dfP.iloc[-1, 1]

    # --------------- EMA 20 --------------- #

    EMA_l = 20
    EMA_20 = ta.ema(dfP['close'], EMA_l).iloc[-1]

    # ------------------ MACD ---------------- #
    SLOW = 10
    FAST = 3
    SIGNAL = 16

    MACD_values = ta.macd(dfP["close"], fast=FAST, slow=SLOW, signal=SIGNAL)

    MACD = MACD_values.iloc[:, 0].iloc[-1]
    Signal = MACD_values.iloc[:, 2].iloc[-1]
    Histogram = MACD_values.iloc[:, 1].iloc[-1]

    # ------------------ SUPPER TREND ---------------- #

    ST1 = ta.supertrend(
        high=dfP['high'], low=dfP['low'], close=dfP['close'], length=7, multiplier=2).iloc[:, 0].iloc[-1]
    ST2 = ta.supertrend(
        high=dfP['high'], low=dfP['low'], close=dfP['close'], length=7, multiplier=3).iloc[:, 0].iloc[-1]
    ST3 = ta.supertrend(
        high=dfP['high'], low=dfP['low'], close=dfP['close'], length=10, multiplier=4).iloc[:, 0].iloc[-1]

    # ------------------ VOLUME SMA ---------------- #

    SMA_l = 20
    SMA_9 = 9
    SMAv = ta.sma(dfP['volume'], SMA_9).iloc[-1]
    SMAv9 = ta.sma(dfP['volume'], SMA_l).iloc[-1]
    # ------------------ UPDATE DB ---------------- #

    data_to_add = (instru, timestamp, EMA_20, MACD, Signal, Histogram, ST1, ST2, ST3, SMAv, SMAv9)
    database.append(table_name='indicators', row_data=data_to_add)
    conn.close()


def update_OptionChain():
    obj = SmartConnect(api_key=apikey)
    obj.generateSession(username, pwd, pyotp.TOTP(token).now())
    instru_df = pd.read_csv('Database/instruments_list.csv', low_memory=False)
    instru_df['expiry'] = pd.to_datetime(instru_df['expiry'], format='%d%b%Y')

    df = pd.DataFrame()
    while True:

        bank_nifty_ltp = obj.ltpData("NSE", "Nifty Bank", "99926009")['data']['ltp']

        # Round up to the nearest 100th
        rounded_number = math.ceil(bank_nifty_ltp / 100.0) * 100

        n1 = rounded_number
        n2 = rounded_number

        strike_price = [rounded_number]
        for n in range(1, 20):
            n1 += 100
            n2 -= 100
            strike_price.append(n1)
            strike_price.append(n2)

        option_chain = []
        for price in strike_price:
            t, s = options_token_symbol(price=price, CE_PE='PE', df=instru_df, instru=INDEX)
            option_chain.append([t, s, None])

        header = ['token', 'symbol', 'price']

        OC_df = pd.DataFrame(option_chain, columns=header)

        for index, row in OC_df.iterrows():
            ltp = obj.ltpData("NFO", row['symbol'], row['token'])['data']['ltp']

            row['price'] = ltp
            time.sleep(.5)

        df = pd.concat([df, OC_df], ignore_index=True)

        # Connect to the SQLite database
        conn = sqlite3.connect("Database/market_data.db")
        conn.execute('DELETE FROM option_chain')
        conn.commit()
        df.to_sql('option_chain', conn, index=False, if_exists='append')
        conn.commit()
        conn.close()
        print("Option Chain Got Updated------------------")
        time.sleep(30)


def options_token_symbol(price, CE_PE, df, instru):
    strike_price = price * 100

    df = df[(df['name'] == instru) & df["symbol"].str.contains(CE_PE)]

    # Filter the DataFrame based on the current Thursday's expiry
    filtered_df = (df.loc[(df['strike'] == strike_price)]).sort_values(by='expiry')

    # Get the token from the filtered DataFrame
    token1 = str(filtered_df['token'].values[0])
    symbol = filtered_df['symbol'].values[0]

    return token1, symbol


def calculate_candle_start_time():
    # Get the current time
    current_time = datetime.now().time()

    # Calculate the minutes remaining to the next five-minute interval
    minutes_remaining = 5 - (current_time.minute % 5)

    # Calculate the timedelta to add to the current time
    time_delta = timedelta(minutes=minutes_remaining)

    # Create a datetime object with the current date and time
    current_datetime = datetime.combine(datetime.now().date(), current_time)

    # Add the timedelta to the current datetime
    rounded_datetime = current_datetime + time_delta

    # Format the rounded datetime to the desired format
    formatted_datetime = rounded_datetime.strftime("%Y-%m-%d %H:%M")

    # Return the rounded time
    return formatted_datetime


def execute_trade():
    order_details = {
        "token": None,
        "symbol": None,
        "stratergy_name": None,
        "order_id": None,
        "entry_price": None,
        "entry_time": None,
        "exit_price": None,
        "exit_time": None,
    }

    obj = SmartConnect(api_key=apikey)
    obj.generateSession(username, pwd, pyotp.TOTP(token).now())

    s_token, s_symbol = database.get_token_symbol(INDEX)

    order_details["token"] = s_token
    order_details["symbol"] = s_symbol

    ltp = obj.ltpData(exchange=EXCHANGE, tradingsymbol=s_symbol, symboltoken=s_token)['data']['ltp']
    print(ltp)

    buy_at = ltp * .9  # wait and trade 10% down

    sl_at = buy_at - (buy_at * .07)  # 7% stop loss
    take_profit_at = buy_at + (buy_at * .5)  # 50% Target
    X = .05
    Y = .05

    trail_target = buy_at + (buy_at * X)  # trailing when moves X amount will move SL up by Y amount
    global exit_loop
    exit_loop = False

    while not exit_loop:
        ltp = obj.ltpData(exchange="NFO", tradingsymbol=s_symbol, symboltoken=s_token)['data']['ltp']

        if buy_at > ltp:
            print("Entry triggered and Bought option")
            # TODO punch the order
            # Update the order DICT with entry price and time, exit price and time,
            order_details["entry_price"] = ltp
            order_details["entry_time"] = datetime.now()
            order_details["order_id"] = random.randint(1000000000, 2000000000)
            while True:
                ltp = obj.ltpData(exchange="NFO", tradingsymbol=s_symbol, symboltoken=s_token)['data']['ltp']

                if sl_at > ltp:
                    print("SL Hit")

                    # TODO punch the order
                    # Update the order DICT with entry price and time, exit price and time,
                    order_details["exit_price"] = ltp
                    order_details["exit_time_time"] = datetime.now()
                    exit_loop = True
                    break

                elif take_profit_at < ltp:
                    print("Took profit and exited")

                    # TODO punch the order
                    # Update the order DICT with entry price and time, exit price and time,
                    order_details["exit_price"] = ltp
                    order_details["exit_time_time"] = datetime.now()
                    exit_loop = True
                    break

                elif ltp > trail_target:
                    sl_at = sl_at + (sl_at * Y)
                    trail_target = trail_target + (trail_target * X)

                time.sleep(1)
            database.append(table_name="order book", row_data=tuple(order_details.values()))

        else:
            time.sleep(1)


def generate_dates():
    today = datetime.now().date()
    date_list = [today - timedelta(days=i) for i in range(5)]
    date_dict = {i + 1: date.strftime("%Y-%m-%d") for i, date in enumerate(date_list)}

    print("Select a date:")
    for serial, date_str in date_dict.items():
        print(f"{serial}. {date_str}")

    while True:
        try:
            selected_serial = int(input("Enter the serial number of the desired date: "))
            selected_date = date_dict[selected_serial]
            return selected_date
        except (ValueError, KeyError):
            print("Invalid input. Please enter a valid serial number.")



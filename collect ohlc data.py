import threading
from datetime import datetime, timedelta, time as dt_time
import Supprot_functions
import database
import time
from SmartApi import SmartConnect
from config import *
import pyotp

SYMBOL_TOKEN = Supprot_functions.symbol_token()

Supprot_functions.update_historic_data(SYMBOL_TOKEN)
print("Historic data got updated................")


def update_option_chain_thread():
    Supprot_functions.update_OptionChain()


threading.Thread(target=update_option_chain_thread).start()
print("Option Chain thread started............")

time.sleep(3)

obj = SmartConnect(api_key=apikey)
obj.generateSession(username, pwd, pyotp.TOTP(token).now())

defined_time = dt_time(9, 20)

if datetime.now().time() < defined_time:
    start_time = datetime.combine(datetime.now().date(), defined_time)
    start_time = start_time.strftime('%Y-%m-%d %H:%M')
else:
    start_time = Supprot_functions.calculate_candle_start_time()

print(f"Start Time is: {start_time}\n")

INTERVAL = INTERVAL[CANDLE_TIME]
while True:
    print("Checking for time")
    if datetime.now().strftime('%Y-%m-%d %H:%M') == start_time:
        starting_time = time.time()
        time_object = datetime.strptime(start_time, '%Y-%m-%d %H:%M')
        candle_time = (time_object - timedelta(minutes=CANDLE_TIME)).strftime('%Y-%m-%d %H:%M')
        print("I AM candle Time:", candle_time)
        while True:
            historicParam = {
                "exchange": EXCHANGE,
                "symboltoken": SYMBOL_TOKEN,
                "interval": INTERVAL,
                "fromdate": candle_time,
                "todate": candle_time
            }
            data = obj.getCandleData(historicParam)['data']

            if data is None:
                print("Found None Waiting")
                time.sleep(.5)
            else:
                data = data[0]
                parsed_date = datetime.strptime(data[0], '%Y-%m-%dT%H:%M:%S%z')
                # Format the datetime object to the desired format
                formatted_date = parsed_date.strftime('%Y-%m-%d %H:%M')

                ohlc_tuple = (SYMBOL_TOKEN, formatted_date, data[1], data[2], data[3], data[4], data[5])

                database.append(table_name="ohlc_data", row_data=ohlc_tuple)

                print(ohlc_tuple)

                print("ohlc Updated")
                Supprot_functions.createIndicators(SYMBOL_TOKEN)
                print("indicators Updated")

                time_object = datetime.strptime(start_time, '%Y-%m-%d %H:%M')

                start_time = (time_object + timedelta(minutes=CANDLE_TIME)).strftime('%Y-%m-%d %H:%M')
                print(f"Start Time is: {start_time}\n")

                end_time = time.time()
                elapsed_time = end_time - starting_time
                print(f"Time taken: {elapsed_time:.2f} seconds")
                print("Waiting for next Candle cycle....:", SLEEP_SEC)
                time.sleep(SLEEP_SEC)
                break

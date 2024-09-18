from datetime import datetime
import database
import time
from config import *
import Supprot_functions

# Market Timing
START_TIME = "9:19"
END_TIME = "15:30"

db = database.DB()

dataUpdated, last_row = database.dataUpdated(0)

current_time = datetime.now().strftime('%H:%M')

while True:
    current_time = datetime.now().strftime('%H:%M')
    if START_TIME < current_time < END_TIME:
        print("passed 1")
        dataUpdated, row_id = database.dataUpdated(last_row)

        if dataUpdated:
            print("passed 2")
            last_row = row_id
            db.update_latest_values()
            if db.Latest_close < db.ST3 and \
                    db.Latest_close < db.ST2 and \
                    db.Latest_close < db.ST1 and \
                    db.SMAv20 > db.Volume_close:
                print("Trade Found_________________________")
                # TODO execute the trade
                Supprot_functions.execute_trade()

            else:
                print("Trade NOT Found__________WAITING For Trade_______________")
                time.sleep(SLEEP_SEC)
    elif current_time > END_TIME:
        break

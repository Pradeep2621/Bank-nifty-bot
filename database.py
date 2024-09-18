import sqlite3
import time

database_name = "Database/market_data.db"


def append(table_name, row_data):
    db = sqlite3.connect(database_name)
    curses = db.cursor()

    curses.execute(F"INSERT INTO {table_name} VALUES {row_data}")

    db.commit()
    db.close()


def dataUpdated(last_row):
    conn = sqlite3.connect(database_name)
    cursor = conn.cursor()

    cursor.execute(f'SELECT MAX(rowid) FROM indicators')
    last_row_id = cursor.fetchone()[0]
    print(last_row_id)

    return last_row < last_row_id, last_row_id


def get_token_symbol(symbol):
    conn = sqlite3.connect(database_name)
    cursor = conn.cursor()

    cursor.execute(f"""
    SELECT * 
    FROM option_chain 
    WHERE 
    symbol LIKE '{symbol}%' AND 
    price > 45 AND 
    price < 55
    """)

    data = cursor.fetchone()

    if data is None:
        cursor.execute(f"""
            SELECT *
            FROM option_chain 
            WHERE 
            symbol LIKE '{symbol}%' AND 
            price < 55
            """)

        data = cursor.fetchone()

    token = data[0]
    symbol = data[1]

    return token, symbol


class DB:
    def __init__(self):
        # Initializing attributes with None
        self.EMA20 = None
        self.MACD = None
        self.Signal = None
        self.Histogram = None
        self.ST1 = None
        self.ST2 = None
        self.ST3 = None
        self.SMAv20 = None
        self.SMAv9 = None
        self.Latest_close = None
        self.Volume_close = None

    def update_latest_values(self):
        conn = sqlite3.connect(database_name)
        cursor = conn.cursor()

        cursor.execute(f'''
        SELECT *
        FROM indicators
        ORDER BY ROWID 
        DESC LIMIT 1
        ''')

        last_updated_data = cursor.fetchone()
        print(last_updated_data)

        self.EMA20 = last_updated_data[2]
        self.MACD = last_updated_data[3]
        self.Signal = last_updated_data[4]
        self.Histogram = last_updated_data[5]
        self.ST1 = last_updated_data[6]
        self.ST2 = last_updated_data[7]
        self.ST3 = last_updated_data[8]
        self.SMAv20 = last_updated_data[9]
        self.SMAv9 = last_updated_data[10]

        cursor.execute(f'''
                SELECT *
                FROM ohlc_data 
                ORDER BY ROWID 
                DESC LIMIT 1
                ''')

        last_updated_data = cursor.fetchone()
        self.Latest_close = last_updated_data[5]
        self.Volume_close = last_updated_data[6]






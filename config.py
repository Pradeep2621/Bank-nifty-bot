
apikey = 'api key'
username = 'User name'
pwd = 'your password'
token = 'token'
INTERVAL = {
    1: "ONE_MINUTE",
    3: "THREE_MINUTE",
    5: "FIVE_MINUTE",
    10: "TEN_MINUTE",
    15: "FIFTEEN_MINUTE",
    30: "THIRTY_MINUTE",
    60: "ONE_HOUR",
    "DAY": "ONE_DAY",
}


# Inputs


INDEX = "BANKNIFTY"
EXCHANGE = "NFO"  # NFO for Future and Options and NSE for INDEX MCX for Commodities
CANDLE_TIME = 5  # like 1 minute candle 5 min candle etc
SLEEP_SEC = (CANDLE_TIME * 60) - 10


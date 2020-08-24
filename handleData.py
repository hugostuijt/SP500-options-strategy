import pandas as pd
from pathlib import Path
import numpy as np
import pandas_market_calendars as mcal
from datetime import datetime
import calendar


def next3rdFriday(date):
    date = datetime.strptime(date, '%Y-%m-%d')
    year = date.year
    month = date.month

    c = calendar.Calendar(firstweekday=calendar.SUNDAY)
    monthcal = c.monthdatescalendar(year, month)
    friday = [day for week in monthcal for day in week if day.weekday() == calendar.FRIDAY and day.month == month][2]

    return pd.Timestamp(friday)


# ========== IMPORT THE RAW DATA AND CONVERT DATES, ETC =============================

raw = pd.read_csv(r"C:\Users\hwstu\OneDrive\Documents\Projects\SPX options strategy\raw_data2.csv")
raw['strike_price'] = raw['strike_price'] / 1000

# Change date formats
temp = raw['date'].astype(str)
raw['date'] = pd.to_datetime(temp.str[0:4] + '/' + temp.str[4:6] + '/' + temp.str[6:8])
temp = raw['exdate'].astype(str)
raw['exdate'] = pd.to_datetime(temp.str[0:4] + '/' + temp.str[4:6] + '/' + temp.str[6:8])

# Count business days
A = [d.date() for d in raw['date']]
B = [d.date() for d in raw['exdate']]
raw['days'] = np.busday_count(A, B)

# ========== WE CAN NOW WORK WIT THE DATA TO SELECT ALL OUR TRADING DAYS ===================

outputCols = ['date', 'exdate', 'days', 'strike_price', 'best_bid', 'best_offer']
output = pd.DataFrame(columns=outputCols)
startDate = '2000-01-01'
endDate = '2019-06-30'
# All CBOE trading days (thus excluding holidays)
CBOEtrading = mcal.get_calendar('CFE').schedule(startDate, endDate)
tradingDates = CBOEtrading.index.to_series().reset_index(drop=True)

holdingperiod = 3 * 5 * 4  # 60 trading days for a 3 month holding period.

buyDate = next3rdFriday(startDate)
# we now have the 3rd friday, but want the next trading day
loc = tradingDates[tradingDates == buyDate].index[0]
buyDate = tradingDates[loc + 1]

maturities = raw.loc[raw['date'] == buyDate, 'days']
idx = maturities.sub(holdingperiod).abs().idxmin()
maturity = maturities[idx]

temp = raw.loc[(raw['date'] == buyDate) & (raw['days'] == maturity)]
output.append()

temp = raw[raw['date'] == buyDate]

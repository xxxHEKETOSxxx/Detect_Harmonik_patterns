import MetaTrader5 as mt5
import pandas as pd
import pandas_ta as ta
import pytz
from scipy import stats
from math import atan, radians, degrees
import time
from datetime import datetime
import numpy as np
from pandas import DataFrame, Series
import warnings
warnings.filterwarnings("ignore")



if not mt5.initialize():
    print("initialize() failed, error code =", mt5.last_error())
    quit()
symbol = 'AUDCADb'

timezone = pytz.timezone("Etc/UTC")
utc_from = datetime(2021, 1, 20, tzinfo=timezone)
utc_to = datetime(2023, 12, 20, tzinfo=timezone)
rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_H1, utc_from, utc_to)
rates_frame = pd.DataFrame(rates)

warnings.filterwarnings("ignore")

pd.set_option('display.max_columns', 500)  # сколько столбцов показываем
pd.set_option('display.max_rows', 5000)  # сколько столбцов показываем
pd.set_option('display.width', 1500)  # макс. ширина таблицы для показа

if not mt5.initialize():
    print("initialize() failed, error code =", mt5.last_error())
    quit()
symbol = 'EURUSD'
timezone = pytz.timezone("Etc/UTC")
utc_from = datetime(2023, 1, 1, tzinfo=timezone)
utc_to = datetime(2024, 12, 31, tzinfo=timezone)
rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M15, utc_from, utc_to)
rates_frame = pd.DataFrame(rates)
rates_frame['time'] = pd.to_datetime(rates_frame['time'], unit='s')


# Функция расчета индикатора ZigZag
def zigzag(df):
    bull = df["close"] >= df["open"]
    bear = df["close"] <= df["open"]

    trend = bull.astype(int).replace(0, -1).replace([np.nan], method="ffill")

    peak = (bull & bear.shift(1)).astype(bool)
    bottom = (bear & bull.shift(1)).astype(bool)

    zigzag_series = np.select([peak, bottom], [df['high'], df['low']], np.nan)
    zigzag_series = pd.Series(zigzag_series)
    zigzag_series = zigzag_series.ffill()

    peaks = zigzag_series[peak].dropna().tail(5).values

    # Последние 5 впадин
    bottoms = zigzag_series[bottom].dropna().tail(5).values

    x = peaks[-5]
    a = peaks[-4]
    b = peaks[-3]
    c = peaks[-2]
    d = peaks[-1]

    return zigzag_series, trend, x, a, b, c, d


zigzag_data, trend, x, a, b, c, d = zigzag(rates_frame)
rates_frame['TREND'] = trend
rates_frame['ZIGZAG'] = zigzag_data

xab = np.abs(b - a) / np.abs(x - a)
xad = np.abs(a - d) / np.abs(x - a)
abc = np.abs(b - c) / np.abs(a - b)
bcd = np.abs(c - d) / np.abs(b - c)

fib_range = np.abs(c - d)


def fib_levels(c, d):
    levels = []

    levels.append(c + (0 * fib_range))
    levels.append(c + (0.236 * fib_range))
    levels.append(c + (0.382 * fib_range))
    levels.append(c + (0.5 * fib_range))
    levels.append(c + (0.618 * fib_range))
    levels.append(c + (1 * fib_range))

    if d > c:
        return np.array(levels)[::-1]
    else:
        return np.array(levels)


fib_levels = fib_levels(c, d)

print(fib_levels)


# Бэт
def isBat(mode):
    _xab = (xab >= 0.382) and (xab <= 0.5)
    _abc = (abc >= 0.382) and (abc <= 0.886)
    _bcd = (bcd >= 1.618) and (bcd <= 2.618)
    _xad = (xad <= 0.618) and (xad <= 1.000)

    return _xab and _abc and _bcd and _xad and (d < c if mode == 1 else d > c)



def isAntiBat(mode):
    _xab = (xab >= 0.500) and (xab <= 0.886)
    _abc = (abc >= 1.000) and (abc <= 2.618)
    _bcd = (bcd >= 1.618) and (bcd <= 2.618)
    _xad = (xad >= 0.886) and (xad <= 1.000)

    return _xab and _abc and _bcd and _xad and (d < c if mode == 1 else d > c)


def isAltBat(mode):
    _xab = (xab <= 0.382)
    _abc = (abc >= 0.382) and (abc <= 0.886)
    _bcd = (bcd >= 2.0) and (bcd <= 3.618)
    _xad = (xad <= 1.13)

    return _xab and _abc and _bcd and _xad and (d < c if mode == 1 else d > c)


def isButterfly(mode):
    _xab = (xab <= 0.786)
    _abc = (abc >= 0.382) and (abc <= 0.886)
    _bcd = (bcd >= 1.618) and (bcd <= 2.618)
    _xad = (xad >= 1.27) and (xad <= 1.618)

    return _xab and _abc and _bcd and _xad and (d < c if mode == 1 else d > c)


# Анти Бабочка
def isAntiButterfly(mode):
    _xab = (xab >= 0.236) and (xab <= 0.886)
    _abc = (abc >= 1.130) and (abc <= 2.618)
    _bcd = (bcd >= 1.000) and (bcd <= 1.382)
    _xad = (xad >= 0.500) and (xad <= 0.886)

    return _xab and _abc and _bcd and _xad and (d < c if mode == 1 else d > c)



def isABCD(mode):
    _abc = (abc >= 0.382) and (abc <= 0.886)
    _bcd = (bcd >= 1.13) and (bcd <= 2.618)

    return _abc and _bcd and (d < c if mode == 1 else d > c)


def isGartley(mode):
    _xab = (xab >= 0.5) and (xab <= 0.618)
    _abc = (abc >= 0.382) and (abc <= 0.886)
    _bcd = (bcd >= 1.13) and (bcd <= 2.618)
    _xad = (xad >= 0.75) and (xad <= 0.875)

    return _xab and _abc and _bcd and _xad and (d < c if mode == 1 else d > c)


def isAntiGartley(mode):
    _xab = (xab >= 0.500) and (xab <= 0.886)
    _abc = (abc >= 1.000) and (abc <= 2.618)
    _bcd = (bcd >= 1.500) and (bcd <= 5.000)
    _xad = (xad >= 1.000) and (xad <= 5.000)

    return _xab and _abc and _bcd and _xad and (d < c if mode == 1 else d > c)


def isCrab(mode):
    _xab = (xab >= 0.500) and (xab <= 0.875)
    _abc = (abc >= 0.382) and (abc <= 0.886)
    _bcd = (bcd >= 2.000) and (bcd <= 5.000)
    _xad = (xad >= 1.382) and (xad <= 5.000)

    return _xab and _abc and _bcd and _xad and (d < c if mode == 1 else d > c)


def isAntiCrab(mode):
    _xab = (xab >= 0.250) and (xab <= 0.500)
    _abc = (abc >= 1.130) and (abc <= 2.618)
    _bcd = (bcd >= 1.618) and (bcd <= 2.618)
    _xad = (xad >= 0.500) and (xad <= 0.750)

    return _xab and _abc and _bcd and _xad and (d < c if mode == 1 else d > c)



def isShark(mode):
    _xab = (xab >= 0.500) and (xab <= 0.875)
    _abc = (abc >= 1.130) and (abc <= 1.618)
    _bcd = (bcd >= 1.270) and (bcd <= 2.240)
    _xad = (xad >= 0.886) and (xad <= 1.130)

    return _xab and _abc and _bcd and _xad and (d < c if mode == 1 else d > c)



def isAntiShark(mode):
    _xab = (xab >= 0.382) and (xab <= 0.875)
    _abc = (abc >= 0.500) and (abc <= 1.000)
    _bcd = (bcd >= 1.250) and (bcd <= 2.618)
    _xad = (xad >= 0.500) and (xad <= 1.250)

    return _xab and _abc and _bcd and _xad and (d < c if mode == 1 else d > c)



def is5o(mode):
    _xab = (xab >= 1.13) and (xab <= 1.618)
    _abc = (abc >= 1.618) and (abc <= 2.24)
    _bcd = (bcd >= 0.5) and (bcd <= 0.625)
    _xad = (xad >= 0.0) and (xad <= 0.236)

    return _xab and _abc and _bcd and _xad and (d < c if mode == 1 else d > c)


def isWolf(mode):
    _xab = (xab >= 1.27) and (xab <= 1.618)
    _abc = (abc >= 0) and (abc <= 5)
    _bcd = (bcd >= 1.27) and (bcd <= 1.618)
    _xad = (xad >= 0.0) and (xad <= 5)

    return _xab and _abc and _bcd and _xad and (d < c if mode == 1 else d > c)

def isHnS(mode):
    _xab = (xab >= 2.0) and (xab <= 10)
    _abc = (abc >= 0.90) and (abc <= 1.1)
    _bcd = (bcd >= 0.236) and (bcd <= 0.88)
    _xad = (xad >= 0.90) and (xad <= 1.1)
    return _xab and _abc and _bcd and _xad and (d < c if mode == 1 else d > c)


def isConTria(mode):
    _xab = (xab >= 0.382) and (xab <= 0.618)
    _abc = (abc >= 0.382) and (abc <= 0.618)
    _bcd = (bcd >= 0.382) and (bcd <= 0.618)
    _xad = (xad >= 0.236) and (xad <= 0.764)

    return _xab and _abc and _bcd and _xad and (d < c if mode == 1 else d > c)

def isExpTria(mode):
    _xab = (xab >= 1.236) and (xab <= 1.618)
    _abc = (abc >= 1.000) and (abc <= 1.618)
    _bcd = (bcd >= 1.236) and (bcd <= 2.000)
    _xad = (xad >= 2.000) and (xad <= 2.236)

    return _xab and _abc and _bcd and _xad and (d < c if mode == 1 else d > c)



SIGNAL_b = np.where((isABCD(1) or (isAltBat(1)) or (isAltBat(1)) or (isButterfly(1)) or (isGartley(1)) or (
    isCrab(1)) or (isShark(1)) or (is5o(1)) or (isWolf(1)) or (isHnS(1)) or (isConTria(1)) or (isExpTria(1))),1,0)
SIGNAL_s = np.where((isABCD(-1) or (isAltBat(-1)) or (isAltBat(-1)) or (isButterfly(-1)) or (isGartley(-1)) or (
    isCrab(-1)) or (isShark(-1)) or (is5o(-1)) or (isWolf(-1)) or (isHnS(-1)) or (isConTria(-1)) or ( isExpTria(-1))), -1,0)


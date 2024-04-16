"""
    This module calculates simple returns on ohlc data.  
"""
import math 
import sys

# set root path
sys.path.append('..')
from interface import interface_localDB as db

""" 
    This function calculates the number of shares that can be bought
    Inputs:
        - cash: [float] amount of cash available to buy shares
        - price: [float] price of the stock
    Returns:
        - shares: [int] number of shares that can be bought
"""
def calcShares(cash, price):
    numShares = math.floor(cash/price)
    return numShares

"""
    This function calculates the absolute $ return between two dates
    Inputs:
        - history: [pd.DataFrame] ohlc data
        - start: [str] start date
        - end: [str] end date
        - direction: [str] 'long' or 'short'
        - cash: [float] amount of cash available to buy shares
    Returns:
        - return_: [float] absolute $ return
"""
def calcReturnBetweenDates(history, start, end, direction, cash=10000):
    start_price = history.loc[history['date'] == start, 'close'].values[0]
    end_price = history.loc[history['date'] == end, 'close'].values[0]

    # if either is empty, exit
    if start_price == None or end_price == None:
        print('start or end date yielded no price data')
        return None
    
    if direction == 'long':
        return_ = end_price - start_price
    elif direction == 'short':
        return_ = start_price - end_price

    quantity = calcShares(cash, start_price)

    return return_ * quantity

"""
    calculates sharpe ratio for a given returns dataframe
    Params:
    @returns: [pd.DataFrame] dataframe with log returns
    @underlying_df: [pd.DataFrame] dataframe with underlying ohlc data
    @rfrate: [float] risk free rate
    @periods: [int] number of periods per year
"""
def calcSharpeRatio(returns, underlying_df, rfrate=0.0487, periods=12):
    # return sharpe ratio
    sharpe = (returns['logReturn'].mean() - rfrate) / underlying_df['logReturn'].std()
    return sharpe
import math
import pandas as pd 

"""
    This function calculates log returns on the passed in values 
    inputs:
        - history - dataframe of timeseries data 
        - colName - name of the column to calculate log returns on
    output:
        - history with a log return column added
"""
def calcLogReturns(history, colName):
    # calculate log returns as ln(today's close price / yesterday's close price)
    history['logReturn'] = history[colName].apply(lambda x: math.log(x)) - history[colName].shift(1).apply(lambda x: math.log(x))
    
    return history

"""
    returns a string of the current date in YYYYMM format
"""
def futures_getExpiryDateString():
    return pd.Timestamp.today().strftime('%Y%m')

"""
    Returns volume mean and sd grouped by month
    inputs:
        - history: dataframe of 1day ohlcv data
    outputs:
        - dataframe with columns: [month, volume_mean, volume_sd]
"""
def aggregate_volume_month(history):
    # throw error if interval is not 1day
    if history['interval'][0] != '1day':
        raise ValueError('interval must be 1day')
    
    # convert date column to datetime
    history['date'] = pd.to_datetime(history['date'])

    # sort by date
    history = history.sort_values(by='date')

    # add month column
    history['month'] = history['date'].dt.month

    # group by month and get mean and sd of volume
    volume_month = history.groupby('month')['volume'].agg(['mean', 'std']).reset_index()

    return volume_month

"""
    Returns volume mean and sd grouped by day of month
    inputs:
        - history: dataframe of 1day ohlcv data
    outputs:
        - dataframe with columns: [month, volume_mean, volume_sd]
"""
def aggregate_volume_dayOfMonth(history):
    # throw error if interval is not 1day
    if history['interval'][0] != '1day':
        raise ValueError('interval must be 1day')
        
    # convert date column to datetime
    history['date'] = pd.to_datetime(history['date'])

    # sort by date
    history = history.sort_values(by='date')

    # add month column
    history['dayOfMonth'] = history['date'].dt.day

    # group by month and get mean and sd of volume
    volume_dayOfMonth = history.groupby('dayOfMonth')['volume'].agg(['mean', 'std']).reset_index()

    return volume_dayOfMonth
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
    return history.reset_index(drop=True)

"""
    returns a string of the current date in YYYYMM format
"""
def futures_getExpiryDateString():
    return pd.Timestamp.today().strftime('%Y%m')

"""
    Returns mean and sd of target column grouped by month
    inputs:
        - history: dataframe of 1day ohlcv data
        - targetCol: str of column to aggregate
    outputs:
        - dataframe with columns: [month, volume_mean, volume_sd]
"""
def aggregate_by_month(history, targetCol):
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
    aggregate_by_month = history.groupby('month')[targetCol].agg(['mean', 'std']).reset_index()

    return aggregate_by_month

"""
    Returns mean and sd of tagetcol grouped by day of month
    inputs:
        - history: dataframe of 1day ohlcv data
        - targetCol: str of column to aggregate
    outputs:
        - dataframe with columns: [month, volume_mean, volume_sd]
"""
def aggregate_by_dayOfMonth(history, targetCol):
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
    aggregate_by_dayOfMonth = history.groupby('dayOfMonth')[targetCol].agg(['mean', 'std']).reset_index()

    return aggregate_by_dayOfMonth


"""
    Returns means and sd of tagetCol grouped by day of week
    inputs:
        - history: dataframe of 1day ohlcv data
        - targetCol: str of column to aggregate
    outputs:
        - dataframe with columns: [dayofweek, mean, sd]
"""
def aggregate_by_dayOfWeek(history, targetCol):
    # throw error if interval is not 1day
    if history['interval'][0] != '1day':
        raise ValueError('interval must be 1day')
        
    # convert date column to datetime
    history['date'] = pd.to_datetime(history['date'])

    # sort by date
    history = history.sort_values(by='date')

    # add month column
    history['dayOfWeek'] = history['date'].dt.dayofweek

    # group by month and get mean and sd of volume
    aggregate_by_dayOfWeek = history.groupby('dayOfWeek')[targetCol].agg(['mean', 'std']).reset_index()

    return aggregate_by_dayOfWeek

"""
    Returns mean and sd of tagetCol grouped by timestamp 
    inputs:
        - history: dataframe of <1day ohlcv data with date column in format 'YYYY-MM-DD HH:MM:SS'
        - targetCol: str of column to aggregate
    outputs:
        - dataframe with columns: [timestamp, mean, sd]
"""
def aggregate_by_timestamp(history, targetCol):
        
    # convert date column to datetime if it is not already
    if history['date'].dtype != 'datetime64[ns]':
        history['date'] = pd.to_datetime(history['date'])

    # sort by date
    history = history.sort_values(by='date')

    # add month column
    history['timestamp'] = history['date'].dt.strftime('%H:%M:%S')

    # group by month and get mean and sd of volume
    aggregate_by_timestamp = history.groupby('timestamp')[targetCol].agg(['mean', 'std']).reset_index()

    return aggregate_by_timestamp
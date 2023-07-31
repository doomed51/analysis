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

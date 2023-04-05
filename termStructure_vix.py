"""
This module returns VIX term structure as a dataframe, and contains helper functions to simplify preparing term structure data for analysis. 
"""
import pandas as pd

## read in vix term structure data
vix_ts_raw = pd.read_csv('vix.csv')

# convert date column to datetime
vix_ts_raw['Date'] = pd.to_datetime(vix_ts_raw['Date'])

# set date as index
vix_ts_raw.set_index('Date', inplace=True)

""" 
Returns raw vix term structure data
"""
def getRawVixTermStructure():
    return vix_ts_raw

"""
Returns vix term structure data with percent change between n and n+1 month futures
----------------
Params: 
    fourToSeven: bool, default False
        if True, adds a column to the dataframe that is the percent difference between the 4th and 7th month futures
    currentToLast: bool, default False
        if True, adds a column to the dataframe that is the percent difference between the current and longest term future

"""
def getVixTermStructurePctContango(fourToSeven = False, currentToLast = False):
    # create a new df with the percent change between n and n+1 month futures
    vix_ts_pctContango = vix_ts_raw.pct_change(axis='columns', periods=-1).drop(columns='8')*-1

    if fourToSeven:
        # add contango from the 4th to 7th month
        vix_ts_raw['fourToSevenMoContango'] = (vix_ts_raw['6'] - vix_ts_raw['3'])/vix_ts_raw['3']
        vix_ts_pctContango = vix_ts_pctContango.join(vix_ts_raw['fourToSevenMoContango'], on='Date')

    if currentToLast:
        # add contango between current and longest term future
        vix_ts_raw['currentToLastContango'] = (vix_ts_raw['8'] - vix_ts_raw['0'])/vix_ts_raw['0']
        vix_ts_pctContango = vix_ts_pctContango.join(vix_ts_raw['currentToLastContango'], on='Date')

    return vix_ts_pctContango


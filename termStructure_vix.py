"""
This module consists of two functions that return VIX term structure, and contango values between contracts.
    - getRawVixTermStructure(): returns the raw vix term structure data
    - getVixTermStructurePctContango(): returns the percent change between n and n+1 month futures, and optionally adds columns for contango between the 4th and 7th month futures, and contango between the current and longest term future

"""
import pandas as pd

## read in vix term structure data
vix_ts_raw = pd.read_csv('vix.csv')

# convert date column to datetime
vix_ts_raw['date'] = pd.to_datetime(vix_ts_raw['date'], format='mixed')

# set date as index
vix_ts_raw.set_index('date', inplace=True)

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
def getVixTermStructurePctContango(fourToSeven = False, currentToLast = False, averageContango = False):
    # create a new df with the percent change between n and n+1 month futures
    vix_ts_pctContango = vix_ts_raw.pct_change(axis='columns', periods=-1).drop(columns='8')*-1
    


    if fourToSeven:
        # add contango from the 4th to 7th month
        vix_ts_raw['fourToSevenMoContango'] = (vix_ts_raw['6'] - vix_ts_raw['3'])/vix_ts_raw['3']
        vix_ts_pctContango = vix_ts_pctContango.join(vix_ts_raw['fourToSevenMoContango'], on='date')

    if currentToLast:
        # add contango between current and longest term future
        vix_ts_raw['currentToLastContango'] = (vix_ts_raw['8'] - vix_ts_raw['0'])/vix_ts_raw['0']
        vix_ts_pctContango = vix_ts_pctContango.join(vix_ts_raw['currentToLastContango'], on='date')
    
    if averageContango:
        # add averageContango column 
        vix_ts_pctContango['averageContango'] = vix_ts_pctContango.mean(axis=1)
    
    ## sort by Date column
    vix_ts_pctContango.sort_values(by='date', inplace=True)
    print(vix_ts_pctContango)
    return vix_ts_pctContango


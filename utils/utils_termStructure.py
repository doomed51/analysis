"""
This module consists of two functions that return VIX term structure, and contango values between contracts.
    The current implementation uses vix contract data from vixcentral.com 
"""
import pandas as pd

""" 
Returns raw vix term structure df
"""
def getRawTermStructure(termstructure_db_conn, symbol='VIX', interval='1day'):
    symbol = symbol.upper()
    tablename = f'{symbol}_{interval}'
    # read in vix term structure data
    vix_ts_raw = pd.read_sql(f'SELECT * FROM {tablename}', termstructure_db_conn)

    ## read in vix term structure data
    #vix_ts_raw = pd.read_csv('vix.csv')

    # convert date column to datetime
    vix_ts_raw['date'] = pd.to_datetime(vix_ts_raw['date'])

    # set date as index
    vix_ts_raw.set_index('date', inplace=True)
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
def getVixTermStructurePctContango(vix_ts_raw, oneToTwo=False, fourToSeven = False, currentToLast = False, averageContango = False):
    
    # create a new df with the percent change between n and n+1 month futures
    vix_ts_pctContango = vix_ts_raw.pct_change(axis='columns', periods=-1).drop(columns='month8')*-1
    
    if fourToSeven:
        # add contango from the 4th to 7th month
        vix_ts_raw['fourToSevenMoContango'] = ((vix_ts_raw['month7'] - vix_ts_raw['month4'])/vix_ts_raw['month4'])*100
        vix_ts_pctContango = vix_ts_pctContango.join(vix_ts_raw['fourToSevenMoContango'], on='date')

    if currentToLast:
        # add contango between current and longest term future
        vix_ts_raw['currentToLastContango'] = ((vix_ts_raw['month8'] - vix_ts_raw['month1'])/vix_ts_raw['month1'])*100
        vix_ts_pctContango = vix_ts_pctContango.join(vix_ts_raw['currentToLastContango'], on='date')
    
    if oneToTwo:
        # add contango between m1 and m2
        vix_ts_raw['oneToTwoMoContango'] = ((vix_ts_raw['month2'] - vix_ts_raw['month1'])/vix_ts_raw['month1'])*100
        vix_ts_pctContango = vix_ts_pctContango.join(vix_ts_raw['oneToTwoMoContango'], on='date')
    
    if averageContango:
        # add averageContango column 
        vix_ts_pctContango['averageContango'] = vix_ts_pctContango.mean(axis=1)
    
    ## sort by Date column
    vix_ts_pctContango.sort_values(by='date', inplace=True)
    return vix_ts_pctContango


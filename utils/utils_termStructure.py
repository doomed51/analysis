"""
This module consists of two functions that return VIX term structure, and contango values between contracts.
    The current implementation uses vix contract data from vixcentral.com 
"""
import pandas as pd
import seaborn as sns

""" 
Returns raw term structure for the supplied symbol and interval
"""
def getRawTermStructure(termstructure_db_conn, symbol='VIX', interval='1day'):
    symbol = symbol.upper()
    tablename = f'{symbol}_{interval}'
    # read in vix term structure data
    vix_ts_raw = pd.read_sql(f'SELECT * FROM {tablename}', termstructure_db_conn)

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
def getTermStructurePctContango(ts_raw, oneToTwo=False, oneToThree=False, twoToThree = False, threeToFour= False, fourToSeven = False, currentToLast = False, averageContango = False):
    
    # create a new df with the percent change between n and n+1 month futures
    ts_pctContango = ts_raw.pct_change(axis='columns', periods=-1).drop(columns='month8')*-1
    
    if fourToSeven:
        # add contango from the 4th to 7th month
        ts_raw['fourToSevenMoContango'] = ((ts_raw['month7'] - ts_raw['month4'])/ts_raw['month4'])*100
        ts_pctContango = ts_pctContango.join(ts_raw['fourToSevenMoContango'], on='date')

    if currentToLast:
        # add contango between current and longest term future
        ts_raw['currentToLastContango'] = ((ts_raw['month8'] - ts_raw['month1'])/ts_raw['month1'])*100
        ts_pctContango = ts_pctContango.join(ts_raw['currentToLastContango'], on='date')
    
    if oneToTwo:
        # add contango between m1 and m2
        ts_raw['oneToTwoMoContango'] = ((ts_raw['month2'] - ts_raw['month1'])/ts_raw['month1'])*100
        ts_pctContango = ts_pctContango.join(ts_raw['oneToTwoMoContango'], on='date')
    
    if oneToThree:
        # add contango between m1 and m3
        ts_raw['oneToThreeMoContango'] = ((ts_raw['month3'] - ts_raw['month1'])/ts_raw['month1'])*100
        ts_pctContango = ts_pctContango.join(ts_raw['oneToThreeMoContango'], on='date')
    
    if twoToThree: 
        # add contango between m2 and m3
        ts_raw['twoToThreeMoContango'] = ((ts_raw['month3'] - ts_raw['month2'])/ts_raw['month2'])*100
        ts_pctContango = ts_pctContango.join(ts_raw['twoToThreeMoContango'], on='date')
    
    if threeToFour:
        # add contango between m3 and m4
        ts_raw['threeToFourMoContango'] = ((ts_raw['month4'] - ts_raw['month3'])/ts_raw['month3'])*100
        ts_pctContango = ts_pctContango.join(ts_raw['threeToFourMoContango'], on='date')

    if averageContango:
        # add averageContango column 
        ts_pctContango['averageContango'] = ts_pctContango.mean(axis=1)
    
    ## sort by Date column
    ts_pctContango.sort_values(by='date', inplace=True)
    return ts_pctContango

"""
    Returns a plot of term structure for the last n periods 
    df: terms structure dataframe with columns: [date, month1, month2, ...]
"""
def plotTermStructure(ts, symbol, ax, numDays=5):
    ts.reset_index(inplace=True)
    # sort ts by date, and get the last 5 rows
    ts['date'] = pd.to_datetime(ts['date'])
    ts = ts.sort_values(by='date').tail(numDays)
    print(ts)
    
    # iterate through the last numDays records in ts
    for i in range(len(ts.tail(numDays))):
        sns.lineplot(x=ts.columns[1:], y=ts.iloc[i, 1:], ax=ax, label=ts['date'].iloc[i].strftime('%Y-%m-%d'))
    
    # set gridstyle
    ax.grid(True, which='both', axis='both', linestyle='--')
    sns.set_style('darkgrid')
    
    





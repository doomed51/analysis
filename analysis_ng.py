import datetime 
import sqlite3

import interface_localDB as db
import matplotlib.pyplot as plt
import pandas as pd
import utils as ut
import utils_futures as ut_Futures

from dateutil.relativedelta import relativedelta
from matplotlib import dates

dbname_futures = "/workbench/historicalData/venv/saveHistoricalData/historicalData_futures.db"
symbol = 'NG'
timezone = 'US/Eastern'

"""
    This function returns a dataframe with the term structure of NG futures
    inputs:
        - symbol: str of future underlying (default='NG')
        - interval: str of interval to get data for (default='1day')
        - numMOnths: number of months to look forward (default=12)
        - targetDate: date to calculate term structure for (default=
                      today) in format YYYMMMDD, must be a business day
    Output:
        - dataframe with term structure of NG futures
        term structure is calulcated as the difference between the last close price of month 0 and month 0+1; month 0+1 and month 0+2; etc. 
"""
def getTermStructure(conn, symbol='NG', interval='1day', numMonths=12, targetDate=pd.Timestamp.today().strftime('%Y%m%d')):
    # construct a dataframe as [ TS0: [month1.lastClosePrice - month0.lastClosePrice], TS1: [month2.lastClosePrice - month1.lastClosePrice], ... ]
    #   Where
    #       month0 = current month e.g. if today is 20230711, month0=11 and
    #        lastTradeMonth=202311
    #       month0.lastClosePrice = most recent close price of the month0 contract
    # ensure targetDate is a business day
    targetDate = pd.Timestamp(targetDate)
    if (targetDate.weekday() > 4):
        # set targetDate to the previous business day
        print('targetDate is not a business day, adjusting...')
        targetDate = targetDate - pd.tseries.offsets.BDay(1)
        
    # get current month expiry string 
    expiryMonth = ut.futures_getExpiryDateString()
    expiryMonth = '202308'
    
    i=0
    #empty dataframe with columns period(dtype int), termStructure (dtype float)
    ts = pd.DataFrame(columns=['period', 'termStructure'])
    # set type of period to int
    while (i<numMonths):
        # set the expiry month within the current iteration 
        expiryMonth = (datetime.datetime.strptime(expiryMonth, '%Y%m') + relativedelta(months=1)).strftime('%Y%m')

        #set expiryMonth_plusOne as the next month
        expiryMonth_plusOne = (datetime.datetime.strptime(str(expiryMonth), '%Y%m') + relativedelta(months=1)).strftime('%Y%m')
        
        TS = db.futures_getCellValue(conn, symbol, interval, lastTradeMonth=expiryMonth_plusOne) - db.futures_getCellValue(conn, symbol, interval, lastTradeMonth=expiryMonth)
        print('%s - %s to %s: %s'%(i, expiryMonth, expiryMonth_plusOne, TS))
        #append to ts dataframe: i, TS
        ts = ts._append({'period': i, 'termStructure': TS}, ignore_index=True)
        i+=1
    return ts

"""
    plots term structure of passed in futures ts dataframe
    input:
        ts dataframe w/ columns:  [date, close_expiry1, close_expiry2, ...]
        numDays: number of days to plot (default=5)
"""
def plotTermStructure(ts, numDays=5):
    
    # sort ts by date, and get the last 5 rows
    ts['date'] = pd.to_datetime(ts['date'])
    ts = ts.sort_values(by='date').tail(numDays)

    # set axis values 
    axis_x = ts.columns[2:]
    axis_y = ts.iloc[:, 2:]

    # plot each row 
    for i in range(len(ts.tail(numDays))):
        plt.plot(axis_x, axis_y.iloc[i, :])
    
    # add legend
    plt.legend(ts['date'])
    
    # add title
    plt.title('%s Term Structure'%symbol)

    # rotate x axis labels
    plt.xticks(rotation=45)
    plt.tight_layout()

"""
    Plots %contango of term structure over various months as follows: 
        1. retrieve %contango ts by calling getTermStructureContango(ts, startMonth, endMonth)
        2. plot all of these on the same plot 
"""
def plotTermStructureContango(ts, startMonth, endMonth):
    
    # get %contango ts 
    ts_contango = ut_Futures.getContango(ts, startMonth, endMonth)
    
    #plot the last column vs. date column; adding a label 
    plt.plot(ts_contango['date'], ts_contango.iloc[:, -1], label='%s'%(ts_contango.columns[-1]))

    ## add legend
    plt.legend()
    
    # add title
    plt.title('%s Term Structure Contango'%symbol)
    plt.tight_layout()
    print(ts_contango)



""" 
    Test use case: create a grid of 2x2 plots 
    Inputs:
        - n/a
    Outputs: 
        - 2x2 grid of plots
"""
def plotGrid_testCase():
    row = 2
    column = 2

    index = 1
    # create a 2x2 grid of plots
    #fig, axs = 
    plt.subplot(row, column, index)
    plotTermStructure(ts, 10)

    index+=1
    plt.subplot(row, column, index)
    plotTermStructureContango(ts, 1, 9)
    plotTermStructureContango(ts, 1, 11)    

    plt.tight_layout()

with db.sqlite_connection(dbname_futures) as conn:
    ts = ut_Futures.getRawTermstructure(conn, 'NG')

#plotTermStructure(ts)
#plotTermStructureContango(ts, 1, 9)
#plotTermStructureContango(ts, 1, 11)
plotGrid_testCase()


plt.show()
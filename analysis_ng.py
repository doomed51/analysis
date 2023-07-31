import datetime 
import sqlite3

import interface_localDB as db
import matplotlib.pyplot as plt
import pandas as pd
import utils as ut

from dateutil.relativedelta import relativedelta

dbname_futures = "/workbench/historicalData/venv/saveHistoricalData/historicalData_futures.db"

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
    ts['period'] = ts['period'].astype(int)
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
    print(ts)
    return ts

#conn = db._connectToDb_deprecate(dbname_futures)
#print(conn)

with db.sqlite_connection(dbname_futures) as conn:
    getTermStructure(conn, targetDate='20230721 00:00:00')

exit()

ng_202308 = db.getPriceHistory('NG', '1day', lastTradeMonth='202308').reset_index(drop=True)
ng_202305 = db.getPriceHistory('NG', '1day', lastTradeMonth='202312').reset_index(drop=True)
ng_202308 = ut.calcLogReturns(ng_202308, 'close')
ng_202305 = ut.calcLogReturns(ng_202305, 'close')
print(ng_202308)


#plt.plot(ng_202308['date'], ng_202308['logReturn'])
#plt.plot(ng_202305['date'], ng_202308['logReturn'], color='red')

#plot bar plots of pct change and log return for 202308 with different colours
plt.bar(ng_202308['date'], ng_202308['logReturn'], color='red')
plt.bar(ng_202308['date'], ng_202308['pctChange'], color='blue')



# set chart title to symbol - lastTradeMonth from the returned dataframe
plt.title(ng_202308['symbol'][0]+' - '+ng_202308['lastTradeMonth'][0])

plt.show()

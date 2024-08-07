## Imported from: https://github.com/doomed51/saveHistoricalData.git
#  LAST UPDATE DATE: 2024-04-29

"""
This module simplifies interacting with the local database of historical ohlc data. 

    - connect to db
    - save historical data to local db 
    - retrieve historical data for symbol and interval 
    - automatically clears duplicates if any

"""

import sqlite3
import sys
import config
import pandas as pd
sys.path.append('..')
from utils import utils as ut

pd.options.mode.chained_assignment = None  # default='warn'

""" Global vars """
dbname_index = config.dbname_stock

index_list = config._indexList # global reference list of index symbols, this is some janky ass shit .... 

""" implements contextmanager for db connection """
class sqlite_connection(object): 
    
    def __init__(self, db_name):
        self.db_name = db_name
    
    def __enter__(self):
        self.conn = sqlite3.connect(self.db_name)
        return self.conn
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.commit()
        self.conn.close()

"""
Establishes a connection to the appropriate DB based on type of symbol passed in. 

Returns sqlite connection object 

"""
def _connectToDb_deprecate(dbname = dbname_index):
    # set dbname to \\workbench\\historicalData\\venv\\saveHistoricalData\\ + dbname
    return sqlite3.connect(dbname)

"""
constructs the appropriate tablename to call local DB 

Params
===========
symbol - [str]
interval - [str] 

"""
def _constructTableName(symbol, interval):
    type_ = 'stock'
    if symbol.upper() in index_list:
        type_ = 'index'

    tableName = symbol+'_'+type_+'_'+interval

    return tableName

"""
utility - permanently remove duplicate records from ohlc table

Params
==========
tablename - [str]
"""
def _removeDuplicates(tablename):
    conn = _connectToDb() # connect to DB

    ## construct SQL qeury that will group on 'date' column and
    ## select the min row ID of each group; then delete all the ROWIDs from 
    ## the table that not in this list
    sql_selectMinId = 'DELETE FROM %s WHERE ROWID NOT IN (SELECT MIN(ROWID) FROM %s GROUP BY date)'%(tablename, tablename)

    ## run the query 
    cursor = conn.cursor()
    cursor.execute(sql_selectMinId)

"""
sub to update the symbol record lookup table
This should be called when local db records are updated 
This should not be run before security history is added to the db 

Params
----------
tablename: table that needs to be updated 
numMissingDays: number of days we do not have locally  
"""
def _updateLookup_symbolRecords(conn, tablename, earliestTimestamp, numMissingDays = 5):
    lookupTablename = '00-lookup_symbolRecords'
    
    ## get the earliest record date saved for the target symbol 
    sql_minDate_symbolHistory = 'SELECT MIN(date), symbol, interval FROM %s'%(tablename)
    minDate_symbolHistory = pd.read_sql(sql_minDate_symbolHistory, conn)
    
    ## get the earliest date from the lookup table for the matching symbol 
    sql_minDate_recordsTable = 'SELECT firstRecordDate FROM \'%s\' WHERE symbol = \'%s\' and interval = \'%s\''%(lookupTablename, minDate_symbolHistory['symbol'][0], minDate_symbolHistory['interval'][0])
    minDate_recordsTable = pd.read_sql(sql_minDate_recordsTable, conn)
    
    ## add a new record entry in the lookup table since none are there 
    if minDate_recordsTable.empty:
        ## compute the number of missing business days 
        ## since this is a new record, we expect a timestamp to have been 
        ## passed on the call to write history to the db 
                
        if earliestTimestamp:
            ## set missing business days to the difference between the earliest available date in ibkr and the earliest date in the local db
            numMissingDays = len(pd.bdate_range(earliestTimestamp, minDate_symbolHistory.iloc[0]['MIN(date)']))

        ## add missing columns 
        minDate_symbolHistory['numMissingBusinessDays'] = numMissingDays
        minDate_symbolHistory['name'] = tablename
        
        ## rename columns to match db table columns 
        minDate_symbolHistory.rename(columns={'MIN(date)':'firstRecordDate'}, inplace=True)
        minDate_symbolHistory = minDate_symbolHistory.iloc[:,[4,1,2,0,3]]
      
        ## save record to db
        minDate_symbolHistory.to_sql(f"{lookupTablename}", conn, index=False, if_exists='append')
    
    ## otherwise update the existing record
    elif minDate_symbolHistory['MIN(date)'][0] < minDate_recordsTable['firstRecordDate'][0]:
        ## update lookuptable with the symbolhistory min date
        sql_update = 'UPDATE \'%s\' SET firstRecordDate = \'%s\' WHERE symbol = \'%s\' and interval = \'%s\''%(lookupTablename, minDate_symbolHistory['MIN(date)'][0], minDate_symbolHistory['symbol'][0], minDate_symbolHistory['interval'][0]) 
        cursor = conn.cursor()
        cursor.execute(sql_update)

def __remove_timezone_from_datestring(datestring):
    """
        lambda function: Remove timezone info from datestring
    """    
    if len(datestring) > 19:
        return datestring[:19]
    else:
        return datestring

""" ensures proper format of px history tables retrieved from db """
def _formatpxHistory(pxHistory):
    
    pxHistory.reset_index(drop=True, inplace=True)
    
    ## Remove unnecessary info in the date string
    if pxHistory['interval'][1] == '1day':
        pxHistory['date'] = pxHistory['date'].str[:10] # remove milliseconds
    
    else: 
        pxHistory['formatted_date'] = pxHistory['date'].apply(__remove_timezone_from_datestring)
        pxHistory.drop(columns=['date'], inplace=True)
        pxHistory.rename(columns={'formatted_date':'date'}, inplace=True)

    pxHistory = pxHistory[~pxHistory['date'].duplicated()]
   
    # format to datetime type 
    if pxHistory['interval'][1] == '1day':
        pxHistory.loc[:,'date'] = pd.to_datetime(pxHistory['date'], format='%Y-%m-%d')
    else:
        pxHistory.loc[:,'date'] = pd.to_datetime(pxHistory['date'], format='%Y-%m-%d %H:%M:%S')
    
    # make sure date is datetime type
    # pxHistory.loc[:,'date'] = pd.to_datetime(pxHistory.loc[:,'date'])
    pxHistory['date'] = pd.to_datetime(pxHistory['date'])

    # final formatting
    pxHistory = pxHistory.sort_values(by='date')

    return pxHistory

"""
Save history to a sqlite3 database
###

Params
------------
history: [DataFrame]
    pandas dataframe with security timeseries data
conn: [Sqlite3 connection object]
    connection to the local db 
"""
def saveHistoryToDB(history, conn, earliestTimestamp=''):
    
    ## set type to index if the symbol is in the index list 
    if history['symbol'][0] in index_list:
        type = 'index'
    else: 
        type='stock'
    
    # Write the dataframe to the database with the correctly formatted table name
    tableName = history['symbol'][0]+'_'+type+'_'+history['interval'][0]
    history.to_sql(f"{tableName}", conn, index=False, if_exists='append')
    
    #make sure there are no duplicates in the resulting table
    _removeDuplicates(tableName)

    ## make sure the records lookup table is kept updated
    #if earliestTimestamp:
    _updateLookup_symbolRecords(conn, tableName, earliestTimestamp=earliestTimestamp)

"""
Returns dataframe of px from database 

Params
===========
symbol - [str]
interval - [str] 
lookback - [str] optional 

"""
def getPriceHistory(conn, symbol, interval, withpctChange=True, lastTradeMonth=''):
    if lastTradeMonth:
        tableName = symbol+'_'+lastTradeMonth+'_'+interval
    else:
        tableName = _constructTableName(symbol, interval)
    sqlStatement = 'SELECT * FROM '+tableName
    pxHistory = pd.read_sql(sqlStatement, conn)
    
    # format the px history
    pxHistory = _formatpxHistory(pxHistory)

    # calc pct change if needed
    if withpctChange:
        pxHistory['pctChange'] = pxHistory['close'].pct_change()

    # caclulate log returns
    pxHistory = ut.calcLogReturns(pxHistory, 'close')
    
    return pxHistory

def getPriceHistoryWithTablename(conn, tablename):
    sqlStatement = 'SELECT * FROM '+tablename
    pxHistory = pd.read_sql(sqlStatement, conn)
    pxHistory = _formatpxHistory(pxHistory)
    pxHistory = ut.calcLogReturns(pxHistory, 'close')
    return pxHistory
""" 
Returns the lookup table fo records history as df 
"""
def getLookup_symbolRecords(conn):
    sqlStatement_selectRecordsTable = 'SELECT * FROM \'00-lookup_symbolRecords\''
    symbolRecords = pd.read_sql(sqlStatement_selectRecordsTable, conn)
    # convert firstRecordDate column to datetime
    symbolRecords['firstRecordDate'] = pd.to_datetime(symbolRecords['firstRecordDate'])
    return symbolRecords

"""
lists the unique symbols in the lookup table
"""
def listSymbols(conn):
    sqlStatement_selectRecordsTable = 'SELECT DISTINCT symbol FROM \'00-lookup_symbolRecords\' ORDER BY symbol ASC'
    symbols = pd.read_sql(sqlStatement_selectRecordsTable, conn)
    return symbols

"""
    Returns value of a specified cell for the target futures contract
    inputs:
        symbol: str
        interval: str
        expiryMonth: str as YYYYMM
        targetColumn: str, column we want from the db table 
        targetDate: str as YYYY-MM-DD, date of the column we want
    outputs:
        value of the target cell
"""
def futures_getCellValue(conn, symbol, interval='1day', lastTradeMonth='202308', targetColumn='close', targetDate='2023-07-21'):
    # construct tablename
    tableName = symbol+'_'+str(lastTradeMonth)+'_'+interval
    targetDate = '2023-07-21 00:00:00'
    # run sql query to get cell value 
    sqlStatement = 'SELECT '+targetColumn+' FROM '+tableName+' WHERE date = \''+targetDate+'\''

    value = pd.read_sql(sqlStatement, conn)
    # return val 
    return value[targetColumn][0]
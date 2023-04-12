"""
This module simplifies interacting with the local database of historical ohlc data. 

    - connect to db
    - save historical data to local db 
    - retrieve historical data for symbol and interval 
    - automatically clears duplicates if any

"""

import sqlite3
import pandas as pd

""" Global vars """
dbname_stocks = 'historicalData_stock.db' ## vanilla stock data location 
dbname_index = 'historicalData_index.db' ## index data location

index_list = ['VIX', 'VIX3M', 'VVIX'] # global reference list of index symbols, this is some janky ass shit .... 

## lookup table for interval labels 
intervalMappings = pd.DataFrame(
    {
        'label': ['5m', '15m', '30m', '1h', '1d', '1m'],
        'stock': ['FiveMinutes', 'FifteenMinutes', 'HalfHour', 'OneHour', 'OneDay', 'OneMonth'],
        'index':['5mins', '15mins', '30mins', '1hour', '1day', '1month']
    }
)

"""
Establishes a connection to the appropriate DB based on type of symbol passed in. 

Returns sqlite connection object 

"""
def _connectToDb():
    return sqlite3.connect(dbname_index)

"""
constructs the appropriate tablename to call local DB 

Params
===========
symbol - [str]
interval - [str] (must match with intervalMappings global var)

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
Utility to update the symbol record lookup table
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
def getPriceHistory(symbol, interval):
    tableName = _constructTableName(symbol, interval)
    conn = _connectToDb()
    sqlStatement = 'SELECT * FROM '+tableName
    pxHistory = pd.read_sql(sqlStatement, conn)
    conn.close()
    pxHistory.rename(columns={'date':'Date'}, inplace=True)
    #convert date column to datetime
    pxHistory['Date'] = pd.to_datetime(pxHistory['Date'])
    #sort by date
    pxHistory.sort_values(by='Date', inplace=True)
    pxHistory.set_index('Date', inplace=True)

    # if interval is in 1day, 1wk, 1mo reset index
    if interval in ['1min', '5mins', '15mins', '30mins', '1hour']:
        pxHistory['Date'] = pxHistory.index.date
        pxHistory['Time'] = pxHistory.index.time
        # change index label to 'datetime'
        pxHistory.index.name = 'datetime'
    
    return pxHistory

"""
establishes a connection to the appropriate DB based on type of symbol passed in. 

Returns sqlite connection object 

Params
========
symbol - [str] 
"""
def _connectToDb():
    return sqlite3.connect(dbname_index)

""" 
Returns the lookup table fo records history as df 
"""
def getLookup_symbolRecords():
    conn = _connectToDb()
    sqlStatement_selectRecordsTable = 'SELECT * FROM \'00-lookup_symbolRecords\''
    symbolRecords = pd.read_sql(sqlStatement_selectRecordsTable, conn)
    # convert firstRecordDate column to datetime
    symbolRecords['firstRecordDate'] = pd.to_datetime(symbolRecords['firstRecordDate'])
    return symbolRecords
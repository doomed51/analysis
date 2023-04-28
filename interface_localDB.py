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
dbname_index = '\workbench\historicalData\\venv\saveHistoricalData\historicalData_index.db'

index_list = ['VIX', 'VIX3M', 'VVIX'] # global reference list of index symbols, this is some janky ass shit .... 

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

""" ensures proper format of data retrieved from db """
def _formatpxHistory(pxHistory):
        
    ##### Remove any errant timezone info:
    # get the rows that have timezone info in the date column
    # remove the timezone info from the date column
    # update pxhistory with the formatted date column
    pxHistory_hasTimezone = pxHistory[pxHistory['date'].str.len() > 19]
    if not pxHistory_hasTimezone.empty:
        # remove the timezone info from the date column
        pxHistory_hasTimezone.loc[:,'date'] = pxHistory_hasTimezone['date'].str[:19]
        # update pxhistory with the formatted date column
        pxHistory.update(pxHistory_hasTimezone)

    # final formatting ... 
    pxHistory['date'] = pd.to_datetime(pxHistory['date'], format='mixed')
    pxHistory.sort_values(by='date', inplace=True) #sort by date
    
    # if interval is < 1 day, split the date and time column
    if pxHistory['interval'][0] in ['1min', '5mins', '15mins', '30mins', '1hour']:
        print('asdf')
        #pxHistory[['Date', 'Time']] = pxHistory['Date'].str.split(' ', expand=True)
        # set format for Date and Time columns
        #pxHistory['Date'] = pd.to_datetime(pxHistory['Date'])
        #print('max length of date column: ', pxHistory['Date'].len().max())
        #exit()
    return pxHistory

"""
Returns dataframe of px from database 

Params
===========
symbol - [str]
interval - [str] 
lookback - [str] optional 

"""
def getPriceHistory(symbol, interval, withpctChange=True):
    tableName = _constructTableName(symbol, interval)
    conn = _connectToDb()
    sqlStatement = 'SELECT * FROM '+tableName
    pxHistory = pd.read_sql(sqlStatement, conn)
    conn.close()
    if interval == '1day':
        print(pxHistory)
    pxHistory = _formatpxHistory(pxHistory)
    if withpctChange:
        pxHistory['pctChange'] = pxHistory['close'].pct_change()
        ## drop the first row since it will have NaN for pctChange
        pxHistory.drop(pxHistory.index[0], inplace=True)
    return pxHistory

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

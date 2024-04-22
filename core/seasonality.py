import pandas as pd 

"""
Returns seasonal aggregate of passed in pxhistory df
"""
def getSeasonalAggregate(pxHistory, interval, symbol, numdays=0):
    
    # if numdays >0, then only aggregate data for last numdays
    if numdays > 0:
        pxHistory = pxHistory[pxHistory['date'] > (pxHistory['date'].max() - pd.Timedelta(days=numdays))]
    
    # aggregate by time and compute mean and std dev of %change
    if interval in ['1min', '5mins', '15mins', '30mins', '1hour']:
        pxHistory_aggregated = pxHistory.groupby(pxHistory['date'].dt.time).agg({'pctChange':['mean', 'std']})
        # add cumsum that resets at the start of each day
        pxHistory_aggregated['cumsum'] = pxHistory.groupby(pxHistory['date'].dt.time)['pctChange'].cumsum()

    elif interval in ['1day', '1week', '1month']:
        pxHistory_aggregated = pxHistory.groupby(pxHistory['date'].dt.day).agg({'pctChange':['mean', 'std']})
    
    elif interval in ('weekByDay'):
        pxHistory_aggregated = pxHistory.groupby(pxHistory['date'].dt.dayofweek).agg({'pctChange':['mean', 'std']})
    
    elif interval in ('yearByMonth'):
        
        # reset index so we can use the Date column to agg 
        pxHistory.reset_index(inplace=True)
        # group pxhistory by (year, month) and get the min and max Date in each group 
        pxHistory_monthly = pxHistory.groupby([pxHistory['date'].dt.year, pxHistory['date'].dt.month]).agg({'date':['min', 'max']})
        #rename index columns to year and month
        pxHistory_monthly.index.names = ['year', 'month']

        # flatten multi-index columns
        pxHistory_monthly.columns = ['_'.join(col).strip() for col in pxHistory_monthly.columns.values]
        # reset index
        pxHistory_monthly.reset_index(inplace=True)

        ## calc the percent change between the first and last trading day of each month:
        ##  1. given pxHistoroy contains the close price for any given Date 
        ##  2. Add a column to pxHistory_monthly that is the percent change of the close price between Date_min and Date_max
        ##  3. group by month and calculate the mean and std dev of pctChange
        pxHistory_monthly['pctChange'] = pxHistory_monthly.apply(lambda row: (pxHistory[(pxHistory['date'] == row['date_max'])]['close'].values[0] - pxHistory[(pxHistory['date'] == row['date_min'])]['close'].values[0])/pxHistory[(pxHistory['date'] == row['date_min'])]['close'].values[0], axis=1)

        pxHistory_aggregated = pxHistory_monthly.groupby('month').agg({'pctChange':['mean', 'std']})
    else:
        print('aggreagation not supported for interval: '+interval)

    # flatten multi-index columns
    pxHistory_aggregated.columns = ['_'.join(col).strip() for col in pxHistory_aggregated.columns.values]

    # add symbol and interval to aggregated df 
    pxHistory_aggregated['symbol'] = symbol
    pxHistory_aggregated['interval'] = interval

    return pxHistory_aggregated

"""
plots seasonal analysis for a given symbol and interval combo
"""
import matplotlib
import math

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import localDb_interface as db

from matplotlib.dates import date2num

"""
Plots seasonal returns in a 3x3 grid
"""
def plotSeasonalReturns(seasonalReturns, intervals, symbols, titles):
    # create a grid of symbols & intervals to draw the plots into 
    # col x rows : interval x symbol 
    title = 'Seasonal Returns for %s' % symbols[0]
    numCols = 3
    """if symbols:
        numRows = math.ceil(len(symbols)/numCols)
    else:"""
    numRows = 3

    fig, axes = plt.subplots(nrows=numRows, ncols=numCols, figsize=(numCols*6, numRows*4))

    fig.suptitle(title)

    sns.set()

    # bar plot for ALL history: seasonalReturns[0]
    sns.barplot(x=seasonalReturns[0].index, y='pctChange_std', data=seasonalReturns[0], ax=axes[0,0], color='grey', alpha=0.5)
    sns.barplot(x=seasonalReturns[0].index, y='pctChange_mean', data=seasonalReturns[0], ax=axes[0,0].twinx(), color='red')
    axes[0,0].set_title(titles[0]) # set title for subplot
    axes[0,0].set_xlabel('') # hide x axis title
    
    # bar plot for last 60 days: seasonalReturns[1]
    sns.barplot(x=seasonalReturns[1].index, y='pctChange_std', data=seasonalReturns[1], ax=axes[0,1], color='grey', alpha=0.5)
    sns.barplot(x=seasonalReturns[1].index, y='pctChange_mean', data=seasonalReturns[1], ax=axes[0,1].twinx(), color='red')
    axes[0,1].set_title(titles[1]) # set title for subplot
    axes[0,1].set_xlabel('') # hide x axis title

    #bar plot for last 90 days: seasonalReturns[2]
    sns.barplot(x=seasonalReturns[2].index, y='pctChange_std', data=seasonalReturns[2], ax=axes[0,2], color='grey', alpha=0.5)
    sns.barplot(x=seasonalReturns[2].index, y='pctChange_mean', data=seasonalReturns[2], ax=axes[0,2].twinx(), color='red')
    axes[0,2].set_title(titles[2]) # set title for subplot
    axes[0,2].set_xlabel('') # hide x axis title

    # bar plot of last 30 days: seasonalReturns[3]
    sns.barplot(x=seasonalReturns[3].index, y='pctChange_std', data=seasonalReturns[3], ax=axes[1,0], color='grey', alpha=0.5)
    sns.barplot(x=seasonalReturns[3].index, y='pctChange_mean', data=seasonalReturns[3], ax=axes[1,0].twinx(), color='red')
    axes[1,0].set_title(titles[3]) # set title for subplot
    axes[1,0].set_xlabel('') # hide x axis title

    # bar plof of prev 30 days: seasonalReturns[4]
    sns.barplot(x=seasonalReturns[4].index, y='pctChange_std', data=seasonalReturns[4], ax=axes[1,1], color='grey', alpha=0.5)
    sns.barplot(x=seasonalReturns[4].index, y='pctChange_mean', data=seasonalReturns[4], ax=axes[1,1].twinx(), color='red')
    axes[1,1].set_title(titles[4]) # set title for subplot
    axes[1,1].set_xlabel('') # hide x axis title

    # bar plot of prev 60 days: seasonalReturns[5]
    sns.barplot(x=seasonalReturns[5].index, y='pctChange_std', data=seasonalReturns[5], ax=axes[1,2], color='grey', alpha=0.5)
    sns.barplot(x=seasonalReturns[5].index, y='pctChange_mean', data=seasonalReturns[5], ax=axes[1,2].twinx(), color='red')
    axes[1,2].set_title(titles[5]) # set title for subplot
    axes[1,2].set_xlabel('') # hide x axis title

    sns.heatmap(seasonalReturns[6].pivot_table(index='time', columns='date', values='pctChange'), ax=axes[2,0])
    axes[2,0].set_title(titles[6])

    sns.heatmap(seasonalReturns[7].pivot_table(index='time', columns='date', values='pctChange'), ax=axes[2,1])
    axes[2,1].set_title(titles[7])

    sns.heatmap(seasonalReturns[8].pivot_table(index='time', columns='date', values='pctChange'), ax=axes[2,2])
    axes[2,2].set_title(titles[8])

    # tilt x axis labels 45 degrees
    axes[0,0].set_xticklabels(axes[0,0].get_xticklabels(), rotation=45)
    axes[0,1].set_xticklabels(axes[0,0].get_xticklabels(), rotation=45)
    axes[0,2].set_xticklabels(axes[0,0].get_xticklabels(), rotation=45)
    axes[1,0].set_xticklabels(axes[0,0].get_xticklabels(), rotation=45)
    axes[1,1].set_xticklabels(axes[0,0].get_xticklabels(), rotation=45)
    axes[1,2].set_xticklabels(axes[0,0].get_xticklabels(), rotation=45)

"""
Returns seasonal aggregate of passed in pxhistory df
"""
def getSeasonalAggregate(pxHistory, interval, symbol, numdays=0):
    
    # if numdays >0, then only aggregate data for last numdays
    if numdays > 0:
        pxHistory = pxHistory[pxHistory['date'] > (pxHistory['date'].max() - pd.Timedelta(days=numdays))]
    
    # aggregate by time and compute mean and std dev of %change
    if interval in ['1min', '5mins', '15mins', '30mins', '1hour']:
        pxHistory_aggregated = pxHistory.groupby('time').agg({'pctChange':['mean', 'std']})

    elif interval in ['1day', '1week', '1month']:
        #pxHistory_aggregated = pxHistory.groupby('Date').agg({'pctChange':['mean', 'std']})
        # group by day of month and compute mean and std dev of %change
        pxHistory_aggregated = pxHistory.groupby(pxHistory.index.day).agg({'pctChange':['mean', 'std']})
    
    else:
        print('aggreagation not supported for interval: '+interval)

    # flatten multi-index columns
    pxHistory_aggregated.columns = ['_'.join(col).strip() for col in pxHistory_aggregated.columns.values]

    # add symbol and interval to aggregated df 
    pxHistory_aggregated['symbol'] = symbol
    pxHistory_aggregated['interval'] = interval

    return pxHistory_aggregated


"""
Runs seasonal analysis on intra-day data for a given symbol and interval
    plots different subsets of data: all, last 30 days, last 60 days, last 90 days 
"""
def seasonalAnalysis_intraday(symbol, interval, target='close', restrictTradingHours=False):
    pxHistory = db.getPriceHistory(symbol, interval)

    # calculate %change on target=close for each row
    pxHistory['pctChange'] = pxHistory[target].pct_change()

    # explicitly sort by date
    pxHistory.sort_values(by='Date', inplace=True)

    if interval not in ['1day']:
        pxHistory['date'] = pxHistory.index.date
        pxHistory['time'] = pxHistory.index.time
       
    if restrictTradingHours:
            # remove rows outside of trading hours
            pxHistory = pxHistory.between_time('9:30', '16:00')
    
    #drop the first row of pxHistory as it has NaN for pctChange
    pxHistory.drop(pxHistory.index[0], inplace=True)

    # get mean and std for aggregated data
    pxHistory_aggregated = getSeasonalAggregate(pxHistory, interval, symbol)

    # select only aggregated data of last 60 days
    pxHistory60 = pxHistory[pxHistory['date'] > (pxHistory['date'].max() - pd.Timedelta(days=60))]
    pxhistory60_aggregated = getSeasonalAggregate(pxHistory60, interval, symbol)

    # select last 30 days of data from pxhistory 
    pxHistory30 = pxHistory[pxHistory['date'] > (pxHistory['date'].max() - pd.Timedelta(days=30))]
    pxhistory30_aggregated = getSeasonalAggregate(pxHistory30, interval, symbol)

    # select last 90 days of data from pxhistory 
    pxHistory90 = pxHistory[pxHistory['date'] > (pxHistory['date'].max() - pd.Timedelta(days=90))]
    pxhistory90_aggregated = getSeasonalAggregate(pxHistory90, interval, symbol)

    # select aggregated data for last 30, prev 30, 
    # and prev prev 30 days of data from pxhistory
    pxHistory302 = pxHistory[(pxHistory['date'] < (pxHistory30['date'].min())) & (pxHistory['date'] > (pxHistory30['date'].min() - pd.Timedelta(days=31)))]
    pxHistory303 = pxHistory[(pxHistory['date'] < pxHistory302['date'].min()) & (pxHistory['date'] > pxHistory302['date'].min() - pd.Timedelta(days=31))]
    pxhistory302_aggregated = getSeasonalAggregate(pxHistory302, interval, symbol)
    pxhistory303_aggregated = getSeasonalAggregate(pxHistory303, interval, symbol)

    # increment row for every new 'catgory' of analysis, or every 3rd plot 

    # count business days between pxhistory.index.min() and pxhistory.index.max()
    numBusinessDays = len(pd.bdate_range(pxHistory.index.min(), pxHistory.index.max()))

    ## plot the results 
    plotSeasonalReturns(
    [
        pxHistory_aggregated, pxhistory60_aggregated, pxhistory90_aggregated, 
        pxhistory30_aggregated, pxhistory302_aggregated, pxhistory303_aggregated, pxHistory30, pxHistory302, pxHistory303],
          
          [interval, interval, interval, 
           interval, interval, interval, 
           interval, interval, interval], 
           
           [symbol, symbol, symbol, 
            symbol, symbol, symbol,
            symbol, symbol, symbol], 
            
            ['Starting from %s'%(pxHistory.index.min().date()), 
             'Last %s Days'%(len(pd.bdate_range(pxHistory60.index.min(), pxHistory60.index.max()))),
              'Last %s Days'%(len(pd.bdate_range(pxHistory90.index.min(), pxHistory90.index.max()))),
             'From %s to %s'%(pxHistory30.index.min().date(), pxHistory30.index.max().date()), 
             'From %s to %s'%(pxHistory302.index.min().date(), pxHistory302.index.max().date()), 
             'From %s to %s'%(pxHistory303.index.min().date(), pxHistory303.index.max().date()),
             'From %s to %s'%(pxHistory30.index.min().date(), pxHistory30.index.max().date()),
              'From %s to %s'%(pxHistory302.index.min().date(), pxHistory302.index.max().date()),
               'From %s to %s'%(pxHistory303.index.min().date(), pxHistory303.index.max().date()) ])



## get timeseries data from db
symbol = 'KOLD'
interval = '5mins'
target = 'close' # open, high, low, close, volume
restrictTradingHours = True # if true -> only analyze data between 9:30am and 4pm

seasonalAnalysis_intraday(symbol, interval, target, restrictTradingHours)
plt.subplots_adjust(hspace=0.3, wspace=0.4, left=0.05, right=0.95, top=0.95, bottom=0.09)
plt.xticks(rotation=45)
plt.show()


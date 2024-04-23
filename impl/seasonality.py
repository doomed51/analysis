"""
plots various seasonal analyses for a given symbol

    - plotSeasonalReturns_intraday: 3x3 grid of barplots for analyzing intraday seasonal returns
    - plotSeasonalReturns_overview: 1x3 grid of barplots for a quick overview of seasonality in a symbol 
"""

import config
import datetime as dt
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from interface import interface_localDB as db
from matplotlib.dates import date2num
from utils import utils as ut

dbname_stock = config.dbname_stock

"""
Plots seasonal returns in a 3x3 grid
"""
def plotSeasonalReturns_intraday(seasonalReturns, intervals, symbols, titles, target = 'close'):
    # create a grid of symbols & intervals to draw the plots into 
    # col x rows : interval x symbol 
    title = 'Intraday Seasonal Returns for %s' % symbols[0]
    numCols = 3
    numRows = 3

    # setup figure and axes
    fig, axes = plt.subplots(nrows=numRows, ncols=numCols, figsize=(numCols*6, numRows*4.2))

    # set title for figure
    fig.suptitle(title)
    # bar plot for ALL history: i.e. seasonalReturns[0]
    sns.barplot(x=seasonalReturns[0].index, y='pctChange_std', data=seasonalReturns[0], ax=axes[0,0], color='grey', alpha=0.5)
    sns.barplot(x=seasonalReturns[0].index, y='pctChange_mean', data=seasonalReturns[0], ax=axes[0,0].twinx(), color='red')
    axes[0,0].set_title(titles[0]) # set title for subplot
    axes[0,0].set_xlabel('') # hide x axis title
    
    
    # bar plot for last 60 days: i.e. seasonalReturns[1]
    sns.barplot(x=seasonalReturns[1].index, y='pctChange_std', data=seasonalReturns[1], ax=axes[0,1], color='grey', alpha=0.5)
    sns.barplot(x=seasonalReturns[1].index, y='pctChange_mean', data=seasonalReturns[1], ax=axes[0,1].twinx(), color='red')
    axes[0,1].set_title(titles[1]) # set title for subplot
    axes[0,1].set_xlabel('') # hide x axis title

    #bar plot for last 90 days: i.e. seasonalReturns[2]
    sns.barplot(x=seasonalReturns[2].index, y='pctChange_std', data=seasonalReturns[2], ax=axes[0,2], color='grey', alpha=0.5)
    sns.barplot(x=seasonalReturns[2].index, y='pctChange_mean', data=seasonalReturns[2], ax=axes[0,2].twinx(), color='red')
    axes[0,2].set_title(titles[2]) # set title for subplot
    axes[0,2].set_xlabel('') # hide x axis title

    # bar plot of last 30 days: i.e. seasonalReturns[3]
    sns.barplot(x=seasonalReturns[3].index, y='pctChange_std', data=seasonalReturns[3], ax=axes[1,0], color='grey', alpha=0.5)
    sns.barplot(x=seasonalReturns[3].index, y='pctChange_mean', data=seasonalReturns[3], ax=axes[1,0].twinx(), color='red')
    axes[1,0].set_title(titles[3]) # set title for subplot
    axes[1,0].set_xlabel('') # hide x axis title

    # bar plof of prev 30 days: i.e. seasonalReturns[4]
    sns.barplot(x=seasonalReturns[4].index, y='pctChange_std', data=seasonalReturns[4], ax=axes[1,1], color='grey', alpha=0.5)
    sns.barplot(x=seasonalReturns[4].index, y='pctChange_mean', data=seasonalReturns[4], ax=axes[1,1].twinx(), color='red')
    axes[1,1].set_title(titles[4]) # set title for subplot
    axes[1,1].set_xlabel('') # hide x axis title

    # bar plot of prev 60 days: i.e. seasonalReturns[5]
    sns.barplot(x=seasonalReturns[5].index, y='pctChange_std', data=seasonalReturns[5], ax=axes[1,2], color='grey', alpha=0.5)
    sns.barplot(x=seasonalReturns[5].index, y='pctChange_mean', data=seasonalReturns[5], ax=axes[1,2].twinx(), color='red')
    axes[1,2].set_title(titles[5]) # set title for subplot
    axes[1,2].set_xlabel('') # hide x axis title

    sns.heatmap(seasonalReturns[6].pivot_table(index=seasonalReturns[6]['date'].dt.time, columns=seasonalReturns[6]['date'].dt.date, values='pctChange'), ax=axes[2,0])
    axes[2,0].set_title(titles[6])

    sns.heatmap(seasonalReturns[7].pivot_table(index=seasonalReturns[7]['date'].dt.time, columns=seasonalReturns[7]['date'].dt.date, values='pctChange'), ax=axes[2,1])
    axes[2,1].set_title(titles[7])

    sns.heatmap(seasonalReturns[8].pivot_table(index=seasonalReturns[8]['date'].dt.time, columns=seasonalReturns[8]['date'].dt.date, values='pctChange'), ax=axes[2,2])
    axes[2,2].set_title(titles[8])

    # tilt x axis labels 90 degrees
    axes[0,0].set_xticklabels(axes[0,0].get_xticklabels(), rotation=90, fontsize=8)
    axes[0,1].set_xticklabels(axes[0,0].get_xticklabels(), rotation=90, fontsize=8)
    axes[0,2].set_xticklabels(axes[0,0].get_xticklabels(), rotation=90, fontsize=8)
    axes[1,0].set_xticklabels(axes[0,0].get_xticklabels(), rotation=90, fontsize=8)
    axes[1,1].set_xticklabels(axes[0,0].get_xticklabels(), rotation=90, fontsize=8)
    axes[1,2].set_xticklabels(axes[0,0].get_xticklabels(), rotation=90, fontsize=8)

    axes[0,0].set_xticks(axes[0,0].get_xticks()[::3])
    axes[0,1].set_xticks(axes[0,1].get_xticks()[::3])
    axes[0,2].set_xticks(axes[0,2].get_xticks()[::3])
    axes[1,0].set_xticks(axes[1,0].get_xticks()[::3])
    axes[1,1].set_xticks(axes[1,1].get_xticks()[::3])
    axes[1,2].set_xticks(axes[1,2].get_xticks()[::3])

    # set margin of the figure
    plt.subplots_adjust(hspace=0.3, wspace=0.4, left=0.05, right=0.95, top=0.95, bottom=0.09)

def logReturns_overview_of_seasonality(symbol, restrictTradingHours=False, ytdlineplot=False):
    """
    Generate a figure with subplots showing the seasonality of log returns for a given symbol.

    Parameters:
    - symbol (str): The symbol for which to generate the seasonality overview.
    - restrictTradingHours (bool): Whether to restrict the trading hours to 9:30am to 4pm.
    - ytdlineplot (bool): Whether to include a line plot for log returns of the current year.

    Returns:
    - fig (matplotlib.figure.Figure): The generated figure with subplots showing the seasonality of log returns.
    """
    # get px history from db
    with db.sqlite_connection(dbname_stock) as conn:
        pxHistory_htf = db.getPriceHistory(conn, symbol, '1day', withpctChange=True)
        pxHistory_ltf = db.getPriceHistory(conn, symbol, '30mins', withpctChange=True)

    # Restrict trading hours to 9:30am to 4pm if specified
    if restrictTradingHours:
        pxHistory_ltf = pxHistory_ltf[(pxHistory_ltf['date'].dt.time >= dt.time(9, 30)) & (pxHistory_ltf['date'].dt.time <= dt.time(15, 55))]

    # Calculate log returns for px history
    logReturn_htf = ut.calcLogReturns(pxHistory_htf, 'close')
    logReturn_ltf = ut.calcLogReturns(pxHistory_ltf, 'close')
    
    # Create figure and axes
    fig, axes = plt.subplots(2, 3, figsize=(19, 9))

    # Add title to the figure
    fig.suptitle('Log Return Seasonality for %s (%s years of data)'%(symbol.upper(), round(len(pxHistory_htf)/252, 1)))

    # Monthly seasonality
    seasonalAggregate_yearByMonth_logReturns_1day = ut.aggregate_by_month(logReturn_htf, 'logReturn')

    # Plot yearly seasonality
    ax1 = axes[0,0]
    ax2 = ax1.twinx()
    sns.barplot(x=seasonalAggregate_yearByMonth_logReturns_1day.index, y='std', data=seasonalAggregate_yearByMonth_logReturns_1day, ax=ax1, color='grey', alpha=0.5)
    sns.barplot(x=seasonalAggregate_yearByMonth_logReturns_1day.index, y='mean', data=seasonalAggregate_yearByMonth_logReturns_1day, ax=ax2, color='red', alpha=0.75)
    axes[0,0].set_title('Yearly Seasonality')
    axes[0,0].set_xticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])

    # Plot current year log returns if ytdlineplot is True
    if ytdlineplot == True:
        fig.suptitle('Return Seasonality for %s vs %s return (%s years of data)'%(symbol.upper(), logReturn_htf['date'].dt.year.max(), round(len(pxHistory_htf)/252, 1)))
        logReturn_1day_currentYear = logReturn_htf[logReturn_htf['date'].dt.year == logReturn_htf['date'].dt.year.max()].reset_index(drop=True)
        seasonalAggregate_logReturnsForCurrentyear = ut.aggregate_by_month(logReturn_1day_currentYear, 'logReturn')
        sns.lineplot(x=seasonalAggregate_logReturnsForCurrentyear.index, y='mean', data=seasonalAggregate_logReturnsForCurrentyear, ax=ax2, color='green', alpha=1)

    # Day of month seasonality
    aggregate_day_of_month = ut.aggregate_by_dayOfMonth(logReturn_htf, 'logReturn')
    ax3 = axes[0,1]
    ax4 = ax3.twinx()
    sns.barplot(x=aggregate_day_of_month.index, y='std', data=aggregate_day_of_month, ax=ax3, color='grey', alpha=0.5)
    sns.barplot(x=aggregate_day_of_month.index, y='mean', data=aggregate_day_of_month, ax=ax4, color='red', alpha=0.6)
    axes[0,1].set_title('Day of Month Seasonality')
    axes[0,1].set_xlabel('Day of Month')
    axes[0,1].set_xticks(axes[0,1].get_xticks()[::2])

    if ytdlineplot == True:
        aggregate_day_of_month_currentYear = ut.aggregate_by_dayOfMonth(logReturn_1day_currentYear, 'logReturn')
        sns.lineplot(x=aggregate_day_of_month_currentYear.index, y='mean', data=aggregate_day_of_month_currentYear, ax=ax4, color='green', alpha=1)

    # Day of week seasonality
    aggregate_day_of_week = ut.aggregate_by_dayOfWeek(logReturn_htf, 'logReturn')
    ax5 = axes[0,2]
    ax6 = ax5.twinx()
    sns.barplot(x=aggregate_day_of_week.index, y='std', data=aggregate_day_of_week, ax=ax5, color='grey', alpha=0.5)
    sns.barplot(x=aggregate_day_of_week.index, y='mean', data=aggregate_day_of_week, ax=ax6, color='red', alpha=1)
    axes[0,2].set_title('Day of Week Seasonality')
    axes[0,2].set_xlabel('Day of Week')
    axes[0,2].set_xticklabels(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])

    if ytdlineplot == True:
        aggregate_day_of_week_currentYear = ut.aggregate_by_dayOfWeek(logReturn_1day_currentYear, 'logReturn')
        sns.lineplot(x=aggregate_day_of_week_currentYear.index, y='mean', data=aggregate_day_of_week_currentYear, ax=ax6, color='green', alpha=1)

    # Intra-day seasonality
    aggregate_timestamp_5mins = ut.aggregate_by_timestamp(logReturn_ltf, 'logReturn')
    aggregate_timestamp_5mins['cumsum'] = aggregate_timestamp_5mins['mean'].cumsum()
    print(logReturn_ltf)
    ax7 = axes[1,0]
    ax8 = ax7.twinx()
    sns.barplot(x=aggregate_timestamp_5mins.index, y='std', data=aggregate_timestamp_5mins, ax=ax7, color='grey', alpha=0.5)
    sns.barplot(x=aggregate_timestamp_5mins.index, y='mean', data=aggregate_timestamp_5mins, ax=ax8, color='red', alpha=1)
    sns.lineplot(x=aggregate_timestamp_5mins.index, y='cumsum', data=aggregate_timestamp_5mins, ax=ax8, color='grey', alpha=0.5, linestyle='--')
    axes[1,0].set_title('Intra-Day Seasonality')
    axes[1,0].set_xlabel('Time of Day')
    axes[1,0].set_xticklabels(aggregate_timestamp_5mins['timestamp'], rotation=90, fontsize=8)

    if ytdlineplot == True:
        aggregate_timestamp_5mins_currentYear = ut.aggregate_by_timestamp(logReturn_ltf[logReturn_ltf['date'].dt.year == logReturn_ltf['date'].dt.year.max()], 'logReturn')
        sns.lineplot(x=aggregate_timestamp_5mins_currentYear.index, y='mean', data=aggregate_timestamp_5mins_currentYear, ax=ax8, color='green', alpha=1)

    # Intra-day seasonality restricted to trading hours
    logReturn_5mins_restricted = logReturn_ltf[(logReturn_ltf['date'].dt.time >= dt.time(9, 30)) & (logReturn_ltf['date'].dt.time <= dt.time(15, 55))]
    aggregate_logReturn_5mins_restricted = ut.aggregate_by_timestamp(logReturn_5mins_restricted, 'logReturn')
    aggregate_logReturn_5mins_restricted['cumsum'] = aggregate_logReturn_5mins_restricted['mean'].cumsum()
    ax9 = axes[1,1]
    ax10 = ax9.twinx()
    sns.barplot(x=aggregate_logReturn_5mins_restricted.index, y='std', data=aggregate_logReturn_5mins_restricted, ax=ax9, color='grey', alpha=0.5)
    sns.barplot(x=aggregate_logReturn_5mins_restricted.index, y='mean', data=aggregate_logReturn_5mins_restricted, ax=ax10, color='red', alpha=1)
    sns.lineplot(x=aggregate_logReturn_5mins_restricted.index, y='cumsum', data=aggregate_logReturn_5mins_restricted, ax=ax10, color='grey', alpha=0.5, linestyle='--')
    axes[1,1].set_title('Intra-Day Seasonality (Restricted Hours)')
    axes[1,1].set_xlabel('Time of Day')
    axes[1,1].set_xticklabels(aggregate_logReturn_5mins_restricted['timestamp'], rotation=90, fontsize=8)

    if ytdlineplot == True:
        aggregate_logReturn_5mins_restricted_currentYear = ut.aggregate_by_timestamp(logReturn_5mins_restricted[logReturn_5mins_restricted['date'].dt.year == logReturn_5mins_restricted['date'].dt.year.max()], 'logReturn')
        sns.lineplot(x=aggregate_logReturn_5mins_restricted_currentYear.index, y='mean', data=aggregate_logReturn_5mins_restricted_currentYear, ax=ax10, color='green', alpha=1)

    # Heatmap of intra-day log returns for last 30 days
    pivot_logReturn_5mins_restricted = logReturn_5mins_restricted.pivot_table(index=logReturn_5mins_restricted['date'].dt.time, columns=logReturn_5mins_restricted['date'].dt.date, values='logReturn')
    pivot_logReturn_5mins_restricted = pivot_logReturn_5mins_restricted[pivot_logReturn_5mins_restricted.columns[-30:]]
    sns.heatmap(pivot_logReturn_5mins_restricted, ax=axes[1,2], center=0, cmap='RdYlGn')
    axes[1,2].set_title('Intra-Day log returns for last 30 days')

    plt.tight_layout()
    return fig

def legReturn_seasonality_ltf_dashboard(symbol, restrictTradingHours = False, ytdLineplot=False): 
    """
        plots a dashboard (4x4) of ltf = [1min, 5min, 15min] seasonality for a given symbol
    """
    # get px history from db
    with db.sqlite_connection(dbname_stock) as conn:
        pxHistory_1min = db.getPriceHistory(conn, symbol, '1min', withpctChange=True)
        pxHistory_5min = db.getPriceHistory(conn, symbol, '5min', withpctChange=True)
        pxHistory_15min = db.getPriceHistory(conn, symbol, '15min', withpctChange=True)

    # Restrict trading hours to 9:30am to 4pm if specified
    if restrictTradingHours:
        pxHistory_1min = pxHistory_1min[(pxHistory_1min['date'].dt.time >= dt.time(9, 30)) & (pxHistory_1min['date'].dt.time <= dt.time(15, 55))]
        pxHistory_5min = pxHistory_5min[(pxHistory_5min['date'].dt.time >= dt.time(9, 30)) & (pxHistory_5min['date'].dt.time <= dt.time(15, 55))]
        pxHistory_15min = pxHistory_15min[(pxHistory_15min['date'].dt.time >= dt.time(9, 30)) & (pxHistory_15min['date'].dt.time <= dt.time(15, 55))]

    # Calculate log returns for px history
    logReturn_1min = ut.calcLogReturns(pxHistory_1min, 'close')
    logReturn_5min = ut.calcLogReturns(pxHistory_5min, 'close')
    logReturn_15min = ut.calcLogReturns(pxHistory_15min, 'close')

    # Create figure and axes
    fig, axes = plt.subplots(4, 4, figsize=(19, 9))

    # Add title to the figure
    fig.suptitle('Log Return Seasonality for %s (%s years of data)'%(symbol.upper(), round(len(pxHistory_1min)/252, 1)))

    # Monthly seasonality
    seasonalAggregate_yearByMonth_logReturns_1min = ut.aggregate_by_month(logReturn_1min, 'logReturn')
    seasonalAggregate_yearByMonth_logReturns_5min = ut.aggregate_by_month(logReturn_5min, 'logReturn')
    seasonalAggregate_yearByMonth_logReturns_15min = ut.aggregate_by_month(logReturn_15min, 'logRerurn')

"""
Returns seasonal aggregate of passed in pxhistory df
"""
def DEPRECATED_getSeasonalAggregate(pxHistory, interval, symbol, numdays=0):
    
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

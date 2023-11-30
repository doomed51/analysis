"""
    This module containts analysis function for multiple strategies for JPY currency
"""
import config 
import sys

from returns import calcReturns as calcReturns
import interface_localDB as db
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

sys.path.append('..')
from utils import utils

"""
    Simple implementation of monthly seasonality strategy. 
    inputs:
        - symbol [string] symbol to get price history for
        - startMonth [int] month to open long 
        - endMonth [int] month to close
    output:
        - dataframe with date, px, logReturn, cumsum 
        - Assumes opening and closing of positions at the END of target months
"""
def strategy_monthToMonth(symbol, startMonth, endMonth):

    # get price history
    with db.sqlite_connection(config.dbname_stock) as conn:
        try: 
            history = db.getPriceHistory(conn, symbol, '1day', withpctChange=False)
        except:
            print(f'ERROR: Could not retrieve price history for {symbol}')
            exit()

    ## add date columns for easier selection 
    history['month'] = history['date'].dt.month
    history['day'] = history['date'].dt.day
    history['year'] = history['date'].dt.year

    ## Create a dataframe conssiting of trade open and close dates in sequence 
    tradeDates = pd.DataFrame(columns=['date'])
    # from history, get the earliest available year for the startMonth we want
    earliestYear = history[history['month'] == startMonth]['year'].min()

    if endMonth < startMonth: #track end month is in the following year 
        endYearModifier = 1
    else:
        endYearModifier = 0

    # add the dates we want 
    for year in range(earliestYear, 2024):
        # dates trades are opened 
        tradeDates = tradeDates._append({'date': pd.Timestamp(year=year, month=startMonth, day=utils.getLastBusinessDay(year, startMonth))}, ignore_index=True)
        # dates trades are closed 
        tradeDates = tradeDates._append({'date': pd.Timestamp(year=year + endYearModifier, month=endMonth, day=utils.getLastBusinessDay(year + endYearModifier, endMonth))}, ignore_index=True)

    # select just these dates from history 
    history = history[history['date'].isin(tradeDates['date'])]

    # drop column logReturn, 
    history.drop(columns=['logReturn'], inplace=True)
    
    ## add column logReturn with returns for every second row in the dataframe
    history = utils.calcLogReturns(history, 'close')

    # set logReturn to 0 for every other row starting with the first row
    #history['logReturn'][::2] = 0
    history.loc[::2, 'logReturn'] = 0

    # drop rows with logReturn = 0
    history = history[history['logReturn'] != 0]

    #add cumsum column
    history['cumsum'] = history['logReturn'].cumsum()

    return history

def closest_day(group, targetDay):
   #target = pd.Timestamp(group.name.year, group.name.month, targetDay)
   #closest_date = group.loc[group.index.to_series().sub(target).abs().idxmin()]
   
   #add column daydiff = abs(targetDay - day)
   group['daydiff'] = abs(targetDay - group['day'])
   group = group.sort_values(by='daydiff', ascending=True)
   # select top two rows
   #group = group.head(2).sort_values(by='date', ascending=True)
   
   closest_date = group.iloc[0]['date']

   return closest_date

"""
    Simple implementation of day of month seasonality strategy. 
    inputs:
        - symbol [string] symbol to get price history for
        - startDay [int] day of month to open long 
        - endDay [int] day of month to close
    output:
        - dataframe with date, px, logReturn, cumsum 
        - Assumes opening and closing of positions at the END of target months
"""
def strategy_dayOfMonthSeasonality(symbol, startDay, endDay): 
    # get price history
    with db.sqlite_connection(config.dbname_stock) as conn:
        try: 
            history = db.getPriceHistory(conn, symbol, '1day', withpctChange=False)
        except:
            print(f'ERROR: Could not retrieve price history for {symbol}')
            exit()

    ## add date columns for easier selection 
    history['month'] = history['date'].dt.month
    history['day'] = history['date'].dt.day
    history['year'] = history['date'].dt.year
    
    # make a list dates to open and close trades 
    history_startDates = history.groupby(['year', 'month'], group_keys=False).apply(closest_day, startDay).reset_index() # get start dates
    history_startDates.rename(columns={0: 'date'}, inplace=True)
    history_endDates = history.groupby(['year', 'month'], group_keys=False).apply(closest_day, endDay).reset_index() # get end dates
    history_endDates.rename(columns={0: 'date'}, inplace=True)

    # make sure first end date is after first start date
    if history_endDates.iloc[0]['date'] <= history_startDates.iloc[0]['date']:
        history_endDates = history_endDates.iloc[1:]
    
    # select just the dates we want from history 
    history = history[(history['date'].isin(history_startDates['date'])) | (history['date'].isin(history_endDates['date']))]

    # recalculcate logReturn
    history = utils.calcLogReturns(history, 'close')
    # set logReturn to = 0 for every other row starting with the first row
    history.loc[::2, 'logReturn'] = 0
    # drop rows with logReturn = 0
    history = history[history['logReturn'] != 0]
    # add cumsum
    history['cumsum'] = history['logReturn'].cumsum()

    return history


"""
    This function will plot the results of the strategy
"""
def plotResults(returns, returns2=pd.DataFrame(), returns_merged=''):
    symbol = returns['symbol'].iloc[0]
    with db.sqlite_connection(config.dbname_stock) as conn:
        try: 
            history = db.getPriceHistory(conn, symbol, '1day', withpctChange=False)
            # add cumsum column
            history['cumsum'] = history['logReturn'].cumsum()
        except:
            print(f'ERROR: Could not retrieve price history for {symbol}')
            exit()
    # lineplot of cumsum
    fig, ax = plt.subplots(figsize=(15, 10))

    # seaborn lineplot of returns in red
    sns.lineplot(x='date', y='cumsum', data=returns, ax=ax, color='blue') 
    # calculate sharpe ratio
    sharpe = calcReturns.calcSharpeRatio(returns)
    # print sharpe on plot
    ax.text(0.05, 0.95, 'Sharpe Ratio: %.2f'%(sharpe), transform=ax.transAxes, fontsize=14, verticalalignment='top')

    # add return2 on the same axis
    if not returns2.empty:
        sns.lineplot(x='date', y='cumsum', data=returns2, ax=ax, color='green')

    ## add returns_merged
    if returns_merged:
        sns.lineplot(x='date', y='cumsum', data=returns_merged, ax=ax, color='orange')
    
    ## add history cumsum
    sns.lineplot(x='date', y='cumsum', data=history, ax=ax, color='black')

    ax.set_title('%s Cumulative Returns'%(history['symbol'].iloc[0]))
    ax.set_xlabel('Date')
    ax.set_ylabel('Cumulative Returns')

    return fig

"""    ## create proxy artists for legend
    baseline = plt.Line2D((0,1),(0,0), color='black', linestyle='-')
    julyToNov = plt.Line2D((0,1),(0,0), color='blue', linestyle='-')
    janToMarch = plt.Line2D((0,1),(0,0), color='green', linestyle='-')
    combined = plt.Line2D((0,1),(0,0), color='orange', linestyle='-')

    # add legend with red = 'june to nov', orange='jan to march'
    ax.legend([baseline, julyToNov, combined, janToMarch], ['history', 'july to nov', 'combined', 'jan to march'])"""

""" 
    plot the return distribution of the strategy along with mean and sd 
"""
def plotReturnDistribution(returns):
    # calculate mean and sd of returns
    mean = returns['logReturn'].mean()
    sd = returns['logReturn'].std()

    # create figure and axes
    fig, ax = plt.subplots(figsize=(10, 6))

    # seaborn distplot of returns in red
    sns.distplot(returns['logReturn'], ax=ax, color='red', kde=True, hist=True, bins=150) 
    # plot mean and sd
    ax.axvline(mean, color='black', linestyle='--')
    ax.axvline(mean + sd, color='blue', linestyle='--')
    ax.axvline(mean - sd, color='blue', linestyle='--')

    # print mean on plot 
    ax.text(0.05, 0.95, 'Mean: %.2f'%(mean), transform=ax.transAxes, fontsize=14, verticalalignment='top')
    # print sd on plot
    ax.text(0.05, 0.90, 'SD: %.2f'%(sd), transform=ax.transAxes, fontsize=14, verticalalignment='top')

    ax.set_title('%s Return Distribution'%(returns['symbol'].iloc[0]))
    ax.set_xlabel('Log Return')
    ax.set_ylabel('Density')

    return fig
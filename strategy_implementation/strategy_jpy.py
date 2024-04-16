"""
    This module containts analysis function for multiple strategies for JPY currency
"""
import config 
import sys

import calcReturns as calcReturns
import interface_localDB as db
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

sys.path.append('..')
from utils import utils as utils

"""
    Strategy 1: yearly seasonality, YCS 
    - long ycs end of july, close end of november
    inputs:
        - startMonth [int] month to open long 
        - endMonth [int] month to close
    output:
        - dataframe with date, px, logReturn, cumsum 
"""
def strategy_ycs(startMonth = 7, endMonth = 11):

    # get price history
    with db.sqlite_connection(config.dbname_stock) as conn:
        history = db.getPriceHistory(conn, 'YCS', '1day', withpctChange=False)

    ## add date columns for easier selection 
    history['month'] = history['date'].dt.month
    history['day'] = history['date'].dt.day
    history['year'] = history['date'].dt.year

    # create dataframe with date column consisting of the last *business* day for july and november for each year starting in 2009
    tradeOpenDates = pd.DataFrame(columns=['date'])
    # from history, get the earliest available year for the startMonth we want
    earliestYear = history[history['month'] == startMonth]['year'].min()

    # make sure endMonth also correspots to the next year 
    if endMonth < startMonth:
        endYearModifier = 1
    else:
        endYearModifier = 0

    # add the dates we want 
    for year in range(earliestYear, 2024):
        tradeOpenDates = tradeOpenDates._append({'date': pd.Timestamp(year=year, month=startMonth, day=utils.getLastBusinessDay(year, startMonth))}, ignore_index=True)
        tradeOpenDates = tradeOpenDates._append({'date': pd.Timestamp(year=year + endYearModifier, month=endMonth, day=utils.getLastBusinessDay(year + endYearModifier, endMonth))}, ignore_index=True)

    # select just these dates from history 
    history = history[history['date'].isin(tradeOpenDates['date'])]

    # drop the following columns: logReturn, 
    history.drop(columns=['logReturn'], inplace=True)
    
    ## add column logReturn with returns for every second row in the dataframe
    history = utils.calcLogReturns(history, 'close')

    # set logReturn to 0 for every other row starting with the first row
    #history['logReturn'][::2] = 0
    history.loc[::2, 'logReturn'] = 0

    #add cumsum column
    history['cumsum'] = history['logReturn'].cumsum()

    return history

"""
    This function will plot the results of the strategy
"""
def plotResults_ycs(history, returns, returns2, returns_merged):
    # lineplot of cumsum
    fig, ax = plt.subplots(figsize=(15, 10))

    # seaborn lineplot of returns in red
    sns.lineplot(x='date', y='cumsum', data=returns, ax=ax, color='blue') 

    # add return2 on the same axis
    sns.lineplot(x='date', y='cumsum', data=returns2, ax=ax, color='green')

    ## add returns_merged
    sns.lineplot(x='date', y='cumsum', data=returns_merged, ax=ax, color='orange')
    
    ## add history cumsum
    sns.lineplot(x='date', y='cumsum', data=history, ax=ax, color='black')

    ax.set_title('YCS Cumulative Returns')
    ax.set_xlabel('Date')
    ax.set_ylabel('Cumulative Returns')

    ## create proxy artists for legend
    baseline = plt.Line2D((0,1),(0,0), color='black', linestyle='-')
    julyToNov = plt.Line2D((0,1),(0,0), color='blue', linestyle='-')
    janToMarch = plt.Line2D((0,1),(0,0), color='green', linestyle='-')
    combined = plt.Line2D((0,1),(0,0), color='orange', linestyle='-')

    # add legend with red = 'june to nov', orange='jan to march'
    ax.legend([baseline, julyToNov, combined, janToMarch], ['history', 'july to nov', 'combined', 'jan to march'])
    
# get price history
with db.sqlite_connection(config.dbname_stock) as conn:
    history = db.getPriceHistory(conn, 'YCS', '1day', withpctChange=False)
    ## add cumsum
    history['cumsum'] = history['logReturn'].cumsum()
    
returns = strategy_ycs()
returns2 = strategy_ycs(1, 3)
# returns_merged = append returns and returns2
returns_merged = returns._append(returns2)
# drop logReturns = 0, and order by date sorted by old to new 
returns_merged = returns_merged[returns_merged['logReturn'] != 0].sort_values(by='date', ascending=True)
# recalculcate cumsum
returns_merged['cumsum'] = returns_merged['logReturn'].cumsum()
print(returns_merged)

plotResults_ycs(history, returns, returns2, returns_merged)

plt.show()
    
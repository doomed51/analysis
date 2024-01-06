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

"""

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
def strategy_monthToMonth(symbol, startMonth, endMonth, direction=1):

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
    history = utils.calcLogReturns(history, 'close', direction=direction)

    # set logReturn to 0 for every other row starting with the first row
    #history['logReturn'][::2] = 0
    history.loc[::2, 'logReturn'] = 0

    # drop rows with logReturn = 0
    history = history[history['logReturn'] != 0]

    #add cumsum column
    history['cumsum'] = history['logReturn'].cumsum()

    return history.reset_index(drop=True)

"""
    Simple implementation of day of month seasonality strategy. 
    inputs:
        - symbol [string] symbol to get price history for
        - startDay [int] day of month to open long 
        - endDay [int] day of month to close
        - direction [int] 1 = open long, -1 = open short
    output:
        - dataframe with date, px, logReturn, cumsum 
        - Assumes opening and closing of positions at the END of target months
"""
def strategy_dayOfMonthSeasonality(symbol, startDay, endDay, direction=1): 
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
    history_startDates = history.groupby(['year', 'month'], group_keys=False).apply(utils.closest_day, startDay).reset_index() # get start dates
    history_startDates.rename(columns={0: 'date'}, inplace=True)
    history_endDates = history.groupby(['year', 'month'], group_keys=False).apply(utils.closest_day, endDay).reset_index() # get end dates
    history_endDates.rename(columns={0: 'date'}, inplace=True)

    # make sure the list of trades begins with an opening trade
    if history_endDates.iloc[0]['date'] <= history_startDates.iloc[0]['date']:
        history_endDates = history_endDates.iloc[1:]
    
    # get px history for trade open and close dates
    history = history[(history['date'].isin(history_startDates['date'])) | (history['date'].isin(history_endDates['date']))]

    # Calculate returns on trades 
    history = utils.calcLogReturns(history, colName = 'close', direction=direction)
    # drop open 
    history.loc[::2, 'logReturn'] = 0
    # drop rows with logReturn = 0
    history = history[history['logReturn'] != 0]
    # add cumsum
    history['cumsum'] = history['logReturn'].cumsum()

    return history.reset_index(drop=True)

"""
    This function will plot results of a stragegy df 
    inputs:
        - returns [] array of dataframes with columns: [date, px, logReturn, cumsum]
"""
def plotResults(returns = [], benchmark='SPY'):#, returns2=pd.DataFrame(), returns_merged=pd.DataFrame()):
    if benchmark == '':
        benchmark = returns[0]['symbol'][0]
    history_underlying = pd.DataFrame()
    with db.sqlite_connection(config.dbname_stock) as conn:
        try: 
            history = db.getPriceHistory(conn, benchmark, '1day', withpctChange=False)
            if benchmark != returns[0]['symbol'][0]:
                history_underlying = db.getPriceHistory(conn, returns[0]['symbol'][0], '1day', withpctChange=False)
            elif benchmark == returns[0]['symbol'][0]:
                history_underlying = history 

        except:
            print(f'ERROR: Could not retrieve price history for {benchmark}')
            exit()
    
    # make sure dates in benchmark > min date.month in returns
    minDate = returns[0]['date'].min()
    history = history[history['date'] >= minDate].reset_index(drop=True)
    # add cumsum column
    history['cumsum'] = history['logReturn'].cumsum()

    if not history_underlying.empty:
        # add cumsum column
        history_underlying['cumsum'] = history_underlying['logReturn'].cumsum()
    
    # lineplot of cumsum
    fig, ax = plt.subplots()
    for i, strategyReturn in enumerate(returns):

        # check if strategyReturn had strategyName column
        if 'strategyName' in strategyReturn.columns:
            strategyName = strategyReturn['strategyName'][0]
        else:
            strategyName = 'strat %s'%(i+1)

        # seaborn lineplot of returns in red
        sns.lineplot(x='date', y='cumsum', data=strategyReturn, ax=ax, label=strategyName)
        if i == len(returns) - 1:
            # calculate sharpe ratio
            sharpe = calcReturns.calcSharpeRatio(strategyReturn, history_underlying)
            sharpe_benchmark = calcReturns.calcSharpeRatio(strategyReturn, history)
            # print sharpe on plot
            ax.text(0.05, 0.05, 'Sharpe[[%s]]: %.2f'%(strategyName, sharpe), transform=ax.transAxes, fontsize=14, verticalalignment='bottom', bbox=dict(facecolor='white', alpha=0.95, edgecolor='black'))
            # add another text box with a different sharpe 
            ax.text(0.05, 0.01, 'Sharpe Vs. %s[[%s]]:%.2f'%(history['symbol'][0], strategyName, sharpe_benchmark), transform=ax.transAxes, fontsize=14, verticalalignment='bottom', bbox=dict(facecolor='white', alpha=0.95, edgecolor='black'))
    
    ## add history cumsum
    sns.lineplot(x='date', y='cumsum', data=history, ax=ax, color='black', label=benchmark)
    if not history_underlying.empty:
        sns.lineplot(x='date', y='cumsum', data=history_underlying, ax=ax, color='grey', label=returns[0]['symbol'][0])

    ax.set_title('%s Cumulative Returns'%(returns[0]['symbol'][0]))
    ax.set_xlabel('Date')
    ax.set_ylabel('Cumulative Returns')

    # place legend in upper left 
    ax.legend(loc='upper left')

    return fig

""" 
    plot the return distribution of the strategy along with mean and sd 
"""
def plotReturnDistribution(returns):
    # calculate mean and sd of returns
    mean = returns['logReturn'].mean()
    sd = returns['logReturn'].std()

    # create figure and axes
    fig, ax = plt.subplots(figsize=(10, 6))

    # seaborn histplot of returns in red
    sns.histplot(returns['logReturn'], ax=ax, color='red', kde=True, bins=150) 
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

def mergeStrategies(returns):
    # assert returns is a list
    assert isinstance(returns, list), 'ERROR: returns must be a list'
    return utils.mergeStrategyReturns(returns)
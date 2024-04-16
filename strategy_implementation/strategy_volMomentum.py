"""
    Startegy: Volatility Momentum
    Description:
     - short when momo > top x percentiles
"""
import config 
import sys

import calcReturns as calcReturns
import interface_localDB as db
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

sys.path.append('..')
from utils import utils
import momentum as momo

def strategy_volMom(symbol, interval, topPercentile = 0.998, momoPeriods=[3, 6, 12, 24, 48, 96], fwdReturns = [1, 5, 10, 15, 20, 25, 30]):
    # get price history for vix
    symbol = 'VIX'
    with db.sqlite_connection(config.dbname_stock) as conn:
        try: 
            vix = db.getPriceHistory(conn, symbol, interval, withpctChange=False)
            print(vix.tail(50))
            exit()
        except:
            print(f'ERROR: Could not retrieve price history for {symbol}')
            exit()
    
    # add momentum factor columns 
    for period in momoPeriods:
        vix = momo.calcMomoFactor(vix, period)
        vix.rename(columns={'momo': 'momo%s'%(period)}, inplace=True)
        vix.rename(columns={'lagmomo': 'lagmomo%s'%(period)}, inplace=True)
    
    # add forward returns columns
    _n=1
    for period in fwdReturns:
        vix['fwdReturns%s'%(_n)] = vix['close'].pct_change(period).shift(-period)
        _n+=1
    
    # calcLogReturns with lag = [1, 3, 5, 10, 15, 20, 25, 30]
    logReturnLags = [1, 3, 5, 10, 15, 20, 25, 30]
    for lag in logReturnLags:
        vix = utils.calcLogReturns(vix, 'close', lag=lag)
        vix.rename(columns={'logReturn': 'logReturn%s'%(lag)}, inplace=True)
    
    print(vix.head(50))
    exit()

    # limit vix to market hours 
    #vix = vix[(vix['date'].dt.hour >= 9) & (vix['date'].dt.hour <= 16)]
    vix48 = (vix[vix['momo48'] > vix['momo48'].quantile(topPercentile)]).copy()
    # vix48 reset index 
    vix48.reset_index(drop=True, inplace=True)

    print(vix['date'].count())
    print(vix48['date'].count())

    
    
    # add cumsum
    vix48['cumsum1'] = vix48['logReturn1'].cumsum()
    vix48['cumsum3'] = vix48['logReturn3'].cumsum()
    vix48['cumsum5'] = vix48['logReturn5'].cumsum()
    vix48['cumsum10'] = vix48['logReturn10'].cumsum()
    vix48['cumsum15'] = vix48['logReturn15'].cumsum()
    vix48['cumsum20'] = vix48['logReturn20'].cumsum()
    vix48['cumsum25'] = vix48['logReturn25'].cumsum()
    vix48['cumsum30'] = vix48['logReturn30'].cumsum()
    
    print(vix48[['date', 'close', 'momo48', 'logReturn1', 'cumsum1', 'logReturn3', 'cumsum3', 'logReturn5', 'logReturn10', 'logReturn15', 'logReturn20', 'logReturn25', 'logReturn30', 'cumsum5', 'cumsum10', 'cumsum15', 'cumsum20', 'cumsum25', 'cumsum30']].head(50))


    return vix48

    # select records with momo48 > topPercentile
    vix_48 = vix[vix['momo48'] > vix['momo48'].quantile(topPercentile)].copy()
    vix_12 = vix[vix['momo12'] > vix['momo12'].quantile(topPercentile)].copy()
    



    """  # create 2x3 grid of subplots
    fig, ax = plt.subplots(2, 4, figsize=(16, 8), sharex=True, sharey=True)
    # use seaborn
    sns.set()

    # plot scatter of momo48 vs fwdReturns1
    sns.scatterplot(x='momo48', y='fwdReturns1', data=vix_48, ax=ax[0, 0])
    # plot scatter of momo48 vs fwdReturns2
    sns.scatterplot(x='momo48', y='fwdReturns2', data=vix_48, ax=ax[0, 1])
    # plot scatter of momo48 vs fwdReturns3
    sns.scatterplot(x='momo48', y='fwdReturns3', data=vix_48, ax=ax[0, 2])
    # plot scatter of momo48 vs fwdReturns4
    sns.scatterplot(x='momo48', y='fwdReturns4', data=vix_48, ax=ax[1, 0])
    # plot scatter of momo48 vs fwdReturns5
    sns.scatterplot(x='momo48', y='fwdReturns5', data=vix_48, ax=ax[1, 1])
    # plot scatter of momo48 vs fwdReturns6
    sns.scatterplot(x='momo48', y='fwdReturns6', data=vix_48, ax=ax[1, 2])
    # plot scatter of momo48 vs fwdReturns7
    sns.scatterplot(x='momo48', y='fwdReturns7', data=vix_48, ax=ax[1, 3])
    
    # regplot
    sns.regplot(x='momo48', y='fwdReturns1', data=vix_48, ax=ax[0, 0])
    sns.regplot(x='momo48', y='fwdReturns2', data=vix_48, ax=ax[0, 1])
    sns.regplot(x='momo48', y='fwdReturns3', data=vix_48, ax=ax[0, 2])
    sns.regplot(x='momo48', y='fwdReturns4', data=vix_48, ax=ax[1, 0])
    sns.regplot(x='momo48', y='fwdReturns5', data=vix_48, ax=ax[1, 1])
    sns.regplot(x='momo48', y='fwdReturns6', data=vix_48, ax=ax[1, 2])
    sns.regplot(x='momo48', y='fwdReturns7', data=vix_48, ax=ax[1, 3])

    # set titles
    ax[0, 0].set_title('fwdReturns1')
    ax[0, 1].set_title('fwdReturns2')
    ax[0, 2].set_title('fwdReturns3')
    ax[1, 0].set_title('fwdReturns4')
    ax[1, 1].set_title('fwdReturns5')
    ax[1, 2].set_title('fwdReturns6')
    ax[1, 3].set_title('fwdReturns7')

    plt.show()"""

def plotLogReutrns(pxhistory):
    # create figure with 1 subplot
    fig, ax = plt.subplots(1, 1, figsize=(15, 10))

    # seaborn lineplot of logReturns 
    sns.lineplot(x='date', y='cumsum1', data=pxhistory, ax=ax, color='red')
    sns.lineplot(x='date', y='cumsum3', data=pxhistory, ax=ax, color='orange')
    sns.lineplot(x='date', y='cumsum5', data=pxhistory, ax=ax, color='yellow')
    sns.lineplot(x='date', y='cumsum10', data=pxhistory, ax=ax, color='green')
    sns.lineplot(x='date', y='cumsum15', data=pxhistory, ax=ax, color='blue')
    sns.lineplot(x='date', y='cumsum20', data=pxhistory, ax=ax, color='purple')
    sns.lineplot(x='date', y='cumsum25', data=pxhistory, ax=ax, color='black')
    sns.lineplot(x='date', y='cumsum30', data=pxhistory, ax=ax, color='brown')

    ax.set_title('VIX Log Returns - momo48 > 0.9')
    ax.set_xlabel('Date')
    ax.set_ylabel('Log Returns')
    ax.legend(['logReturn1', 'logReturn3', 'logReturn5', 'logReturn10', 'logReturn15', 'logReturn20', 'logReturn25', 'logReturn30'])

    plt.show()


vix99 = strategy_volMom('VIX', '30mins', topPercentile=0.99) 
plotLogReutrns(vix99)

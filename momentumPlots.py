"""
    This modules plots various momentum related plots 
        Functions return figures that can be plotted into tabbed window using utils_tabbedPlotsWindow.py
"""
import sys
sys.path.append('..')

import config
from impl import momentum

import statsmodels.api as sm 
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from interface import interface_localDB as db

from utils import utils_strategyAnalyzer as sa

###
""" Calcultes exponential moving average given pxhistory and period """
def ema(pxhistory, period): 
    return pxhistory.ewm(span=period, adjust=False).mean()

""" returns figure with 2 subplots:
        1. VVIX close price, ema5, ema10
        2. VVIX signal (ema5-ema10) vs. cumulative 5-period forward returns

"""
def plotEmas(pxhistory, period1, period2, forwardReturnsPeriod):
    # calc ema
    pxhistory['period1'] = ema(pxhistory['close'], period1)
    pxhistory['period2'] = ema(pxhistory['close'], period2)

    # calc signal as period1-period2
    pxhistory['signal'] = pxhistory['period1'] - pxhistory['period2']

    # plot vvix and period1
    sns.set_theme(style="darkgrid")
    fig, ax = plt.subplots(1,2, figsize=(20, 10))
    sns.set()
    # plot vix close price, and plot signal in a plot below; ignore missing values
    sns.lineplot(ax=ax[0], data=pxhistory, x='date', y='close', color='red')
    sns.lineplot(ax=ax[0], data=pxhistory, x='date', y='period1', color='blue')
    sns.lineplot(ax=ax[0], data=pxhistory, x='date', y='period2', color='green')
    ax[0].set_title('5min bars')
    ax[0].set_xlabel('date')
    ax[0].set_ylabel('close price')
    ax[0].legend(['close', 'period1', 'period2'])

    # check signal vs. cumulative n-peroid forward returns 
    pxhistory['fwdReturns'] = pxhistory['close'].pct_change(forwardReturnsPeriod).shift(forwardReturnsPeriod)
    # scatter and regplot 
    sns.scatterplot(ax=ax[1], data=pxhistory, x='signal', y='fwdReturns')
    sns.regplot(ax=ax[1], data=pxhistory, x='signal', y='fwdReturns')
    ax[1].set_title('signal vs. %s-period forward returns'%(forwardReturnsPeriod))
    ax[1].set_xlabel('signal')
    ax[1].set_ylabel('%s-period forward returns'%(forwardReturnsPeriod))
    ax[1].legend(['fwdReturns'])

    return fig

"""
    plot scatters of next n period returns vs (short) mom given momPeriod <short> & <long>, highlight when the longer period mom is positive & negative 
    lag returns by = 3, 6, 12, 24, 48, and 96 timeperiods  

"""
def plotMomoScatter(pxhistory, momPeriod1=10, momPeriod2=30, forwardReturnsPeriods=[1,3, 6, 12, 24, 48, 96]):
    # check which momoperiod is bigger
    if momPeriod1 > momPeriod2:
        longMomo = momPeriod1
        shortMomo = momPeriod2
    else:
        longMomo = momPeriod2
        shortMomo = momPeriod1
    # get momo 1 & rename returned columns
    pxhistory = momentum.calcMomoFactor(pxhistory, lag=shortMomo)
    pxhistory.rename(columns={'momo': 'shortMomo', 'lagmomo': 'lagShortMomo'}, inplace=True)
    
    # get momo 2 & rename returned columns
    pxhistory = momentum.calcMomoFactor(pxhistory, lag=longMomo)
    pxhistory.rename(columns={'momo': 'longMomo', 'lagmomo': 'lagLongMomo'}, inplace=True)

    # get forward returns for each ? in forwardReturnsPeriods
    _n=1
    for period in forwardReturnsPeriods:
        pxhistory['fwdReturns%s'%(_n)] = pxhistory['close'].pct_change(period).shift(-period)
        _n+=1
    
    # add new column 'longMomoState' that is 'positive' if longMomo is positive, 'negative' if negative
    pxhistory['longMomoState'] = pxhistory['longMomo'].apply(lambda x: 'positive' if x >= 0 else 'negative')
    
    # create 2x4 figure with scatter of shortMomo vs fwdreturnsPeriods where hue = longMomoState
    sns.set_theme(style="darkgrid")
    fig, ax = plt.subplots(2,7, figsize=(20, 10), sharex=True, sharey=True)
    sns.set()

    # plot scatter of shortMomo vs fwdReturnsPeriods where hue = longMomoState
    sns.scatterplot(ax=ax[0,0], data=pxhistory, x='shortMomo', y='fwdReturns1', hue='longMomoState')
    sns.scatterplot(ax=ax[0,1], data=pxhistory, x='shortMomo', y='fwdReturns2', hue='longMomoState')
    sns.scatterplot(ax=ax[0,2], data=pxhistory, x='shortMomo', y='fwdReturns3', hue='longMomoState')
    sns.scatterplot(ax=ax[0,3], data=pxhistory, x='shortMomo', y='fwdReturns4', hue='longMomoState')
    sns.scatterplot(ax=ax[0,4], data=pxhistory, x='shortMomo', y='fwdReturns5', hue='longMomoState')
    sns.scatterplot(ax=ax[0,5], data=pxhistory, x='shortMomo', y='fwdReturns6', hue='longMomoState')
    sns.scatterplot(ax=ax[0,6], data=pxhistory, x='shortMomo', y='fwdReturns7', hue='longMomoState')
    sns.scatterplot(ax=ax[1,0], data=pxhistory, x='longMomo', y='fwdReturns1')
    sns.scatterplot(ax=ax[1,1], data=pxhistory, x='longMomo', y='fwdReturns2')
    sns.scatterplot(ax=ax[1,2], data=pxhistory, x='longMomo', y='fwdReturns3')
    sns.scatterplot(ax=ax[1,3], data=pxhistory, x='longMomo', y='fwdReturns4')
    sns.scatterplot(ax=ax[1,4], data=pxhistory, x='longMomo', y='fwdReturns5')
    sns.scatterplot(ax=ax[1,5], data=pxhistory, x='longMomo', y='fwdReturns6')
    sns.scatterplot(ax=ax[1,6], data=pxhistory, x='longMomo', y='fwdReturns7')


    # plot regplot of shortMomo vs fwdReturnsPeriods where hue = longMomoState
    sns.regplot(ax=ax[0,0], data=pxhistory, x='shortMomo', y='fwdReturns1', scatter=False)
    sns.regplot(ax=ax[0,1], data=pxhistory, x='shortMomo', y='fwdReturns2', scatter=False)
    sns.regplot(ax=ax[0,2], data=pxhistory, x='shortMomo', y='fwdReturns3', scatter=False)
    sns.regplot(ax=ax[0,3], data=pxhistory, x='shortMomo', y='fwdReturns4', scatter=False)
    sns.regplot(ax=ax[0,4], data=pxhistory, x='shortMomo', y='fwdReturns5', scatter=False)
    sns.regplot(ax=ax[0,5], data=pxhistory, x='shortMomo', y='fwdReturns6', scatter=False)
    sns.regplot(ax=ax[0,6], data=pxhistory, x='shortMomo', y='fwdReturns7', scatter=False)
    sns.regplot(ax=ax[1,0], data=pxhistory, x='longMomo', y='fwdReturns1', scatter=False)
    sns.regplot(ax=ax[1,1], data=pxhistory, x='longMomo', y='fwdReturns2', scatter=False)
    sns.regplot(ax=ax[1,2], data=pxhistory, x='longMomo', y='fwdReturns3', scatter=False)
    sns.regplot(ax=ax[1,3], data=pxhistory, x='longMomo', y='fwdReturns4', scatter=False)
    sns.regplot(ax=ax[1,4], data=pxhistory, x='longMomo', y='fwdReturns5', scatter=False)
    sns.regplot(ax=ax[1,5], data=pxhistory, x='longMomo', y='fwdReturns6', scatter=False)
    sns.regplot(ax=ax[1,6], data=pxhistory, x='longMomo', y='fwdReturns7', scatter=False)

    # calculate rsquared for each regplot
    rsquared1 = smf.ols(formula='fwdReturns1 ~ shortMomo', data=pxhistory[['shortMomo', 'fwdReturns1']]).fit()
    rsquared2 = smf.ols(formula='fwdReturns2 ~ shortMomo', data=pxhistory[['shortMomo', 'fwdReturns2']]).fit()
    rsquared3 = smf.ols(formula='fwdReturns3 ~ shortMomo', data=pxhistory[['shortMomo', 'fwdReturns3']]).fit()
    rsquared4 = smf.ols(formula='fwdReturns4 ~ shortMomo', data=pxhistory[['shortMomo', 'fwdReturns4']]).fit()
    rsquared5 = smf.ols(formula='fwdReturns5 ~ shortMomo', data=pxhistory[['shortMomo', 'fwdReturns5']]).fit()
    rsquared6 = smf.ols(formula='fwdReturns6 ~ shortMomo', data=pxhistory[['shortMomo', 'fwdReturns6']]).fit()
    rsquared7 = smf.ols(formula='fwdReturns7 ~ shortMomo', data=pxhistory[['shortMomo', 'fwdReturns7']]).fit()
    rsquared8 = smf.ols(formula='fwdReturns1 ~ longMomo', data=pxhistory[['longMomo', 'fwdReturns1']]).fit()
    rsquared9 = smf.ols(formula='fwdReturns2 ~ longMomo', data=pxhistory[['longMomo', 'fwdReturns2']]).fit()
    rsquared10 = smf.ols(formula='fwdReturns3 ~ longMomo', data=pxhistory[['longMomo', 'fwdReturns3']]).fit()
    rsquared11 = smf.ols(formula='fwdReturns4 ~ longMomo', data=pxhistory[['longMomo', 'fwdReturns4']]).fit()
    rsquared12 = smf.ols(formula='fwdReturns5 ~ longMomo', data=pxhistory[['longMomo', 'fwdReturns5']]).fit()
    rsquared13 = smf.ols(formula='fwdReturns6 ~ longMomo', data=pxhistory[['longMomo', 'fwdReturns6']]).fit()
    rsquared14 = smf.ols(formula='fwdReturns7 ~ longMomo', data=pxhistory[['longMomo', 'fwdReturns7']]).fit()


    # set titles
    ax[0,0].set_title('shortMomo vs fwdReturns%s (r2=%s)'%(forwardReturnsPeriods[0], round(rsquared1.rsquared, 8)))
    ax[0,1].set_title('shortMomo vs fwdReturns%s (r2=%s)'%(forwardReturnsPeriods[1], round(rsquared2.rsquared, 8)))
    ax[0,2].set_title('shortMomo vs fwdReturns%s (r2=%s)'%(forwardReturnsPeriods[2], round(rsquared3.rsquared, 8)))
    ax[0,3].set_title('shortMomo vs fwdReturns%s (r2=%s)'%(forwardReturnsPeriods[3], round(rsquared4.rsquared, 8)))
    ax[0,4].set_title('shortMomo vs fwdReturns%s (r2=%s)'%(forwardReturnsPeriods[4], round(rsquared5.rsquared, 8)))
    ax[0,5].set_title('shortMomo vs fwdReturns%s (r2=%s)'%(forwardReturnsPeriods[5], round(rsquared6.rsquared, 8)))
    ax[0,6].set_title('shortMomo vs fwdReturns%s (r2=%s)'%(forwardReturnsPeriods[6], round(rsquared7.rsquared, 8)))
    ax[1,0].set_title('longMomo vs fwdReturns%s (r2=%s)'%(forwardReturnsPeriods[0], round(rsquared8.rsquared, 8)))
    ax[1,1].set_title('longMomo vs fwdReturns%s (r2=%s)'%(forwardReturnsPeriods[1], round(rsquared9.rsquared, 8)))
    ax[1,2].set_title('longMomo vs fwdReturns%s (r2=%s)'%(forwardReturnsPeriods[2], round(rsquared10.rsquared, 8)))
    ax[1,3].set_title('longMomo vs fwdReturns%s (r2=%s)'%(forwardReturnsPeriods[3], round(rsquared11.rsquared, 8)))
    ax[1,4].set_title('longMomo vs fwdReturns%s (r2=%s)'%(forwardReturnsPeriods[4], round(rsquared12.rsquared, 8)))
    ax[1,5].set_title('longMomo vs fwdReturns%s (r2=%s)'%(forwardReturnsPeriods[5], round(rsquared13.rsquared, 8)))
    ax[1,6].set_title('longMomo vs fwdReturns%s (r2=%s)'%(forwardReturnsPeriods[6], round(rsquared14.rsquared, 8)))


    # set xlabels
    ax[0,0].set_xlabel('shortMomo')
    ax[1,0].set_xlabel('longMomo')
    
    # set ylabels
    ax[0,0].set_ylabel('fwdReturns1')

    return fig 

"""
    plots quintiles of momo vs fwd returns 
"""
def plotMomoQuintiles(pxHistory, momoPeriods=[], fwdReturnPeriods=[], **kwargs):
    numQuintileBins = kwargs.get('numQuintileBins', 15) # number of quintile bins to use
    # get momo for each ? in momoPeriods
    for period in momoPeriods:
        # skip if momo already in pxHistory
        if 'momo%s'%(period) not in pxHistory.columns:
            pxHistory = momentum.calcMomoFactor(pxHistory, lag=period)
            pxHistory.rename(columns={'momo': 'momo%s'%(period)}, inplace=True)

    # get forward returns for each ? in fwdReturnPeriods
    for period in fwdReturnPeriods:
        pxHistory['fwdReturns%s'%(period)] = pxHistory['close'].pct_change(period).shift(-period)

    # put momo in 5 quintiles
    """
        TODO: move this to previous for loop
    """
    for period in momoPeriods:
        pxHistory['momo%sQuintile'%(period)] = pd.qcut(pxHistory['momo%s'%(period)], numQuintileBins, labels=False)
    
    # set numColumns to the length of fwdreturnperiods
    numColumns = max(1, len(fwdReturnPeriods))
    numRows = max(2, len(momoPeriods))

    # create figure
    sns.set_theme(style="darkgrid")
    fig, ax = plt.subplots(max(2, numRows), max(2, numColumns), figsize=(20, 10))
    sns.set_palette("dark")
    
    # plot barchart of momoquintiles vs fwdreturns
    sns.set()
    for row in range(numRows):
        for column in range(numColumns):
            # select subset of pxhistory 
            pxHistory_ = pxHistory[['momo%sQuintile'%(momoPeriods[row]), 'fwdReturns%s'%(fwdReturnPeriods[column])]]
            # group by quantile calculating mean of fwdreturns
            pxHistory_ = pxHistory_.groupby('momo%sQuintile'%(momoPeriods[row])).mean().reset_index()
            # barplot of quintile vs mean of fwdreturns for that quintile
            sns.barplot(ax=ax[row, column], data=pxHistory_, x='momo%sQuintile'%(momoPeriods[row]), y='fwdReturns%s'%(fwdReturnPeriods[column]), palette="Blues_d")
            ax[row, column].set_xlabel('momo%sQuintile'%(momoPeriods[row]))
            ax[row, column].set_ylabel('fwdReturns%s'%(fwdReturnPeriods[column]))

    # set title
    fig.suptitle('momo quintiles vs fwd returns')

    return fig
    

def plotMomoPairplot(pxhistory, momoPeriods=[3,5,8,13,21,34], forwardReturnsPeriods=[3,5,8,13,21,34]):
    
    # get momo for each ? in momoPeriods
    for period in momoPeriods:
        pxhistory = momentum.calcMomoFactor(pxhistory, lag=period)
        pxhistory.rename(columns={'momo': 'momo%s'%(period), 'lagmomo': 'lagMomo%s'%(period)}, inplace=True)

    # get forward returns for each ? in forwardReturnsPeriods
    _n=1
    for period in forwardReturnsPeriods:
        pxhistory['fwdReturns%s'%(_n)] = pxhistory['close'].pct_change(period).shift(-period)
        _n+=1
    
    # fig axis 
    fig, ax = plt.subplots(2,3, figsize=(20, 10), sharex=True, sharey=True)

    # create pairplot of momo vs fwdreturnsPeriods
    sns.set_theme(style="darkgrid")
    sns.set()
    sns.pairplot(data=pxhistory)

    return fig

"""
    plot scatters of momo crossover signal vs. fwd returns for each forwardReturnsPeriods 
"""
def plotMomoCrossoverSignal(pxHistory, momoPeriod1, momoPeriod2, forwardReturnsPeriods=[5,15,20, 25, 30, 35,40]):
    # set long and short momo 
    if momoPeriod1 > momoPeriod2:
        longMomo = momoPeriod1
        shortMomo = momoPeriod2
    else:
        longMomo = momoPeriod2
        shortMomo = momoPeriod1
    
    # calc shortMomo and longMomo
    pxHistory = momentum.calcMomoFactor(pxHistory, lag=shortMomo)
    pxHistory.rename(columns={'momo': 'shortMomo', 'lagmomo': 'lagShortMomo'}, inplace=True)
    pxHistory = momentum.calcMomoFactor(pxHistory, lag=longMomo)
    pxHistory.rename(columns={'momo': 'longMomo', 'lagmomo': 'lagLongMomo'}, inplace=True)

    # calc longMomo - shortMomo 
    pxHistory['longMinusShortMomo'] = pxHistory['longMomo'] - pxHistory['shortMomo']

    # calc signal as: 
    # 1: when long and short momo are both negative, and shortMomo > longMomo
    # -1: when long and short momo are both positive, and shortMomo < longMomo
    # 0: otherwise
    pxHistory['signal'] = pxHistory.apply(lambda x: 1 if (x['longMomo'] < 0) & (x['shortMomo'] < 0) & (x['shortMomo'] > x['longMomo']) else -1 if (x['longMomo'] > 0) & (x['shortMomo'] > 0) & (x['shortMomo'] < x['longMomo']) else 0, axis=1)

    # get forward returns for each ? in forwardReturnsPeriods
    n=1
    for period in forwardReturnsPeriods:
        pxHistory['fwdReturns%s'%(n)] = pxHistory['close'].pct_change(period).shift(-period)
        n+=1

    # add 90th and 10th longmomo and shortmomo percentile columns
    rollingPeriod = 300
    pxHistory['longMomo90th'] = pxHistory['longMomo'].rolling(rollingPeriod).quantile(.95)
    pxHistory['longMomo10th'] = pxHistory['longMomo'].rolling(rollingPeriod).quantile(.05)
    pxHistory['shortMomo90th'] = pxHistory['shortMomo'].rolling(rollingPeriod).quantile(.95)
    pxHistory['shortMomo10th'] = pxHistory['shortMomo'].rolling(rollingPeriod).quantile(.05)


    # create 2x4 figure with scatter of longMinusShortMomo vs fwdreturnsPeriods
    sns.set_theme(style="darkgrid")
    fig, ax = plt.subplots(2,4, figsize=(20, 10))
    sns.set()

    # plot longmomo, longMomo90th, and longMomo10th
    sns.lineplot(ax=ax[0,0], data=pxHistory, x='date', y='longMomo', color='red')
    sns.lineplot(ax=ax[0,0], data=pxHistory, x='date', y='longMomo90th', color='blue')
    sns.lineplot(ax=ax[0,0], data=pxHistory, x='date', y='longMomo10th', color='green')
    ax[0,0].set_title('longMomo')
    ax[0,0].set_xlabel('date')
    ax[0,0].set_ylabel('longMomo')
    ax[0,0].legend(['longMomo', 'longMomo90th', 'longMomo10th'])

    # plot shortmomo, shortMomo90th, and shortMomo10th
    sns.lineplot(ax=ax[0,1], data=pxHistory, x='date', y='shortMomo', color='red')
    sns.lineplot(ax=ax[0,1], data=pxHistory, x='date', y='shortMomo90th', color='blue')
    sns.lineplot(ax=ax[0,1], data=pxHistory, x='date', y='shortMomo10th', color='green')
    ax[0,1].set_title('shortMomo')
    ax[0,1].set_xlabel('date')
    ax[0,1].set_ylabel('shortMomo')
    ax[0,1].legend(['shortMomo', 'shortMomo90th', 'shortMomo10th'])

    ##########################
    # select where shortmomo90th<shortmomo<shortmomo10th
    pxHistory = pxHistory[(pxHistory['longMomo'] <= pxHistory['longMomo10th']) | (pxHistory['longMomo'] >= pxHistory['longMomo90th'])]
    
    # plot scatter of shortMomo vs fwdReturnsPeriods where 
    _x = 'longMomo'
    sns.scatterplot(ax=ax[0,2], data=pxHistory, x='longMinusShortMomo', y='fwdReturns5')
    sns.scatterplot(ax=ax[0,3], data=pxHistory, x=_x, y='fwdReturns1')
    sns.scatterplot(ax=ax[1,0], data=pxHistory, x=_x, y='fwdReturns3')
    sns.scatterplot(ax=ax[1,1], data=pxHistory, x=_x, y='fwdReturns4')
    sns.scatterplot(ax=ax[1,2], data=pxHistory, x=_x, y='fwdReturns5')
    sns.scatterplot(ax=ax[1,3], data=pxHistory, x=_x, y='fwdReturns6')

    # plot regplot of shortMomo vs fwdReturnsPeriods
    sns.regplot(ax=ax[0,2], data=pxHistory, x='longMinusShortMomo', y='fwdReturns5', scatter=False)
    sns.regplot(ax=ax[0,3], data=pxHistory, x=_x, y='fwdReturns1', scatter=False)
    sns.regplot(ax=ax[1,0], data=pxHistory, x=_x, y='fwdReturns3', scatter=False)
    sns.regplot(ax=ax[1,1], data=pxHistory, x=_x, y='fwdReturns4', scatter=False)
    sns.regplot(ax=ax[1,2], data=pxHistory, x=_x, y='fwdReturns5', scatter=False)
    sns.regplot(ax=ax[1,3], data=pxHistory, x=_x, y='fwdReturns6', scatter=False)

    # calculate rsquared for each regplot
    rsquared1 = smf.ols(formula='fwdReturns1 ~ longMinusShortMomo', data=pxHistory).fit()
    rsquared2 = smf.ols(formula='fwdReturns1 ~ %s'%(pxHistory[_x].name), data=pxHistory[[_x, 'fwdReturns1']]).fit()
    rsquared3 = smf.ols(formula='fwdReturns3 ~ %s'%(pxHistory[_x].name), data=pxHistory[[_x, 'fwdReturns3']]).fit()
    rsquared4 = smf.ols(formula='fwdReturns4 ~ %s'%(pxHistory[_x].name), data=pxHistory[[_x, 'fwdReturns4']]).fit()
    rsquared5 = smf.ols(formula='fwdReturns5 ~ %s'%(pxHistory[_x].name), data=pxHistory[[_x, 'fwdReturns5']]).fit()
    rsquared6 = smf.ols(formula='fwdReturns6 ~ %s'%(pxHistory[_x].name), data=pxHistory[[_x, 'fwdReturns6']]).fit()

    # set titles
    ax[0,2].set_title('fwdReturns%s vs longMinusShortMomo(r2=%s)'%(forwardReturnsPeriods[0], round(rsquared1.rsquared, 5)))
    ax[0,3].set_title('fwdReturns%s vs %s(r2=%s)'%(forwardReturnsPeriods[0], pxHistory[_x].name, round(rsquared2.rsquared, 5)))
    ax[1,0].set_title('fwdReturns%s vs %s(r2=%s)'%(forwardReturnsPeriods[2], pxHistory[_x].name, round(rsquared3.rsquared, 5)))
    ax[1,1].set_title('fwdReturns%s vs %s(r2=%s)'%(forwardReturnsPeriods[3], pxHistory[_x].name, round(rsquared4.rsquared, 5)))
    ax[1,2].set_title('fwdReturns%s vs %s(r2=%s)'%(forwardReturnsPeriods[4], pxHistory[_x].name, round(rsquared5.rsquared, 5)))
    ax[1,3].set_title('fwdReturns%s vs %s(r2=%s)'%(forwardReturnsPeriods[5], pxHistory[_x].name, round(rsquared6.rsquared, 5)))


    return fig

"""
    plots distribution of momo for each momoPeeriod
"""
def plotMomoDist(pxHistory, momPeriod=[3,6,12,24,48,96], percentiles = [.01, .05, .5, .95, .99], **kwargs):
    _bins = kwargs.get('bins', 100) # number of bins for the histogram

    if len(momPeriod) > 10: # max of 10 periods
        momPeriod = momPeriod[:10]
    momPeriod.sort()
    
    # calc momo for each momPeriod
    for period in momPeriod:
        pxHistory = momentum.calcMomoFactor(pxHistory, lag=period)
        pxHistory.rename(columns={'momo': 'momo%s'%(period)}, inplace=True)
        pxHistory.rename(columns={'lagmomo': 'lagmomo%s'%(period)}, inplace=True)
    
    # dynamically set the size of the plot 
    numRows = 2
    numPeriods = max(1, len(momPeriod))
    numCols = max(2, int(numPeriods/numRows))

    # plot distribution of momo for each momoPeriod
    sns.set_theme(style="darkgrid")
    fig, ax = plt.subplots(numRows, numCols, figsize=(20, 10))
    sns.set()
    
    i = 0
    for rowNum in range(numRows): 
        for colNum in range(numCols) :
            if i >= numPeriods:
                break
            # add histogram of momo
            sns.histplot(ax=ax[rowNum, colNum], x=pxHistory['momo%s'%(momPeriod[i])], bins=_bins) 
            ax[rowNum, i%numCols].set_title('momo%s'%(momPeriod[i]))
            # add vertical lines at percentiles
            for percentile in percentiles:
                ax[rowNum, colNum].axvline(pxHistory['momo%s'%(momPeriod[i])].quantile(percentile), color='red')
                # draw the value on the plot 
                ax[rowNum, colNum].text(pxHistory['momo%s'%(momPeriod[i])].quantile(percentile), 0, round(pxHistory['momo%s'%(momPeriod[i])].quantile(percentile), 4), rotation=45, color='red', verticalalignment='bottom')
                # add text to top of plot
                #ax[rowNum, colNum].text(pxHistory['momo%s'%(momPeriod[i])].quantile(percentile), 1, str(percentile), rotation=45, color='red', verticalalignment='top')
            # set title
            ax[rowNum, colNum].set_title('momo%s'%(momPeriod[i]))

            # add axis 0 lines 
            ax[rowNum, colNum].axhline(0, color='black')
            ax[rowNum, colNum].axvline(0, color='black')
            i +=1

    return fig


"""
    returns figure 
        plots momo vs. returns scatter across two different pxhisories 
        inputs: 
            targetPxHistory: pxhistory that returns will be computed on 
            signalPxHistory: pxhistory that momo will be computed on
            momoPeriod: period to compute momo on
            forwardReturnsPeriod: array of periods to shift returns by
"""
def plotCrossAssetMomoScatter(targetPxHistory, signalPxHistory, momoPeriod, forwardReturnsPeriods=[1,3,6,12,24,48,96]):
    # compute momo, longMomo, and long-short for signalPxHistory
    signalPxHistory = momentum.calcMomoFactor(signalPxHistory, lag=momoPeriod)
    signalPxHistory.rename(columns={'momo': 'shortMomo'}, inplace=True)
    longMomo = momoPeriod * 2
    signalPxHistory = momentum.calcMomoFactor(signalPxHistory, lag=longMomo)
    signalPxHistory.rename(columns={'momo': 'longMomo'}, inplace=True)
    signalPxHistory['longMinusShortMomo'] = signalPxHistory['longMomo'] - signalPxHistory['shortMomo']

    # compute forward returns for targetPxHistory
    n=1
    for period in forwardReturnsPeriods:
        targetPxHistory['fwdReturns%s'%(n)] = targetPxHistory['close'].pct_change(period).shift(-period)
        n+=1
    
    # make sure targetPxHistory only has dates that are in signalPxHistory
    targetPxHistory = targetPxHistory[targetPxHistory['date'].isin(signalPxHistory['date'])]

    # merge signalPxHistory['momo'] into targetPxHistory on date
    targetPxHistory = targetPxHistory.merge(signalPxHistory[['date', 'shortMomo', 'longMinusShortMomo']], on='date', how='left')

    # plot momo vs. fwdReturns for each fwdReturnsPeriod
    sns.set_theme(style="darkgrid")
    fig, ax = plt.subplots(2,7, figsize=(20, 10))

    # plot momo vs. fwdReturns for each fwdReturnsPeriod
    sns.scatterplot(ax=ax[0,0], data=targetPxHistory, x='shortMomo', y='fwdReturns1')
    sns.scatterplot(ax=ax[0,1], data=targetPxHistory, x='shortMomo', y='fwdReturns2')
    sns.scatterplot(ax=ax[0,2], data=targetPxHistory, x='shortMomo', y='fwdReturns3')
    sns.scatterplot(ax=ax[0,3], data=targetPxHistory, x='shortMomo', y='fwdReturns4')
    sns.scatterplot(ax=ax[0,4], data=targetPxHistory, x='shortMomo', y='fwdReturns5')
    sns.scatterplot(ax=ax[0,5], data=targetPxHistory, x='shortMomo', y='fwdReturns6')
    sns.scatterplot(ax=ax[0,6], data=targetPxHistory, x='shortMomo', y='fwdReturns7')
    # plot longMinusSHortMomo vs. fwdReturns for each fwdReturnsPeriod
    sns.scatterplot(ax=ax[1,0], data=targetPxHistory, x='longMinusShortMomo', y='fwdReturns1')
    sns.scatterplot(ax=ax[1,1], data=targetPxHistory, x='longMinusShortMomo', y='fwdReturns2')
    sns.scatterplot(ax=ax[1,2], data=targetPxHistory, x='longMinusShortMomo', y='fwdReturns3')
    sns.scatterplot(ax=ax[1,3], data=targetPxHistory, x='longMinusShortMomo', y='fwdReturns4')
    sns.scatterplot(ax=ax[1,4], data=targetPxHistory, x='longMinusShortMomo', y='fwdReturns5')
    sns.scatterplot(ax=ax[1,5], data=targetPxHistory, x='longMinusShortMomo', y='fwdReturns6')
    sns.scatterplot(ax=ax[1,6], data=targetPxHistory, x='longMinusShortMomo', y='fwdReturns7')

    # plot regplot of momo vs. fwdReturns for each fwdReturnsPeriod 
    sns.regplot(ax=ax[0,0], data=targetPxHistory, x='shortMomo', y='fwdReturns1', scatter=False)
    sns.regplot(ax=ax[0,1], data=targetPxHistory, x='shortMomo', y='fwdReturns2', scatter=False)
    sns.regplot(ax=ax[0,2], data=targetPxHistory, x='shortMomo', y='fwdReturns3', scatter=False)
    sns.regplot(ax=ax[0,3], data=targetPxHistory, x='shortMomo', y='fwdReturns4', scatter=False)
    sns.regplot(ax=ax[0,4], data=targetPxHistory, x='shortMomo', y='fwdReturns5', scatter=False)
    sns.regplot(ax=ax[0,5], data=targetPxHistory, x='shortMomo', y='fwdReturns6', scatter=False)
    sns.regplot(ax=ax[0,6], data=targetPxHistory, x='shortMomo', y='fwdReturns7', scatter=False)
    # plot regplot of longMinusShortMomo vs. fwdReturns for each fwdReturnsPeriod
    sns.regplot(ax=ax[1,0], data=targetPxHistory, x='longMinusShortMomo', y='fwdReturns1', scatter=False)
    sns.regplot(ax=ax[1,1], data=targetPxHistory, x='longMinusShortMomo', y='fwdReturns2', scatter=False)
    sns.regplot(ax=ax[1,2], data=targetPxHistory, x='longMinusShortMomo', y='fwdReturns3', scatter=False)
    sns.regplot(ax=ax[1,3], data=targetPxHistory, x='longMinusShortMomo', y='fwdReturns4', scatter=False)
    sns.regplot(ax=ax[1,4], data=targetPxHistory, x='longMinusShortMomo', y='fwdReturns5', scatter=False)
    sns.regplot(ax=ax[1,5], data=targetPxHistory, x='longMinusShortMomo', y='fwdReturns6', scatter=False)
    sns.regplot(ax=ax[1,6], data=targetPxHistory, x='longMinusShortMomo', y='fwdReturns7', scatter=False)


    # calculate rsquared for each regplot
    rsquared1 = smf.ols(formula='fwdReturns1 ~ shortMomo', data=targetPxHistory[['shortMomo', 'fwdReturns1']]).fit()
    rsquared2 = smf.ols(formula='fwdReturns2 ~ shortMomo', data=targetPxHistory[['shortMomo', 'fwdReturns2']]).fit()
    rsquared3 = smf.ols(formula='fwdReturns3 ~ shortMomo', data=targetPxHistory[['shortMomo', 'fwdReturns3']]).fit()
    rsquared4 = smf.ols(formula='fwdReturns4 ~ shortMomo', data=targetPxHistory[['shortMomo', 'fwdReturns4']]).fit()
    rsquared5 = smf.ols(formula='fwdReturns5 ~ shortMomo', data=targetPxHistory[['shortMomo', 'fwdReturns5']]).fit()
    rsquared6 = smf.ols(formula='fwdReturns6 ~ shortMomo', data=targetPxHistory[['shortMomo', 'fwdReturns6']]).fit()
    rsquared7 = smf.ols(formula='fwdReturns7 ~ shortMomo', data=targetPxHistory[['shortMomo', 'fwdReturns7']]).fit()
    rsquared_longMinusShortMomo1 = smf.ols(formula='fwdReturns1 ~ longMinusShortMomo', data=targetPxHistory[['longMinusShortMomo', 'fwdReturns1']]).fit()
    rsquared_longMinusShortMomo2 = smf.ols(formula='fwdReturns2 ~ longMinusShortMomo', data=targetPxHistory[['longMinusShortMomo', 'fwdReturns2']]).fit()
    rsquared_longMinusShortMomo3 = smf.ols(formula='fwdReturns3 ~ longMinusShortMomo', data=targetPxHistory[['longMinusShortMomo', 'fwdReturns3']]).fit()
    rsquared_longMinusShortMomo4 = smf.ols(formula='fwdReturns4 ~ longMinusShortMomo', data=targetPxHistory[['longMinusShortMomo', 'fwdReturns4']]).fit()
    rsquared_longMinusShortMomo5 = smf.ols(formula='fwdReturns5 ~ longMinusShortMomo', data=targetPxHistory[['longMinusShortMomo', 'fwdReturns5']]).fit()
    rsquared_longMinusShortMomo6 = smf.ols(formula='fwdReturns6 ~ longMinusShortMomo', data=targetPxHistory[['longMinusShortMomo', 'fwdReturns6']]).fit()
    rsquared_longMinusShortMomo7 = smf.ols(formula='fwdReturns7 ~ longMinusShortMomo', data=targetPxHistory[['longMinusShortMomo', 'fwdReturns7']]).fit()


    # set titles
    ax[0,0].set_title('fwdReturns%s vs momo(r2=%s)'%(forwardReturnsPeriods[0], round(rsquared1.rsquared, 5)))
    ax[0,1].set_title('fwdReturns%s vs momo(r2=%s)'%(forwardReturnsPeriods[1], round(rsquared2.rsquared, 5)))
    ax[0,2].set_title('fwdReturns%s vs momo(r2=%s)'%(forwardReturnsPeriods[2], round(rsquared3.rsquared, 5)))
    ax[0,3].set_title('fwdReturns%s vs momo(r2=%s)'%(forwardReturnsPeriods[3], round(rsquared4.rsquared, 5)))
    ax[0,4].set_title('fwdReturns%s vs momo(r2=%s)'%(forwardReturnsPeriods[4], round(rsquared5.rsquared, 5)))
    ax[0,5].set_title('fwdReturns%s vs momo(r2=%s)'%(forwardReturnsPeriods[5], round(rsquared6.rsquared, 5)))
    ax[0,6].set_title('fwdReturns%s vs momo(r2=%s)'%(forwardReturnsPeriods[6], round(rsquared7.rsquared, 5)))
    ax[1,0].set_title('fwdReturns%s vs longMinusShortMomo(r2=%s)'%(forwardReturnsPeriods[0], round(rsquared_longMinusShortMomo1.rsquared, 5)))
    ax[1,1].set_title('fwdReturns%s vs longMinusShortMomo(r2=%s)'%(forwardReturnsPeriods[1], round(rsquared_longMinusShortMomo2.rsquared, 5)))
    ax[1,2].set_title('fwdReturns%s vs longMinusShortMomo(r2=%s)'%(forwardReturnsPeriods[2], round(rsquared_longMinusShortMomo3.rsquared, 5)))
    ax[1,3].set_title('fwdReturns%s vs longMinusShortMomo(r2=%s)'%(forwardReturnsPeriods[3], round(rsquared_longMinusShortMomo4.rsquared, 5)))
    ax[1,4].set_title('fwdReturns%s vs longMinusShortMomo(r2=%s)'%(forwardReturnsPeriods[4], round(rsquared_longMinusShortMomo5.rsquared, 5)))
    ax[1,5].set_title('fwdReturns%s vs longMinusShortMomo(r2=%s)'%(forwardReturnsPeriods[5], round(rsquared_longMinusShortMomo6.rsquared, 5)))
    ax[1,6].set_title('fwdReturns%s vs longMinusShortMomo(r2=%s)'%(forwardReturnsPeriods[6], round(rsquared_longMinusShortMomo7.rsquared, 5)))

    return fig

"""
    plots simple mom and pxhistory on diff plots
    input: pxhistory, longMomo, shortMomo
"""
def plotMomoandpx(pxHistory, momoPeriod1, momoPeriod2, momoPercentile=0.1, percentilePeriod=252):
    # set short and long momo
    if momoPeriod1 > momoPeriod2:
        longMomo = momoPeriod1
        shortMomo = momoPeriod2
    else:
        longMomo = momoPeriod2
        shortMomo = momoPeriod1
    
    # get momos 
    pxHistory = momentum.calcMomoFactor(pxHistory, lag=shortMomo)
    pxHistory.rename(columns={'momo': 'shortMomo', 'lagmomo': 'lagShortMomo'}, inplace=True)
    pxHistory = momentum.calcMomoFactor(pxHistory, lag=longMomo)
    pxHistory.rename(columns={'momo': 'longMomo', 'lagmomo': 'lagLongMomo'}, inplace=True)

    # add bottom and top percentile for both momos
    pxHistory['longMomoTopPercentile'] = pxHistory['longMomo'].rolling(percentilePeriod).quantile(1-momoPercentile)
    pxHistory['longMomoBottomPercentile'] = pxHistory['longMomo'].rolling(percentilePeriod).quantile(momoPercentile)
    pxHistory['shortMomoTopPercentile'] = pxHistory['shortMomo'].rolling(percentilePeriod).quantile(1-momoPercentile)
    pxHistory['shortMomoBottomPercentile'] = pxHistory['shortMomo'].rolling(percentilePeriod).quantile(momoPercentile)

    # create figure with 2 rows and 3 columns
    sns.set_theme(style="darkgrid")
    fig, ax = plt.subplots(2,3, figsize=(20, 10), sharex=True)
    sns.set()

    # plot longMomo, longMomoTopPercentile, and longMomoBottomPercentile
    sns.lineplot(ax=ax[0,0], data=pxHistory, x='date', y='longMomo', color='red')
    sns.lineplot(ax=ax[0,0], data=pxHistory, x='date', y='longMomoTopPercentile', color='blue')
    sns.lineplot(ax=ax[0,0], data=pxHistory, x='date', y='longMomoBottomPercentile', color='green')
    ax[0,0].set_title('longMomo')
    ax[0,0].set_xlabel('date')
    ax[0,0].set_ylabel('longMomo')

    # plot shortMomo, shortMomoTopPercentile, and shortMomoBottomPercentile
    sns.lineplot(ax=ax[0,1], data=pxHistory, x='date', y='shortMomo', color='red')
    sns.lineplot(ax=ax[0,1], data=pxHistory, x='date', y='shortMomoTopPercentile', color='blue')
    sns.lineplot(ax=ax[0,1], data=pxHistory, x='date', y='shortMomoBottomPercentile', color='green')
    ax[0,1].set_title('shortMomo')
    ax[0,1].set_xlabel('date')  
    ax[0,1].set_ylabel('shortMomo')

    # plot close 
    sns.lineplot(ax=ax[0,2], data=pxHistory, x='date', y='close', color='red')
    ax[0,2].set_title('close')
    ax[0,2].set_xlabel('date')
    ax[0,2].set_ylabel('close')

    return fig

""" 
    plots specified momoPeriods, fwdReturnPeriod scatter 
    input: pxhistory
            momoAndFwdreturnsPeriods [df] w/ columns: momoPeriod, fwdReturnPeriod
"""
def plotMomoAndFwdReturns(pxHistory, momoAndFwdReturnsPeriods):

    # create figure with 2 rows and 3 columns
    fig, ax = plt.subplots(2,5, figsize=(20, 10), sharex=True, sharey=True)
    # set figure title
    fig.suptitle('Momo vs Fwd Returns with Top r2')
    # get momo for each unique momoperiod in momoAndFwdReturnsPeriods
    for period in momoAndFwdReturnsPeriods['momoPeriod'].unique():
        # skip if momo already in pxHistory
        if 'momo%s'%(period) not in pxHistory.columns:
            pxHistory = momentum.calcMomoFactor(pxHistory, lag=period)
            pxHistory.rename(columns={'momo': 'momo%s'%(period)}, inplace=True)
    
    # get forward returns for each unique fwdReturnPeriod in momoAndFwdReturnsPeriods
    for period in momoAndFwdReturnsPeriods['fwdReturnPeriod'].unique():
        pxHistory['fwdReturns%s'%(period)] = pxHistory['close'].pct_change(period).shift(-period)

    # plot momo vs. fwdReturns for each momoAndFwdReturnsPeriods
    for i in range(0, len(momoAndFwdReturnsPeriods)):
        sns.scatterplot(ax=ax[int(i/5), i%5], data=pxHistory, x='momo%s'%(momoAndFwdReturnsPeriods['momoPeriod'][i]), y='fwdReturns%s'%(momoAndFwdReturnsPeriods['fwdReturnPeriod'][i]))
        ax[int(i/5), i%5].set_title('momo%s vs fwdReturns%s'%(momoAndFwdReturnsPeriods['momoPeriod'][i], momoAndFwdReturnsPeriods['fwdReturnPeriod'][i]))
        ax[int(i/5), i%5].set_xlabel('momo%s'%(momoAndFwdReturnsPeriods['momoPeriod'][i]))
        ax[int(i/5), i%5].set_ylabel('fwdReturns%s'%(momoAndFwdReturnsPeriods['fwdReturnPeriod'][i]))

        # add title
        ax[int(i/5), i%5].set_title('momo%s vs fwdReturns%s; %s'%(momoAndFwdReturnsPeriods['momoPeriod'][i], momoAndFwdReturnsPeriods['fwdReturnPeriod'][i], momoAndFwdReturnsPeriods['correl'][i]))

        # plot regplot of momo vs. fwdReturns for each fwdReturnsPeriod
        sns.regplot(ax=ax[int(i/5), i%5], data=pxHistory, x='momo%s'%(momoAndFwdReturnsPeriods['momoPeriod'][i]), y='fwdReturns%s'%(momoAndFwdReturnsPeriods['fwdReturnPeriod'][i]), scatter=False)

        # add axis lines at 0
        ax[int(i/5), i%5].axhline(0, color='grey', alpha=0.5)
        ax[int(i/5), i%5].axvline(0, color='grey', alpha=0.5)

    return fig

""" 
    plots scatters filtered by percentilles 
"""
def plotMomoandPx_filteredByPercentile(pxHistory, momoAndFwdReturnsPeriods, momoPercentileTop=0.99, momoPercentileBottom=0.01):
    # create figure with 2 rows and 3 columns
    sns.set_theme(style="darkgrid")
    fig, ax = plt.subplots(2,5, figsize=(20, 10), sharex=True, sharey=True)
    sns.set()
    # set figure title
    fig.suptitle('Momo vs Fwd Returns with Top r2 filtered by momoPercentile')
    
    # get momo for each unique momoperiod in momoAndFwdReturnsPeriods
    for period in momoAndFwdReturnsPeriods['momoPeriod'].unique():
        # skip if momo already in pxHistory
        if 'momo%s'%(period) not in pxHistory.columns:
            pxHistory = momentum.calcMomoFactor(pxHistory, lag=period)
            pxHistory.rename(columns={'momo': 'momo%s'%(period)}, inplace=True)
    
    # get forward returns for each unique fwdReturnPeriod in momoAndFwdReturnsPeriods
    for period in momoAndFwdReturnsPeriods['fwdReturnPeriod'].unique():
        pxHistory['fwdReturns%s'%(period)] = pxHistory['close'].pct_change(period).shift(-period)

    # plot momo vs. fwdReturns for each momoAndFwdReturnsPeriods
    for i in range(0, len(momoAndFwdReturnsPeriods)):
        # set pxHistory filtered to select records where momo is above top percentil, and beloww bottom percentile
        pxHistory_filtered = pxHistory[(pxHistory['momo%s'%(momoAndFwdReturnsPeriods['momoPeriod'][i])] >= pxHistory['momo%s'%(momoAndFwdReturnsPeriods['momoPeriod'][i])].quantile(momoPercentileTop)) | (pxHistory['momo%s'%(momoAndFwdReturnsPeriods['momoPeriod'][i])] <= pxHistory['momo%s'%(momoAndFwdReturnsPeriods['momoPeriod'][i])].quantile(momoPercentileBottom))]

        # plot scatter
        sns.scatterplot(ax=ax[int(i/5), i%5], data=pxHistory_filtered, x='momo%s'%(momoAndFwdReturnsPeriods['momoPeriod'][i]), y='fwdReturns%s'%(momoAndFwdReturnsPeriods['fwdReturnPeriod'][i]))

        # plot regplot 
        sns.regplot(ax=ax[int(i/5), i%5], data=pxHistory_filtered, x='momo%s'%(momoAndFwdReturnsPeriods['momoPeriod'][i]), y='fwdReturns%s'%(momoAndFwdReturnsPeriods['fwdReturnPeriod'][i]), scatter=False)

        # add title
        ax[int(i/5), i%5].set_title('momo%s vs fwdReturns%s; %s'%(momoAndFwdReturnsPeriods['momoPeriod'][i], momoAndFwdReturnsPeriods['fwdReturnPeriod'][i], momoAndFwdReturnsPeriods['correl'][i]))
        
        # add axis lines at 0
        ax[int(i/5), i%5].axhline(0, color='grey', alpha=0.5)
        ax[int(i/5), i%5].axvline(0, color='grey', alpha=0.5)

    return fig

def plotMomoOverview (pxHistory, momoPeriod, emaPeriod):
    fig, ax = plt.subplots(2, 2)
    fig.suptitle('Momo%s Overview'%(momoPeriod))
   
    # plot heatmap 
    mean_fwdReturns = sa.bucketAndCalcSignalReturns(pxHistory, 'momo', 2, 50)
    sns.heatmap(mean_fwdReturns, annot=False, cmap='RdYlGn', ax=ax[0,0])
    ax[0,0].set_title('momo%s vs. fwdreturns'%(momoPeriod))
    
    # plot momo and close 
    sns.lineplot(ax=ax[0,1], data=pxHistory, x='date', y='momo', color='green', alpha=0.5)
    sns.lineplot(ax=ax[0,1].twinx(), data=pxHistory, x='date', y='close', color='grey') 
    ax[0,1].set_title('close and momo%s'%(momoPeriod))
    ax[0,1].grid(True, which='both', axis='both', linestyle='-')
    # add hline at 0
    ax[0,1].axhline(0, color='black', alpha=0.5)
    ax[0,1].legend()


    # plot momo autocorrelation
    autocorrelations = sa.calculateAutocorrelations(pxHistory, 'momo', 100)
    ax[1,0].stem(autocorrelations, use_line_collection=True, linefmt='--')
    ax[1,0].set_title('momo%s autocorrelation'%(momoPeriod))

    # plot momo distribution
    sns.histplot(ax=ax[1,1], data=pxHistory, x='momo', bins=100)
    ax[1,1].axvline(pxHistory['momo'].quantile(.9), color='red', linestyle='--')
    ax[1,1].axvline(pxHistory['momo'].quantile(.1), color='red', linestyle='--') 
    ax[1,1].set_title('momo%s distribution'%(momoPeriod))
    ax[1,1].grid(True, which='both', axis='both', linestyle='-')
    ax[1,1].axvline(pxHistory['momo'].mean(), color='black', alpha=0.2)

    # adjust right hand margins
    plt.subplots_adjust(right=5)

    return fig 
"""
    Simple returns calc using VVIX as signal, and VIX as the target 
        1. long VIX when VVIX ema(5) < ema(10) 
        2. short VIX when VVIX ema(5) > ema(10)
"""
import sys
sys.path.append('..')

import config
import momentum

import statsmodels.api as sm 
import statsmodels.formula.api as smf

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import interface_localDB as db

from utils import utils_tabbedPlotsWindow as tabbedWindow 

###
# set pandas to print all rows 
pd.set_option('display.max_rows', None)
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
def plotMomoDist(pxHistory, momPeriod=[3,6,10,24,48,96]):
    # calc momo for each momPeriod
    n=1
    for period in momPeriod:
        pxHistory = momentum.calcMomoFactor(pxHistory, lag=period)
        pxHistory.rename(columns={'momo': 'momo%s'%(n)}, inplace=True)
        pxHistory.rename(columns={'lagmomo': 'lagmomo%s'%(period)}, inplace=True)
        n+=1 
    
    # set percentiles to draw vertical lines at
    percentiles = [.05, .5, .95, .99]

    # plot distribution of momo for each momoPeriod
    sns.set_theme(style="darkgrid")
    fig, ax = plt.subplots(2,3, figsize=(20, 10))
    sns.set()

    # plot distribution of momo for each momoPeriod
    sns.histplot(ax=ax[0,0], x=pxHistory['momo1'])
    # add vertical lines at percentiles
    for percentile in percentiles:
        ax[0,0].axvline(pxHistory['momo1'].quantile(percentile), color='red')
        # draw the value on the plot 
        ax[0,0].text(pxHistory['momo1'].quantile(percentile), 0, round(pxHistory['momo1'].quantile(percentile), 2), rotation=45, color='red')
    sns.histplot(ax=ax[0,1], x=pxHistory['momo2'])
    # add vertical lines at percentiles
    for percentile in percentiles:
        ax[0,1].axvline(pxHistory['momo2'].quantile(percentile), color='red')
        # draw the value on the plot
        ax[0,1].text(pxHistory['momo2'].quantile(percentile), 0, round(pxHistory['momo2'].quantile(percentile), 2), rotation=45, color='red')
    sns.histplot(ax=ax[0,2], x=pxHistory['momo3'])
    # add vertical lines at percentiles
    for percentile in percentiles:
        ax[0,2].axvline(pxHistory['momo3'].quantile(percentile), color='red')
        # draw the value on the plot
        ax[0,2].text(pxHistory['momo3'].quantile(percentile), 0, round(pxHistory['momo3'].quantile(percentile), 2), rotation=45, color='red')

    sns.histplot(ax=ax[1,0], x=pxHistory['momo4'])
    # add vertical lines at percentiles
    for percentile in percentiles:
        ax[1,0].axvline(pxHistory['momo4'].quantile(percentile), color='red')
        # draw the value on the plot
        ax[1,0].text(pxHistory['momo4'].quantile(percentile), 0, round(pxHistory['momo4'].quantile(percentile), 2), rotation=45, color='red')
    
    sns.histplot(ax=ax[1,1], x=pxHistory['momo5'])
    # add vertical lines at percentiles
    for percentile in percentiles:
        ax[1,1].axvline(pxHistory['momo5'].quantile(percentile), color='red')
        # draw the value on the plot
        ax[1,1].text(pxHistory['momo5'].quantile(percentile), 0, round(pxHistory['momo5'].quantile(percentile), 2), rotation=45, color='red')
    
    sns.histplot(ax=ax[1,2], x=pxHistory['momo6'])
    # add vertical lines at percentiles
    for percentile in percentiles:
        ax[1,2].axvline(pxHistory['momo6'].quantile(percentile), color='red')
        # draw the value on the plot
        ax[1,2].text(pxHistory['momo6'].quantile(percentile), 0, round(pxHistory['momo6'].quantile(percentile), 2), rotation=45, color='red')

    # set titles
    ax[0,0].set_title('momo%s'%(momPeriod[0]))
    ax[0,1].set_title('momo%s'%(momPeriod[1]))
    ax[0,2].set_title('momo%s'%(momPeriod[2]))
    ax[1,0].set_title('momo%s'%(momPeriod[3]))
    ax[1,1].set_title('momo%s'%(momPeriod[4]))
    ax[1,2].set_title('momo%s'%(momPeriod[5]))

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

    # set figure title 
    fig.suptitle('shortmomo-%s, longmomo-%s vs. fwdReturns%s'%(momoPeriod, longMomo, forwardReturnsPeriods))

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


    ###


    return fig


    print(targetPxHistory.head(30))

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
    This functions returns a figure with scatters of momo percentile vs. fwd returns for each fwdReturnsPeriod and a given momo period 
"""
def plotMomoPercentileScatter(pxHistory, momoPeriod, forwardReturnsPeriods=[1,3,6,12,24,48,96]):
    # calc momo for each momoPeriod
    pxHistory = momentum.calcMomoFactor(pxHistory, lag=momoPeriod)

    # add column 'momoPercentile' to pxHistory
    pxHistory['momoPercentile'] = pxHistory['momo'].rank(pct=True)

    # add forward returns for each fwdReturnsPeriod
    n=1
    for period in forwardReturnsPeriods:
        pxHistory['fwdReturns%s'%(period)] = pxHistory['close'].pct_change(period).shift(-period)
        n+=1

    # select only the records with momoPercentile > 0.9
    pxHistory = pxHistory[pxHistory['momoPercentile'] > 0.95]

    # create 2x4 grid 
    sns.set_theme(style="darkgrid")
    fig, ax = plt.subplots(2,4, figsize=(20, 10), sharex=True, sharey=True)

    # set figure title 
    fig.suptitle('momoPeriod%s vs. Fwd Returns'%(momoPeriod))
    sns.set()

    # plot momoPercentile vs. fwdReturns for each fwdReturnsPeriod
    sns.scatterplot(ax=ax[0,0], data=pxHistory, x='momoPercentile', y='fwdReturns%s'%(forwardReturnsPeriods[0]))
    sns.scatterplot(ax=ax[0,1], data=pxHistory, x='momoPercentile', y='fwdReturns%s'%(forwardReturnsPeriods[1]))
    sns.scatterplot(ax=ax[0,2], data=pxHistory, x='momoPercentile', y='fwdReturns%s'%(forwardReturnsPeriods[2]))
    sns.scatterplot(ax=ax[0,3], data=pxHistory, x='momoPercentile', y='fwdReturns%s'%(forwardReturnsPeriods[3]))
    sns.scatterplot(ax=ax[1,0], data=pxHistory, x='momoPercentile', y='fwdReturns%s'%(forwardReturnsPeriods[4]))
    sns.scatterplot(ax=ax[1,1], data=pxHistory, x='momoPercentile', y='fwdReturns%s'%(forwardReturnsPeriods[5]))
    sns.scatterplot(ax=ax[1,2], data=pxHistory, x='momoPercentile', y='fwdReturns%s'%(forwardReturnsPeriods[6]))

    # plot regplot of momoPercentile vs. fwdReturns for each fwdReturnsPeriod
    sns.regplot(ax=ax[0,0], data=pxHistory, x='momoPercentile', y='fwdReturns%s'%(forwardReturnsPeriods[0]), scatter=False)
    sns.regplot(ax=ax[0,1], data=pxHistory, x='momoPercentile', y='fwdReturns%s'%(forwardReturnsPeriods[1]), scatter=False)
    sns.regplot(ax=ax[0,2], data=pxHistory, x='momoPercentile', y='fwdReturns%s'%(forwardReturnsPeriods[2]), scatter=False)
    sns.regplot(ax=ax[0,3], data=pxHistory, x='momoPercentile', y='fwdReturns%s'%(forwardReturnsPeriods[3]), scatter=False)
    sns.regplot(ax=ax[1,0], data=pxHistory, x='momoPercentile', y='fwdReturns%s'%(forwardReturnsPeriods[4]), scatter=False)
    sns.regplot(ax=ax[1,1], data=pxHistory, x='momoPercentile', y='fwdReturns%s'%(forwardReturnsPeriods[5]), scatter=False)
    sns.regplot(ax=ax[1,2], data=pxHistory, x='momoPercentile', y='fwdReturns%s'%(forwardReturnsPeriods[6]), scatter=False)

    # calculate rsquared for each regplot
    rsquared1 = smf.ols(formula='fwdReturns%s ~ momoPercentile'%(forwardReturnsPeriods[0]), data=pxHistory[['momoPercentile', 'fwdReturns%s'%(forwardReturnsPeriods[0])]]).fit()
    rsquared2 = smf.ols(formula='fwdReturns%s ~ momoPercentile'%(forwardReturnsPeriods[1]), data=pxHistory[['momoPercentile', 'fwdReturns%s'%(forwardReturnsPeriods[1])]]).fit()
    rsquared3 = smf.ols(formula='fwdReturns%s ~ momoPercentile'%(forwardReturnsPeriods[2]), data=pxHistory[['momoPercentile', 'fwdReturns%s'%(forwardReturnsPeriods[2])]]).fit()
    rsquared4 = smf.ols(formula='fwdReturns%s ~ momoPercentile'%(forwardReturnsPeriods[3]), data=pxHistory[['momoPercentile', 'fwdReturns%s'%(forwardReturnsPeriods[3])]]).fit()
    rsquared5 = smf.ols(formula='fwdReturns%s ~ momoPercentile'%(forwardReturnsPeriods[4]), data=pxHistory[['momoPercentile', 'fwdReturns%s'%(forwardReturnsPeriods[4])]]).fit()
    rsquared6 = smf.ols(formula='fwdReturns%s ~ momoPercentile'%(forwardReturnsPeriods[5]), data=pxHistory[['momoPercentile', 'fwdReturns%s'%(forwardReturnsPeriods[5])]]).fit()
    rsquared7 = smf.ols(formula='fwdReturns%s ~ momoPercentile'%(forwardReturnsPeriods[6]), data=pxHistory[['momoPercentile', 'fwdReturns%s'%(forwardReturnsPeriods[6])]]).fit()

    # set titles
    ax[0,0].set_title('fwdReturns%s vs momoPercentile(r2=%s)'%(forwardReturnsPeriods[0], round(rsquared1.rsquared, 5)))
    ax[0,1].set_title('fwdReturns%s vs momoPercentile(r2=%s)'%(forwardReturnsPeriods[1], round(rsquared2.rsquared, 5)))
    ax[0,2].set_title('fwdReturns%s vs momoPercentile(r2=%s)'%(forwardReturnsPeriods[2], round(rsquared3.rsquared, 5)))
    ax[0,3].set_title('fwdReturns%s vs momoPercentile(r2=%s)'%(forwardReturnsPeriods[3], round(rsquared4.rsquared, 5)))
    ax[1,0].set_title('fwdReturns%s vs momoPercentile(r2=%s)'%(forwardReturnsPeriods[4], round(rsquared5.rsquared, 5)))
    ax[1,1].set_title('fwdReturns%s vs momoPercentile(r2=%s)'%(forwardReturnsPeriods[5], round(rsquared6.rsquared, 5)))
    ax[1,2].set_title('fwdReturns%s vs momoPercentile(r2=%s)'%(forwardReturnsPeriods[6], round(rsquared7.rsquared, 5)))

    return fig

############################################
### re-enable this secton to run script from console 
############################################

# load vvix and vix bars
"""with db.sqlite_connection(config.dbname_stock) as conn:
    vvix = db.getPriceHistory(conn, 'VVIX', '1day')
    vvix_30mins = db.getPriceHistory(conn, 'VVIX', '30mins')
    vvix_5mins = db.getPriceHistory(conn, 'VVIX', '5mins')

    vix = db.getPriceHistory(conn, 'VIX', '1day')
    vix_5mins = db.getPriceHistory(conn, 'VIX', '5mins')
    vix_5mins_r = vix_5mins[(vix_5mins['date'].dt.time >= pd.to_datetime('09:30:00').time()) & (vix_5mins['date'].dt.time <= pd.to_datetime('16:15:00').time())]
    vix_30mins = db.getPriceHistory(conn, 'VIX', '30mins')"""


#tpw = tabbedWindow.plotWindow()
# resize to full screen
#

############################################

#### VIX 
# VANILLA SCATTERS
#tpw.addPlot('VIX_1d momoScatter(15,30)', plotMomoScatter(vix, 15, 30,[5,15,20,25,30,35,40]))
#tpw.addPlot('VIX_30m(12,48)', plotMomoScatter(vix_30mins, 12, 48, [5,15,20,25,30,35,40]))
#tpw.addPlot('VIX-5m(10, 48)', plotMomoScatter(vix_5mins, 10, 48))
#tpw.addPlot('VIX_5m-r(12, 48)', plotMomoScatter(vix_5mins_r, 12, 48))

# VIX vs VVIX SCATTERS 
#tpw.addPlot('VIX vs. VVIXmomo(30m)', plotCrossAssetMomoScatter(vix_5mins, vvix_5mins, 30, [1,3,5,10,12,20,30]))
#tpw.addPlot('VIX vs. VVIXmomo(15)', plotCrossAssetMomoScatter(vix, vvix, 15, [5,15,20,25,30,35,40]))

# MOMO PERCENTILE SCATTERS
#tpw.addPlot('VVIX-5m, momo30 percentile scatter', plotMomoPercentileScatter(vvix_5mins, 30))

# CROSSOVERS
#tpw.addPlot('VIX_1d xOver(15,30)', plotMomoCrossoverSignal(vix, 15, 30))
#tpw.addPlot('VIX_5min(15,30)', plotMomoCrossoverSignal(vix_5mins, 15, 30))

# DISTRIBUTIONS 
#tpw.addPlot('VIX momo distribution', plotMomoDist(vix_5mins))
#tpw.addPlot('VIX_30m momo dist', plotMomoDist(vix_30mins))

# MISC. 
#tpw.addPlot('VIX_5m momoAndpx', plotMomoandpx(vix_5mins, 12, 48))
#tpw.addPlot('VIX pairplot', plotMomoPairplot(vix_30mins))


#### VVIX 

#tpw.addPlot('VVIX_5m xOver(15,30)', plotMomoCrossoverSignal(vvix_5mins, 15, 30))

#tpw.addPlot('VVIX_1d(12,48)', plotMomoScatter(vvix, 12, 48))
#tpw.addPlot('VVIX_5m(12, 48)', plotMomoScatter(vvix_5mins, 12, 48))

#tpw.addPlot('VVIX_30m momo dist', plotMomoDist(vvix_30mins))
#tpw.addPlot('VVIX_5m dist', plotMomoDist(vvix_5mins))


#tpw.addPlot('KOLD momo 12 48', plotMomoScatter(kold_5mins, 12, 48))

#tpw.show()

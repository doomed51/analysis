import sys
sys.path.append('..')

## local libs
import interface_localDB as db

from utils import utils as ut
from utils import utils_termStructure as vixts
from utils import utils_tabbedPlotsWindow as pltWindow
import vol_momentum as volMomo

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go

import config
import seasonality
import momentum
import math

### CONFIGS ### 
db_stock = config.dbname_stock
db_termstructure = config.dbname_termstructure

#####################################################
################# PLOT FUNCTIONS ####################
#####################################################

""" plot the relationships between vix term structure and vix price history
 arguments:
  vix_ts_pctContango: the vix term structure data
  vix: the vix price history data
 generate a 1x3 figure with the following subplots:
  1. scatter of fourToSevenMoContango vs. VIX close_pctChange
  2. scatter of avgContango vs. VIX close_pctChange
  3. scatter of vvix percentileRank vs. VIX close_pctChange
 notes: 
  - vix pct change is shifted by 1 day so the scatters represent the
    relationship with next day's return
"""
def plotVixRelationships(vix_ts_pctContango, vix, vvix):
    fig2, ax2 = plt.subplots(2, 3, figsize=(15, 11))
    fig2.suptitle('Contango & VIX next day returns')
    
    # shift vix by 1 day for next day returns
    vix['pctChange'] = vix['pctChange'].shift(-1)

    # plot fourToSevenMoContango vs. VIX close_pctChange
    sns.scatterplot(x=vix_ts_pctContango['fourToSevenMoContango'], y=vix['pctChange'], ax=ax2[0,0])
    sns.regplot(x=vix_ts_pctContango['fourToSevenMoContango'], y=vix['pctChange'], ax=ax2[0,0], line_kws={'color': 'red'})
    ax2[0,0].set_title('4-7 Mo Contango')

    # plot avgContango vs. VIX close_pctChange
    sns.scatterplot(x=vix_ts_pctContango['averageContango'], y=vix['pctChange'], ax=ax2[0,1])
    sns.regplot(x=vix_ts_pctContango['averageContango'], y=vix['pctChange'], ax=ax2[0,1], line_kws={'color': 'red'})
    ax2[0,1].set_title('Avg Contango')

    # plot currentToLastMoContango vs. VIX close_pctChange
    sns.scatterplot(x=vix_ts_pctContango['currentToLastContango'], y=vix['pctChange'], ax=ax2[0,2])
    sns.regplot(x=vix_ts_pctContango['currentToLastContango'], y=vix['pctChange'], ax=ax2[0,2], line_kws={'color': 'red'})
    ax2[0,2].set_title('Current to Last Mo Contango')
    
    # plot vvix percentileRank vs. VIX close_pctChange
    sns.scatterplot(x=vvix['percentileRank'], y=vix['pctChange'], ax=ax2[1,0])
    sns.regplot(x=vvix['percentileRank'], y=vix['pctChange'], ax=ax2[1,0], line_kws={'color': 'red'})
    ax2[1,0].set_title('VVIX Percentile Rank')
    # reverse x axis
    ax2[1,0].invert_xaxis()

    # plot vvix percentileRank_30d vs. VIX close_pctChange
    sns.scatterplot(x=vvix['percentileRank_60d'], y=vix['pctChange'], ax=ax2[1,1])
    sns.regplot(x=vvix['percentileRank_60d'], y=vix['pctChange'], ax=ax2[1,1], line_kws={'color': 'red'})
    ax2[1,1].set_title('VVIX Percentile Rank 60d')
    # reverse x axis
    ax2[1,1].invert_xaxis()

    # plot vvix percentileRank_90d vs. VIX close_pctChange
    sns.scatterplot(x=vvix['percentileRank_90d'], y=vix['pctChange'], ax=ax2[1,2])
    sns.regplot(x=vvix['percentileRank_90d'], y=vix['pctChange'], ax=ax2[1,2], line_kws={'color': 'red'})
    ax2[1,2].set_title('VVIX Percentile Rank 90d')
    # reverse x axis
    ax2[1,2].invert_xaxis()

    return fig2

"""
view for day to day monitoring of VIX term structure changes. The following are displayed:
    - VIX: 4-7 month contango, and percentile rank of vvix
    - VIX: close 
    - VIX close pct change vs. vvix percentile rank scatter
"""
def plotVixTermStructureMonitor(vix_ts_pctContango, vix, vvix, contangoColName = 'fourToSevenMoContango'):
    sns.set_style('darkgrid')
    # using seaborn, create figure with 2 subplots
    fig, ax = plt.subplots(2, 2, figsize=(15, 10))
    # set title
    fig.suptitle('VIX Term Structure')
    contangoPercentile90 = vix_ts_pctContango[contangoColName].quantile(0.9)
    contangoPercentile10 = vix_ts_pctContango[contangoColName].quantile(0.1)
    ###############################
    # plot fourtosevenMoContango and vvix
    ax2=ax[0,0].twinx()
    sns.lineplot(x='date', y=contangoColName, data=vix_ts_pctContango, ax=ax[0,0], color='blue', label=contangoColName, alpha=0.5)
    sns.lineplot(x='date', y='fourToSevenMoContango', data=vix_ts_pctContango, ax=ax[0,0], color='green', label='fourToSevenMoContango')
    sns.lineplot(x=vvix['date'], y='close', data=vvix, ax=ax2, color='red', alpha=0.3, label='VVIX')

    # Format plot
    ax2.set_yscale('log')
    ax[0,0].set_title('%s & VVIX'%(contangoColName)) 
    ax[0,0].axhline(y=0, color='black', linestyle='-')
    ax[0,0].axhline(y=contangoPercentile90, color='grey', linestyle='--', alpha=0.5)
    ax[0,0].axhline(y=contangoPercentile10, color='grey', linestyle='--', alpha=0.5)
    ax[0,0].lines[1].set_alpha(0.5)

    ###############################
    # plot distribution of 4-7 month contango
    sns.histplot(x=vix_ts_pctContango[contangoColName], ax=ax[0,1], bins=100, kde=True)
    
    # format plot
    ax[0,1].set_title('%s Distribution'%(contangoColName))
    #ax[0,1].set_xlabel('%s (%)'%(contangoColName))
    ax[0,1].set_ylabel('Frequency')
    ax[0,1].axvline(x=0, color='black', linestyle='-')
    ax[0,0].legend(loc='upper left')   
    ax2.legend(loc='upper right')
    ax2.grid(False)
    
    # add percentile vlines to the historgram 
    ax[0,1].axvline(x=vix_ts_pctContango[contangoColName].quantile(0.05), color='grey', linestyle='-', alpha=0.9)
    ax[0,1].axvline(x=vix_ts_pctContango[contangoColName].quantile(0.1), color='grey', linestyle='--', alpha=0.5)
    # add value of percentile as overlay text
    ax[0,1].text(vix_ts_pctContango[contangoColName].quantile(0.05), 0, '%.2f'%(vix_ts_pctContango[contangoColName].quantile(0.05)), color='black', fontsize=10)
    ax[0,1].text(vix_ts_pctContango[contangoColName].quantile(0.1), 0, '%.2f'%(vix_ts_pctContango[contangoColName].quantile(0.1)), color='black', fontsize=10)

    # add top percentile vlines to histogram 
    ax[0,1].axvline(x=vix_ts_pctContango[contangoColName].quantile(0.95), color='grey', linestyle='-', alpha=0.9)
    ax[0,1].axvline(x=vix_ts_pctContango[contangoColName].quantile(0.9), color='grey', linestyle='--', alpha=0.5)
    # add value of percentile as overlay text
    ax[0,1].text(vix_ts_pctContango[contangoColName].quantile(0.95), 0, '%.2f'%(vix_ts_pctContango[contangoColName].quantile(0.95)), color='black', fontsize=10)
    ax[0,1].text(vix_ts_pctContango[contangoColName].quantile(0.9), 0, '%.2f'%(vix_ts_pctContango[contangoColName].quantile(0.9)), color='black', fontsize=10)

    # add lastest value of 4-7 month contango vline
    ax[0,1].axvline(x=vix_ts_pctContango[contangoColName].iloc[-1], color='red', linestyle='-', alpha=0.9)
    ax[0,1].text(vix_ts_pctContango[contangoColName].iloc[-1], 0, 'Today: %.2f'%(vix_ts_pctContango[contangoColName].iloc[-1]), color='red', fontsize=10)

    ###############################        
    # plot contango and vix
    ax2=ax[1,0].twinx()
    sns.lineplot(x='date', y=contangoColName, data=vix_ts_pctContango, ax=ax[1,0], color='blue', label='4-7 Mo Contango')
    sns.lineplot(x='date', y='close', data=vix, ax=ax2, color='red', alpha=0.3, label='VIX')
    
    # format plot 
    ax[1,0].set_title('%s & VIX'%(contangoColName))
    ax[1,0].axhline(y=0, color='black', linestyle='-')
    ax[1,0].axhline(y=contangoPercentile90, color='grey', linestyle='--', alpha=0.5)
    ax[1,0].axhline(y=contangoPercentile10, color='grey', linestyle='--', alpha=0.5)
    ax[1,0].legend(loc='upper left')   
    ax2.legend(loc='upper right')
    ax2.grid(False)
    
    # plot contango vs lagged logreturn 
    vix['lagged'] = vix['logReturn'].shift(-1)
    vix['laggedReturn20'] = vix['logReturn'].shift(-20)
    sns.scatterplot(x=vix_ts_pctContango[contangoColName], y=vix['logReturn'].shift(-1), ax=ax[1,1])
    sns.regplot(x=vix_ts_pctContango[contangoColName], y=vix['logReturn'].shift(-1), ax=ax[1,1], line_kws={'color': 'red'})
    ax[1,1].set_title('%s vs. VIX logReturn'%(contangoColName))
    ax[1,1].axhline(y=0, color='black', linestyle='-')
    ax[1,1].axvline(x=0, color='black', linestyle='-')

    return fig

"""
    Returns figure with plots for contango vs. lagged return
    @ts_pctContango: [pd.DataFrame] vix term structure data
    @pxHistory: [pd.DataFrame] vix price history
    @lagPeriods: [[int]] number of periods to lag the return by
"""
def plotContangoVsLaggedReturn(ts_pctContango, pxHistory, contangoColName = 'fourToSevenMoContango', lagPeriods=[1,2,3,4,5,6,10,20]):
    pxHistory.reset_index(drop=True, inplace=True)
    # set numrows and numcols for the plot
    numrows = 2
    numcols = math.ceil((len(lagPeriods)//numrows))

    # create figure and axes
    fig, ax = plt.subplots(numrows, numcols)

    # calculate pctChange for each logPeriods 
    for i in range(len(lagPeriods)):
        pxHistory.loc[:, 'laggedReturn%s'%(lagPeriods[i])] = pxHistory['logReturn'].shift(-lagPeriods[i])

    # plot contango vs. lagged return for each lagPeriod
    for i in range(len(lagPeriods)):
        rowNum = int(i/numcols)
        colNum = i%numcols
        sns.scatterplot(x=ts_pctContango[contangoColName], y=pxHistory['laggedReturn%s'%(lagPeriods[i])], ax=ax[rowNum,colNum])
        sns.regplot(x=ts_pctContango[contangoColName], y=pxHistory['laggedReturn%s'%(lagPeriods[i])], ax=ax[rowNum,colNum], line_kws={'color': 'red'})
        ax[rowNum,colNum].set_title('%s vs. %s fwd return %s'%(contangoColName, pxHistory['symbol'][0], lagPeriods[i]))
        ax[rowNum,colNum].axhline(y=0, color='black', linestyle='-')
        ax[rowNum,colNum].axvline(x=0, color='black', linestyle='-')
    
    return fig

"""
plots intra-month, and month over month seasonality of 4-7mo. contango
 arguments:
    - vix_ts_pctContango: dataframe of vix term structure data
 plots the following:
 - mean and sd of 4-7 month contango aggregated by day of month
 - mean and sd of 4-7 month contango aggregated by month
"""
def plotVixTermStructureSeasonality(vix_ts_pctContango, contangoColName='fourToSevenMoContango'):
    # new df that aggregates 4-7 month contango by day of month
    vix_ts_pctContango_day = vix_ts_pctContango.groupby(vix_ts_pctContango['date'].dt.day).agg({'fourToSevenMoContango': ['mean', 'std']})

    # new df that aggregates 4-7 month contango by month
    vix_ts_pctContango_month = vix_ts_pctContango.groupby(vix_ts_pctContango['date'].dt.month).agg({'fourToSevenMoContango': ['mean', 'std']})

    # using seaborn, create figure with 2 subplots
    fig, ax = plt.subplots(2, 1, figsize=(15, 10))

    # set title
    fig.suptitle('VIX Term Structure Seasonality')

    # barplot mean and sd of 4-7 month contango aggregated by day of month
    sns.barplot(x=vix_ts_pctContango_day.index, y=vix_ts_pctContango_day['fourToSevenMoContango']['mean'], ax=ax[0], color='blue')
    #sns.barplot(x=vix_ts_pctContango_day.index, y=vix_ts_pctContango_day['fourToSevenMoContango']['std'], ax=ax[0].twinx(), color='red')
    ax[0].set_title('4th to 7th Month Contango by Day of Month')

    # barplot mean and sd of 4-7 month contango aggregated by month
    sns.barplot(x=vix_ts_pctContango_month.index, y=vix_ts_pctContango_month['fourToSevenMoContango']['std'], ax=ax[1], color='grey', alpha=0.5)
    sns.barplot(x=vix_ts_pctContango_month.index, y=vix_ts_pctContango_month['fourToSevenMoContango']['mean'], ax=ax[1].twinx(), color='red')
    ax[1].set_title('4th to 7th Month Contango by Month')
    # set x-axis labels to month names
    ax[1].set_xticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])

    return fig


""" 
    Plots term structure in one large plot 
"""
def plotHistoricalTermstructure(ts_data, pxHistory_underlying, contangoColName='default'):
    pxHistory_underlying.reset_index(drop=True, inplace=True)
    if contangoColName == 'default':
        # plot lineplots on 1 plot 
        fig, ax = plt.subplots()
        sns.lineplot(x='date', y='oneToTwoMoContango', data=ts_data, ax=ax, label='oneToTwoMoContango', color='blue')
        sns.lineplot(x='date', y='oneToThreeMoContango', data=ts_data, ax=ax, label='oneToThreeMoContango', color='green')
        sns.lineplot(x='date', y='twoToThreeMoContango', data=ts_data, ax=ax, label='twoToThreeMoContango', color='red')
        sns.lineplot(x='date', y='threeToFourMoContango', data=ts_data, ax=ax, label='threeToFourMoContango', color='pink')
        sns.lineplot(x='date', y='fourToSevenMoContango', data=ts_data, ax=ax, label='fourToSevenMoContango', color='green')
        #sns.lineplot(x='date', y='currentToLastContango', data=ts_data, ax=ax, label='currentToLastContango', color='red')
        sns.lineplot(x='date', y='averageContango', data=ts_data, ax=ax, label='averageContango', color='orange')
        
        # format plot 
        ax.legend(loc='upper left')
        ax2 = ax.twinx()
        sns.lineplot(x='date', y='close', data=pxHistory_underlying, ax=ax2, label=pxHistory_underlying['symbol'][0], color='black', alpha=0.3)
        ax2.set_yscale('log')
        ax2.grid(False)
    
    return fig

"""
    Plots spread between two ts columns 
"""
def plotTermstructureSpread_seaborn(ts_data, pxHistory_underlying, colName1:str, colName2:str): 
    pxHistory_underlying.reset_index(drop=True, inplace=True)
    # add spread column
    ts_data['spread'] = ts_data[colName2] - ts_data[colName1]
    # plot lineplots on 1 plot 
    fig, ax = plt.subplots()
    sns.lineplot(x='date', y='spread', data=ts_data, ax=ax, label='spread', color='blue')
    sns.lineplot(x='date', y=colName1, data=ts_data, ax=ax, label=colName1, color='green')
    sns.lineplot(x='date', y=colName2, data=ts_data, ax=ax, label=colName2, color='red')
    
    px.line(ts_data, x='spread', y='date')

    ax2 = ax.twinx()
    sns.lineplot(x='date', y='close', data=pxHistory_underlying, ax=ax2, label=pxHistory_underlying['symbol'][0], color='black', alpha=0.3)
    
    # format plot 
    ax.legend(loc='upper left')
    ax.axhline(y=0, color='black', linestyle='-')
    ax2.set_yscale('log')
    ax2.legend(loc='upper right')
    ax2.grid(False)
    
    # add hlines at 90th and 10th percentile of spread 
    ax.axhline(y=ts_data['spread'].quantile(0.9), color='grey', linestyle='--', alpha=0.5)
    ax.axhline(y=ts_data['spread'].quantile(0.1), color='grey', linestyle='--', alpha=0.5)

    return fig

def plotTermstructureSpread(ts_data, pxHistory_underlying, colName1, colName2):
    # Reset index and calculate spread
    pxHistory_underlying.reset_index(drop=True, inplace=True)
    ts_data['spread'] = ts_data[colName2] - ts_data[colName1]

    # Create a figure with secondary y-axis
    fig = go.Figure()

    # Add spread line
    fig.add_trace(go.Scatter(x=ts_data['date'], y=ts_data['spread'],
                             mode='lines', name='Spread',
                             line=dict(color='black', width=2)))

    # Add colName1 line
    fig.add_trace(go.Scatter(x=ts_data['date'], y=ts_data[colName1],
                             mode='lines', name=colName1,
                             line=dict(color='blue', width=1, dash='dot')))

    # Add colName2 line
    fig.add_trace(go.Scatter(x=ts_data['date'], y=ts_data[colName2],
                             mode='lines', name=colName2,
                             line=dict(color='green', width=1, dash='dot')))

    # Add pxHistory_underlying close line on secondary y-axis
    fig.add_trace(go.Scatter(x=pxHistory_underlying['date'], y=pxHistory_underlying['close'],
                             mode='lines', name=pxHistory_underlying['symbol'][0],
                             line=dict(color='red', width=1, dash='dash'), yaxis="y2"))

    # Add horizontal lines at 90th and 10th percentile of spread
    fig.add_hline(y=ts_data['spread'].quantile(0.9), line=dict(color='grey', width=1, dash='dashdot'))
    fig.add_hline(y=ts_data['spread'].quantile(0.1), line=dict(color='grey', width=1, dash='dashdot'))

    # add rolling 10 day 90th and 10th percentil of spread 
    fig.add_trace(go.Scatter(x=ts_data['date'], y=ts_data['spread'].rolling(10).quantile(0.9),
                             mode='lines', name='10d 90th percentile',
                             line=dict(color='pink', width=2)))
    fig.add_trace(go.Scatter(x=ts_data['date'], y=ts_data['spread'].rolling(10).quantile(0.1),
                                mode='lines', name='10d 10th percentile',
                                line=dict(color='pink', width=2)))

    # Update layout for a dual-axis chart
    fig.update_layout(
        xaxis_title='Date',
        yaxis=dict(
            title='Spread and Prices',
            tickformat=".2f"
        ),
        yaxis2=dict(
            title='Close Prices',
            overlaying='y',
            side='right',
            showgrid=False,
            type='log'
        )
    )
    fig.show()
    return fig

""" 
    plots symbol autocorrelation 
"""
def plotAutocorrelation(pxHistory_top, pxHistory_bottom, **kwargs):
    max_lag = kwargs.get('max_lag', 40)
    pxHistory_top.reset_index(drop=True, inplace=True)
    pxHistory_bottom.reset_index(drop=True, inplace=True)

    vixnormalizedclose = (pxHistory_bottom['close'] - pxHistory_bottom['close'].mean())/pxHistory_bottom['close'].std()
    vvixnormalizedclose = (pxHistory_top['close'] - pxHistory_top['close'].mean())/pxHistory_top['close'].std()

    # initialize autocrrelation
    vixautocorrel = np.array([1.0] + [vixnormalizedclose.autocorr(lag) for lag in range(1, max_lag + 1)])
    vvixautocorrel = np.array([1.0] + [vvixnormalizedclose.autocorr(lag) for lag in range(1, max_lag + 1)])

    # create figure and axes, 2x2 grid
    fig, ax = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('%s & %s Autocorrelation'%(pxHistory_top['symbol'][0], pxHistory_bottom['symbol'][0]))

    # plot autocorrelation of vvix
    ax[0,0].stem(vvixautocorrel, linefmt='--')
    # add title
    ax[0,0].set_title('%s Autocorrelation (close px)'%(pxHistory_top['symbol'][0]))

    # plot autocorrelation of vix
    ax[1,0].stem(vixautocorrel, linefmt='--')
    # add title
    ax[1,0].set_title('%s Autocorrelation (close px)'%(pxHistory_bottom['symbol'][0]))

    # plot autocorrelation of vvix
    #pd.plotting.autocorrelation_plot(vvix['close'], ax=ax[0,0])
    # add title
    #ax[0,0].set_title('Autocorrelation: %s close px'%(vvix['symbol'][0]))

    vix_logReturnAutoCorrelation = np.array([1.0] + [pxHistory_bottom['logReturn'].autocorr(lag) for lag in range(1, max_lag + 1)])
    vvix_logReturnAutoCorrelation = np.array([1.0] + [pxHistory_top['logReturn'].autocorr(lag) for lag in range(1, max_lag + 1)])
    # plot autocorrelation of vvix logreturn on the same axis
    #pd.plotting.autocorrelation_plot(pxHistory_top['logReturn'], ax=ax[0,1])
    # add title
    ax[0,1].stem(vix_logReturnAutoCorrelation, linefmt='--')
    ax[0,1].set_title('%s Autocorrelation (logrtrn)'%(pxHistory_top['symbol'][0]))

    # plot autocorrelation of vix
    #pd.plotting.autocorrelation_plot(vix['close'], ax=ax[1,0])
    # add title
    #ax[1,0].set_title('Autocorrelation: %s close px'%(vix['symbol'][0]))

    # plot autocorrelation of vix logreturn on the same axis
    #pd.plotting.autocorrelation_plot(pxHistory_bottom['logReturn'], ax=ax[1,1])
    # add title
    ax[1,1].stem(vvix_logReturnAutoCorrelation, linefmt='--')
    ax[1,1].set_title('%s Autocorrelation (logrtrn)'%(pxHistory_bottom['symbol'][0]))

    return fig

"""
    this function plots a scatter of log return in spx vs. a vix close 
    timeframe: 1 day
    inputs: vix
    returns a figure
"""
def plotVixVsSpx(vix, spx):
    # remove dates in vix not in spx 
    vix = vix[vix['date'].isin(spx['date'])]

    # add column absChange to vix that is the absolute value of the change in close vs previous day 
    vix['absChange'] = vix['close'] - vix['close'].shift(1)

    # create figure and axes
    fig, ax = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('VIX vs. SPX')

    # axis solid black line 
    ax[0,0].axhline(y=0, color='grey', linestyle='-')
    ax[0,0].axvline(x=0, color='grey', linestyle='-')
    
    # plot regplot 
    sns.regplot(x=spx['logReturn'], y=vix['absChange'], ax=ax[0,0], line_kws={'color': 'red'})

    # color datapoints that are in the current year in yellow
    sns.scatterplot(x=spx['logReturn'], y=vix['absChange'], ax=ax[0,0], hue=spx['date'].dt.year, palette='YlOrBr')

    # add title
    ax[0,0].set_title('VIX vs. SPX')

    # on ax[0,1] plot the distribution of vix absChange
    sns.histplot(x=vix['absChange'], ax=ax[0,1])
    ax[0,1].set_title('VIX absChange Distribution')


    return fig

"""
    Plots scatters of lagged momentum vs. next day return for multiple lags 
"""
def plotMomentumOverview(pxHistory):
    # reset index
    pxHistory.reset_index(drop=True, inplace=True)
    
    fig, ax = plt.subplots(3, 3, figsize=(15, 10), sharey=True)
    
    # set figure title
    fig.suptitle('%s Momentum'%(pxHistory['symbol'][0]))

    # get momo w/ 1 period lag 
    pxHistory_mom = momentum.calcMomoFactor(pxHistory, lag=2)
    # plot next day pctChange vs. lagged momo 
    sns.scatterplot(x=pxHistory_mom['pctChange'], y=pxHistory_mom['momo'], ax=ax[0,0])
    sns.regplot(x=pxHistory_mom['pctChange'], y=pxHistory_mom['momo'], ax=ax[0,0], line_kws={'color': 'red'})

    ax[0,0].set_title('%s pctChange vs. %s momo 1'%(pxHistory['symbol'][0], pxHistory['symbol'][0]))

    # get momo w/ 3 period lag
    pxHistory_mom = momentum.calcMomoFactor(pxHistory, lag=3)
    # plot next day pctChange vs. lagged momo
    sns.scatterplot(x=pxHistory_mom['pctChange'], y=pxHistory_mom['momo'], ax=ax[0,1])
    sns.regplot(x=pxHistory_mom['pctChange'], y=pxHistory_mom['momo'], ax=ax[0,1], line_kws={'color': 'red'})
    ax[0,1].set_title('%s pctChange vs. %s momo 3'%(pxHistory['symbol'][0], pxHistory['symbol'][0]))

    # get momo w/ 5 period lag
    pxHistory_mom = momentum.calcMomoFactor(pxHistory, lag=5)
    # plot next day pctChange vs. lagged momo
    sns.scatterplot(x=pxHistory_mom['pctChange'], y=pxHistory_mom['momo'], ax=ax[0,2])
    sns.regplot(x=pxHistory_mom['pctChange'], y=pxHistory_mom['momo'], ax=ax[0,2], line_kws={'color': 'red'})
    ax[0,2].set_title('%s pctChange vs. %s momo 5'%(pxHistory['symbol'][0], pxHistory['symbol'][0]))

    # get momo w/ 7 period lag
    pxHistory_mom = momentum.calcMomoFactor(pxHistory, lag=7)
    # plot next day pctChange vs. lagged momo
    sns.scatterplot(x=pxHistory_mom['pctChange'], y=pxHistory_mom['momo'], ax=ax[1,0])
    sns.regplot(x=pxHistory_mom['pctChange'], y=pxHistory_mom['momo'], ax=ax[1,0], line_kws={'color': 'red'})
    ax[1,0].set_title('%s pctChange vs. %s momo 7'%(pxHistory['symbol'][0], pxHistory['symbol'][0]))

    # get momo w/ 10 period lag
    pxHistory_mom = momentum.calcMomoFactor(pxHistory, lag=10)
    # plot next day pctChange vs. lagged momo
    sns.scatterplot(x=pxHistory_mom['pctChange'], y=pxHistory_mom['momo'], ax=ax[1,1])
    sns.regplot(x=pxHistory_mom['pctChange'], y=pxHistory_mom['momo'], ax=ax[1,1], line_kws={'color': 'red'})
    ax[1,1].set_title('%s pctChange vs. %s momo 10'%(pxHistory['symbol'][0], pxHistory['symbol'][0]))

    # get momo w/ 15 period lag
    pxHistory_mom = momentum.calcMomoFactor(pxHistory, lag=15)
    # plot next day pctChange vs. lagged momo
    sns.scatterplot(x=pxHistory_mom['pctChange'], y=pxHistory_mom['momo'], ax=ax[1,2])
    sns.regplot(x=pxHistory_mom['pctChange'], y=pxHistory_mom['momo'], ax=ax[1,2], line_kws={'color': 'red'})
    ax[1,2].set_title('%s pctChange vs. %s momo 15'%(pxHistory['symbol'][0], pxHistory['symbol'][0]))

    # get momo w/ 20 period lag
    pxHistory_mom = momentum.calcMomoFactor(pxHistory, lag=20)
    # plot next day pctChange vs. lagged momo
    sns.scatterplot(x=pxHistory_mom['pctChange'], y=pxHistory_mom['momo'], ax=ax[2,0])
    sns.regplot(x=pxHistory_mom['pctChange'], y=pxHistory_mom['momo'], ax=ax[2,0], line_kws={'color': 'red'})
    ax[2,0].set_title('%s pctChange vs. %s momo 20'%(pxHistory['symbol'][0], pxHistory['symbol'][0]))

    # get momo w/ 30 period lag
    pxHistory_mom = momentum.calcMomoFactor(pxHistory, lag=30)
    # plot next day pctChange vs. lagged momo
    sns.scatterplot(x=pxHistory_mom['pctChange'], y=pxHistory_mom['momo'], ax=ax[2,1])
    sns.regplot(x=pxHistory_mom['pctChange'], y=pxHistory_mom['momo'], ax=ax[2,1], line_kws={'color': 'red'})
    ax[2,1].set_title('%s pctChange vs. %s momo 30'%(pxHistory['symbol'][0], pxHistory['symbol'][0]))

    # get momo w/ 60 period lag
    pxHistory_mom = momentum.calcMomoFactor(pxHistory, lag=60)
    # plot next day pctChange vs. lagged momo
    sns.scatterplot(x=pxHistory_mom['pctChange'], y=pxHistory_mom['momo'], ax=ax[2,2])
    sns.regplot(x=pxHistory_mom['pctChange'], y=pxHistory_mom['momo'], ax=ax[2,2], line_kws={'color': 'red'})
    ax[2,2].set_title('%s pctChange vs. %s momo 60'%(pxHistory['symbol'][0], pxHistory['symbol'][0]))


    return fig

"""
    Plot scatters of lagged momentum vs. next day return of a different symbol
     inputs:
      - pxHistory_momentumSymbol
      - pxHistory_returnSymbol 
"""
def plotMomentumComparison(pxHistory_momentumSymbol, pxHistory_returnSymbol):
    # create figure and axes
    fig, ax = plt.subplots(2, 2, figsize=(15, 10), sharey=True)

    # make sure both passed in dataframes have the same dates
    pxHistory_momentumSymbol = pxHistory_momentumSymbol[pxHistory_momentumSymbol['date'].isin(pxHistory_returnSymbol['date'])]
    pxHistory_returnSymbol = pxHistory_returnSymbol[pxHistory_returnSymbol['date'].isin(pxHistory_momentumSymbol['date'])]

    # replace pctChange column in pxHistory_momentumSymbol with pctChange column in pxHistory_returnSymbol
    pxHistory_momentumSymbol['pctChange'] = pxHistory_returnSymbol['pctChange']

    # reset index
    pxHistory_momentumSymbol.reset_index(drop=True, inplace=True)
    pxHistory_returnSymbol.reset_index(drop=True, inplace=True)

    # get momo w/ 1 period lag 
    pxMom = momentum.calcMomoFactor(pxHistory_momentumSymbol, lag=1)
    # plot next day pctChange vs. lagged momo
    sns.scatterplot(x=pxMom['pctChange'], y=pxMom['momo'], ax=ax[0,0])
    sns.regplot(x=pxMom['pctChange'], y=pxMom['momo'], ax=ax[0,0], line_kws={'color': 'red'})
    ax[0,0].set_title('%s pctChange vs. %s momo 1'%(pxHistory_returnSymbol['symbol'][0], pxHistory_momentumSymbol['symbol'][0]))

    # get momo w/ 5 period lag
    pxMom = momentum.calcMomoFactor(pxHistory_momentumSymbol, lag=5)
    # plot next day pctChange vs. lagged momo
    sns.scatterplot(x=pxMom['pctChange'], y=pxMom['momo'], ax=ax[0,1])
    sns.regplot(x=pxMom['pctChange'], y=pxMom['momo'], ax=ax[0,1], line_kws={'color': 'red'})
    ax[0,1].set_title('%s pctChange vs. %s momo 5'%(pxHistory_returnSymbol['symbol'][0], pxHistory_momentumSymbol['symbol'][0]))

    # get momo w/ 10 period lag
    pxMom = momentum.calcMomoFactor(pxHistory_momentumSymbol, lag=10)
    # plot next day pctChange vs. lagged momo
    sns.scatterplot(x=pxMom['pctChange'], y=pxMom['momo'], ax=ax[1,0])
    sns.regplot(x=pxMom['pctChange'], y=pxMom['momo'], ax=ax[1,0], line_kws={'color': 'red'})
    ax[1,0].set_title('%s pctChange vs. %s momo 10'%(pxHistory_returnSymbol['symbol'][0], pxHistory_momentumSymbol['symbol'][0]))

    # get momo w/ 20 period lag
    pxMom = momentum.calcMomoFactor(pxHistory_momentumSymbol, lag=20)
    # plot next day pctChange vs. lagged momo
    sns.scatterplot(x=pxMom['pctChange'], y=pxMom['momo'], ax=ax[1,1])
    sns.regplot(x=pxMom['pctChange'], y=pxMom['momo'], ax=ax[1,1], line_kws={'color': 'red'})
    ax[1,1].set_title('%s pctChange vs. %s momo 20'%(pxHistory_returnSymbol['symbol'][0], pxHistory_momentumSymbol['symbol'][0]))
    
    return fig

"""
    Plots distribution of forward returns
"""
def plotForwardReturnsDistribution(pxHistory, forwardReturnPeriods=[1,2,3,4,5,6,7]):
    # create figure and axes
    fig, ax = plt.subplots(2, 4, figsize=(15, 10), sharey=True)

    # set figure title
    fig.suptitle('%s Forward Returns Distribution'%(pxHistory['symbol'][0]))

    # loop through forwardReturnPeriods and plot distribution of forward returns
    for i in range(len(forwardReturnPeriods)):
        # get forward returns for period i
        fwdReturns = pxHistory['fwdReturn_%dd'%(forwardReturnPeriods[i])]
        # plot distribution of fwdReturns
        sns.histplot(x=fwdReturns, ax=ax[i//4, i%4])
        # calculate median
        median = fwdReturns.median()
        # calculate mode and add to plot 
        mode = fwdReturns.mode()[0]
        ax[i//4, i%4].axvline(x=median, color='red', linestyle='--')
        # add axvline value as overlay text
        ax[i//4, i%4].text(median, 0, '%.2f'%(median), color='red', fontsize=10)

        ax[i//4, i%4].set_title('%dd fwdReturn'%(forwardReturnPeriods[i]))

    return fig

"""
    PLots cumulative distribution of forward returns
"""
def plotForwardReturnCumulativeDistribution(pxHistory, forwardReturnPeriods=[1,2,3,4,5,6,7]):
    # create figure and axes
    fig, ax = plt.subplots(2, 4, figsize=(15, 10), sharey=True)

    # set figure title
    fig.suptitle('%s Forward Returns Distribution'%(pxHistory['symbol'][0]))

    # loop through forwardReturnPeriods and plot distribution of forward returns
    for i in range(len(forwardReturnPeriods)):
        # get forward returns for period i
        fwdReturns = pxHistory['fwdReturn_%dd'%(forwardReturnPeriods[i])]
        # plot cumulative distribution of fwdReturns
        sns.histplot(x=fwdReturns, ax=ax[i//4, i%4], cumulative=True)
        # calculate median
        #median = fwdReturns.median()
        # calculate mode and add to plot 
        #mode = fwdReturns.mode()[0]
        #ax[i//4, i%4].axvline(x=median, color='red', linestyle='--')
        # add axvline value as overlay text
        #ax[i//4, i%4].text(median, 0, '%.2f'%(median), color='red', fontsize=10)

        ax[i//4, i%4].set_title('%dd fwdReturn'%(forwardReturnPeriods[i]))

    return fig

"""
    Plot scatter of target column vs. forward returns
"""
def plotScatter(pxHistory, targetColumn, forwardReturnPeriods=[1,2,3,4,5,6,7]):
    # create figure and axes
    fig, ax = plt.subplots(2, 4, figsize=(15, 10), sharey=True)

    # set figure title
    fig.suptitle('%s Forward Returns Distribution'%(pxHistory['symbol'][0]))

    # loop through forwardReturnPeriods and plot distribution of forward returns
    for i in range(len(forwardReturnPeriods)):
        # get forward returns for period i
        fwdReturns = pxHistory['fwdReturn_%dd'%(forwardReturnPeriods[i])]
        # plot scatter plot vs fwdReturns
        sns.scatterplot(x=fwdReturns, y=pxHistory[targetColumn], ax=ax[i//4, i%4])
        # plot regplot
        sns.regplot(x=fwdReturns, y=pxHistory[targetColumn], ax=ax[i//4, i%4], line_kws={'color': 'red'})

        # calculate r2
        r2 = fwdReturns.corr(pxHistory[targetColumn])**2
        # add r2 to plot
        ax[i//4, i%4].text(0, 0, 'r2: %.2f'%(r2), color='red', fontsize=10)


        ax[i//4, i%4].set_title('%dd fwdReturn'%(forwardReturnPeriods[i]))

    return fig

"""
    for passed in dataframes (main, reference) return main with only the dates in reference 
    sidenote: this is an incredibly unnecessary abstraction but here we are 
"""
def _filterDates(main, reference):
    return main[main['date'].isin(reference['date'])]

vvix_topPercentile = 0.9
vvix_bottomPercentile = 0.1
vvix_percentileLookbackDays = 252 ## 1 year lookback = 252 *trading* days

#####################################
## prepare vix term structure data 
#####################################
with db.sqlite_connection(db_termstructure) as conn:
    vix_ts_raw = vixts.getRawTermStructure(termstructure_db_conn=conn)
    ng_ts_raw = vixts.getRawTermStructure(termstructure_db_conn=conn, symbol='NG')

vix_ts_pctContango = vixts.getTermStructurePctContango(vix_ts_raw, oneToTwo=True, oneToThree=True, twoToThree=True, threeToFour=True, fourToSeven=True, currentToLast=True, averageContango=True)
ng_ts_pctContango = vixts.getTermStructurePctContango(ng_ts_raw, oneToTwo=True, oneToThree=True, twoToThree=True, fourToSeven=True, threeToFour=True, currentToLast=True, averageContango=True)

###################################
## prepare price history data
with db.sqlite_connection(db_stock) as conn:
    vix = db.getPriceHistory(conn,'VIX', '1day', withpctChange=True)
    #vix_5min = db.getPriceHistory(conn, 'VIX', '5mins', withpctChange=True)
    vvix = db.getPriceHistory(conn, 'VVIX', '1day', withpctChange=True)
    #vvix_5min = db.getPriceHistory(conn, 'VVIX', '5mins', withpctChange=True)
    spx = db.getPriceHistory(conn, 'SPX', '1day', withpctChange=True)
    #spx_5mins = db.getPriceHistory(conn, 'SPX', '5mins', withpctChange=True)
    uvxy = db.getPriceHistory(conn, 'UVXY', '1day', withpctChange=True)
    #uvxy_5mins= db.getPriceHistory(conn, 'UVXY', '5mins', withpctChange=True)
    ung = db.getPriceHistory(conn, 'kold', '1day', withpctChange=True)
    boil = db.getPriceHistory(conn, 'boil', '1day', withpctChange=True)

## calculate percentile rank of VVIX
vvix['percentileRank'] = vvix['close'].rolling(vvix_percentileLookbackDays).apply(lambda x: pd.Series(x).rank(pct=True).iloc[-1])
vvix['percentileRank_90d'] = vvix['close'].rolling(90).apply(lambda x: pd.Series(x).rank(pct=True).iloc[-1])
vvix['percentileRank_60d'] = vvix['close'].rolling(60).apply(lambda x: pd.Series(x).rank(pct=True).iloc[-1])

# add log return column
vvix = ut.calcLogReturns(vvix, 'close')
vix = ut.calcLogReturns(vix, 'close')


#################################################
############## Filter dates 
# reset index to eliminate duplicate indices resulting from joins 
vix_ts_pctContango.reset_index(inplace=True)
ng_ts_pctContango.reset_index(inplace=True)

## from vix_ts_pctContango remove any dates that are not in vix and vvix
vix_ts_pctContango = vix_ts_pctContango[vix_ts_pctContango['date'].isin(vix['date']) & vix_ts_pctContango['date'].isin(vvix['date'])]
vix_ts_pctContango.drop_duplicates(subset=['date'], inplace=True)

# from vvix remove any dates that are not in vix and vix_ts_pctContango
#vvix = vvix[vvix.index.isin(vix.index) & vvix.index.isin(vix_ts_pctContango['date'])]
vvix = vvix[vvix['date'].isin(vix['date']) & vvix['date'].isin(vix_ts_pctContango['date'])]

# from vix remove any dates that are not in vvix and vix_ts_pctContango
vix = vix[vix['date'].isin(vvix['date']) & vix['date'].isin(vix_ts_pctContango['date'])]

# from uvxy_filtered remove any dates not in contango 
uvxy_filtered = uvxy[uvxy['date'].isin(vix_ts_pctContango['date'])].copy()
vix_ts_pctContango_filtered = vix_ts_pctContango[vix_ts_pctContango['date'].isin(uvxy_filtered['date'])]
# remove duplicates 
uvxy_filtered.drop_duplicates(subset=['date'], inplace=True)
spx_filtered = _filterDates(spx, vix_ts_pctContango)

#print(ng_ts_pctContango.head(5))
#print(vix_ts_pctContango.head(5))
# filter ng
ng_ts_pctContango_filtered = _filterDates(ng_ts_pctContango, ung)
ung_filtered = _filterDates(ung, ng_ts_pctContango_filtered)
boil_filtered = _filterDates(boil, ng_ts_pctContango_filtered)
#print(ung.head(5))
#print(ung_filtered.head(5))
##################################################
############### call plots  
sns.set()
sns.set_style('darkgrid')

# get spx price history

# initialize plot window for tabbed plots
tpw = pltWindow.plotWindow()
tpw.MainWindow.resize(2560, 1380)

########## General Overview: 
########## 

#tpw.addPlot('ts 1-2:4-7 spread', plotTermstructureSpread(vix_ts_pctContango, uvxy_filtered, 'oneToTwoMoContango', 'fourToSevenMoContango'))
#tpw.addPlot('vol monitor', plotVixTermStructureMonitor(vix_ts_pctContango, vix, uvxy_filtered, contangoColName='oneToTwoMoContango'))
tpw.addPlot('VIX ts', plotHistoricalTermstructure(vix_ts_pctContango, uvxy_filtered))
tpw.addPlot('NG ts', plotHistoricalTermstructure(ng_ts_pctContango, boil_filtered))
tpw.addPlot('NG vs ung ts', plotTermstructureSpread_seaborn(ng_ts_pctContango_filtered, ung_filtered, 'oneToTwoMoContango', 'fourToSevenMoContango'))
tpw.addPlot('NG vs boil ts', plotTermstructureSpread_seaborn(ng_ts_pctContango_filtered, boil_filtered, 'oneToTwoMoContango', 'fourToSevenMoContango'))
tpw.addPlot('VVIX & VIX Autocorrelation', plotAutocorrelation(vvix, vix))
#tpw.addPlot('Momentum - VVIX', volMomo.plotMomoScatter(vvix))
#tpw.addPlot('Momentum - VIX', volMomo.plotMomoScatter(vix))

#tpw.addPlot('Momentum - VIX vs. VVIX', plotMomentumComparison(vvix, vix))

tpw.show()

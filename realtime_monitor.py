"""
    plots vix / vix3m ratio w/ stats 

"""
# import sys 
# sys.path.append(config.path_lib_analysis_strategies)
# from strategy_implementation.strategy_vix3m_vix_ratio import *
import config 

from interface import interface_ibkr as ib
from interface import interface_localDB as db
from strategy_implementation import strategy_vix3m_vix_ratio as vv

import ffn
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from ib_insync import *
from datetime import datetime, timedelta
from rich import print 
from matplotlib.animation import FuncAnimation
from core import indicators

# _tickerFilepath = config.watchlist_main ## List of symbols to keep track of
_dbName_stock = config.dbname_stock ## Default DB names
ibkrThrottleTime = 10 # minimum seconds to wait between api requests to ibkr

def _calc_ntile(pxhistory, numBuckets, colname, rollingWindow=252):

    if rollingWindow > 0:
        pxhistory['%s_ntile' % colname] = pxhistory[colname].rolling(rollingWindow).apply(lambda x: pd.qcut(x, numBuckets, labels=False, duplicates='drop').iloc[-1], raw=False)
    else:
        pxhistory['%s_ntile' % colname] = pd.qcut(pxhistory[colname], numBuckets, labels=False, duplicates='drop')
    
    return pxhistory

def _calc_zscore(pxhistory, colname, rollingWindow=252, rescale = False): 
    """
        Calculate the z-score of a column.
        Params: 
            colname: str column name to calculate z-score on
            rollingWindow: int rolling window to calculate z-score on. Settingto 0 uses entire population 
            _pxHistory: pd.DataFrame to calculate z-score on. Default is None, which uses the objects default pxhistory
    """
    if rollingWindow == 0:
        pxhistory['%s_zscore'%(colname)] = pxhistory[colname] - pxhistory[colname].mean() / pxhistory[colname].std()
    else: 
        pxhistory['%s_zscore'%(colname)] = pxhistory[colname].rolling(rollingWindow).apply(lambda x: (x[-1] - x.mean()) / x.std(), raw=True)
    
    if rescale:
        pxhistory['%s_zscore'%(colname)] = ffn.rescale(pxhistory['%s_zscore'%(colname)])
    
    return pxhistory

def plot_realtime_monitor_vix3m_vix_ratio():
    symbol = 'VIX3M'
    symbol2 = 'VIX'
    vix3m_vix_ratio_object = vv.StrategyVixAndVol(interval='1day', ma_period_short=15, ma_period_long=60, strategy_name='realtime_monitor')    

    fig, ax = plt.subplots(2, 2, figsize=(15, 7))
    ax1_twin = ax[0,1].twinx()
    ax0_twin = ax[0,0].twinx()

    vix3m_vix_ratio_object.draw_lineplot(ax[1,0], y='vix3m_vix_ratio', y_alt ='vix3m_vix_ratio_decile', n_periods_to_plot=60, plot_title='VIX3M/VIX Ratio')
    vix3m_vix_ratio_object.draw_lineplot(ax[1,1], y='vix3m_vix_ratio_ma_long_vix3m_vix_ratio_ma_short_crossover', y_alt ='vix3m_vix_ratio_ma_long_vix3m_vix_ratio_ma_short_crossover_decile' , n_periods_to_plot=60, plot_title='VIX3M/VIX Ratio Crossover')


    def animate(i):
        # for a in ax:
        #     a.clear()
        # plt.clf()
        # fig.clear()
        wma_period_long = 90
        wma_period_short = 30

        # timestamp.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        ## *** TESTING CODE **** 
        ## manually set p and p2 for testing 
        # import numpy as np
        # p = Ticker(con)
        # p.last = np.random.randint(12, 15)
        # p2 = Ticker(con2)
        # p2.last = np.random.randint(12, 15)

        ## get data from ib 
        ibkr = ib.setupConnection() 
        symbol_bars = ib.getBars(ibkr, symbol = symbol, interval = '1 min', lookback = '2 D')
        symbol2_bars = ib.getBars(ibkr, symbol = symbol2, interval = '1 min', lookback = '2 D')
        ibkr.sleep(1)
        ibkr.disconnect()

        ## format the returned data 
        symbol_bars.set_index('date', inplace=True)
        symbol2_bars.set_index('date', inplace=True)

        ## merge vix3m and vix dataframes
        merged = symbol_bars.merge(symbol2_bars, on='date', suffixes=('_vix3m', '_vix'))
        merged.reset_index(inplace=True)
        merged['date'] = pd.to_datetime(merged['date'])
        
        merged['ratio'] = merged['close_vix3m']/merged['close_vix']
        
        merged = indicators.moving_average_weighted(merged, 'ratio', wma_period_long)
        merged.rename(columns={'ratio_wma': 'ratio_wma_long'}, inplace=True)
        
        merged = indicators.moving_average_weighted(merged, 'ratio', wma_period_short)
        merged.rename(columns={'ratio_wma': 'ratio_wma_short'}, inplace=True)
        
        merged = indicators.moving_average_crossover(merged, colname_long = 'ratio_wma_long', colname_short = 'ratio_wma_short')
        
        merged = indicators.intra_day_cumulative_signal(merged, 'ratio_wma_long_ratio_wma_short_crossover', intraday_reset=True)
        
        merged['symbol'] = 'VIX3M/VIX' 
        merged = _calc_ntile(pxhistory=merged, numBuckets=10, colname='ratio')
        merged = _calc_ntile(pxhistory=merged, numBuckets=10, colname='ratio_wma_long_ratio_wma_short_crossover')
        merged = _calc_ntile(pxhistory=merged, numBuckets=10, colname='ratio_wma_long_ratio_wma_short_crossover_cumsum')
        
        merged = _calc_zscore(pxhistory=merged, colname='ratio_wma_long_ratio_wma_short_crossover', rescale=True)
        merged = indicators.momentum_factor(merged, colname='ratio', lag=30)
        # rolling 5-period avg of momo
        merged['momo'] = merged['momo'].rolling(window=15).mean()
        merged['date'] = merged['date'].dt.strftime('%Y-%m-%d %H:%M:%S')
        # merged['date'] = merged['date'].str[-8:] # only keep h m s 


        # only plot the last 7 * 60 minutes
        merged = merged.iloc[-7*60:]

        ax[0,0].clear()
        ax0_twin.clear()
        
        # plot ratio and WMA's 
        sns.lineplot(y=merged['ratio'], x=merged['date'], ax=ax[0,0], color='blue', label='ratio')
        sns.lineplot(y=merged['ratio_wma_long'], x=merged['date'], ax=ax[0,0], color='red', alpha=0.7)
        sns.lineplot(y=merged['ratio_wma_short'], x=merged['date'], ax=ax[0,0], color='red', alpha=0.2)
        vix3m_vix_ratio_object.apply_default_lineplot_formatting(ax[0,0], title='VIX3M/VIX Ratio')
        ax0_twin.axhline(y=0, color='grey', linestyle='--', alpha=0.3)

        # plot ratio decile 
        sns.lineplot(y=merged['momo'], x=merged['date'], ax=ax0_twin, color='grey', label='momo', alpha=0.3)
        vix3m_vix_ratio_object.apply_default_lineplot_formatting(ax1_twin)

        ax[0,0].legend(loc='upper left')   
        ax0_twin.legend(loc='lower left')

        ax[0,1].clear()
        ax1_twin.clear()
        # sns.lineplot(y=merged['ratio_wma_long_ratio_wma_short_crossover'], x=merged['date'], ax=ax1_twin, color='grey', label='crossover', alpha=0.3)
        
        sns.lineplot(y=merged['ratio_wma_long_ratio_wma_short_crossover_ntile'], x=merged['date'], ax=ax1_twin, color='grey', alpha=0.3, label='crossover decile')
        sns.lineplot(y=merged['ratio_wma_long_ratio_wma_short_crossover_zscore'], x=merged['date'], ax=ax[0,1], color='green', label='crossover zscore')
        vix3m_vix_ratio_object.apply_default_lineplot_formatting(ax[0,1], title='Crossover Cumsum')
        vix3m_vix_ratio_object.apply_default_lineplot_formatting(ax1_twin, title='')
        ax[0,1].axhline(y=0, color='green', linestyle='-', alpha=0.5)
        ax1_twin.axhline(y=0, color='grey', linestyle='--', alpha=0.3)
        # show legend 
        ax[0,1].legend(loc='upper left')
        ax1_twin.legend(loc='lower left')

        # set the plot window title to timestamsp
        fig.suptitle(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), fontsize=7)

        print('%s: VIX3M: %.4f'%(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), merged['close_vix3m'].iloc[-1]))
        print('%s: VIX:   %.4f'%(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), merged['close_vix'].iloc[-1]))
        print('%s: Ratio: %.5f, %speriod avg: %.5f, Crossover: %.5f'%(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), merged['close_vix3m'].iloc[-1]/merged['close_vix'].iloc[-1], wma_period_long, merged['ratio_wma_long'].iloc[-1], merged['ratio_wma_long_ratio_wma_short_crossover'].iloc[-1] ))
        print('%s: Cumulative Crossover: %.5f \n'%(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), merged['ratio_wma_long_ratio_wma_short_crossover_cumsum'].iloc[-1] ))
    
    def interval_length():
        # get in seconds between now and the next minute
        now = datetime.now()
        # next_minute = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
        # seconds_to_next_minute = (next_minute - now).seconds
        # difference between 60 and current second 
        seconds_to_next_minute = 60 - now.second
        print('Seconds to next minute: %s'%(seconds_to_next_minute))
        return seconds_to_next_minute * 1000
    # animate the plot 
    animate(1)
    ani = FuncAnimation(fig, animate, interval=60000)
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    plot_realtime_monitor_vix3m_vix_ratio()
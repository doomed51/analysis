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

def plot_realtime_monitor_vix3m_vix_ratio():
    symbol = 'VIX3M'
    symbol2 = 'VIX'
    vix3m_vix_ratio_object = vv.StrategyVixAndVol(interval='1day', ma_period_short=15, ma_period_long=60, strategy_name='realtime_monitor')    

    fig, ax = plt.subplots(2, 2, figsize=(15, 7))
    ax1_twin = ax[0,1].twinx()

    vix3m_vix_ratio_object.draw_lineplot(ax[1,0], y='vix3m_vix_ratio', y_alt ='vix3m_vix_ratio_decile', n_periods_to_plot=60, plot_title='VIX3M/VIX Ratio')
    vix3m_vix_ratio_object.draw_lineplot(ax[1,1], y='vix3m_vix_ratio_ma_long_vix3m_vix_ratio_ma_short_crossover', y_alt ='vix3m_vix_ratio_ma_long_vix3m_vix_ratio_ma_short_crossover_decile' , n_periods_to_plot=60, plot_title='VIX3M/VIX Ratio Crossover')


    def animate(i):
        # for a in ax:
        #     a.clear()
        # plt.clf()
        # fig.clear()
        wma_period_long = 60
        wma_period_short = 15

        # timestamp.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        ## *** TESTING CODE **** 
        ## manually set p and p2 for testing 
        # import numpy as np
        # p = Ticker(con)
        # p.last = np.random.randint(12, 15)
        # p2 = Ticker(con2)
        # p2.last = np.random.randint(12, 15)

        ibkr = ib.setupConnection() 
        symbol_bars = ib.getBars(ibkr, symbol = symbol, interval = '1 min', lookback = '45000 S')
        symbol2_bars = ib.getBars(ibkr, symbol = symbol2, interval = '1 min', lookback = '45000 S')
        ibkr.sleep(1)
        ibkr.disconnect()
        symbol_bars.set_index('date', inplace=True)
        symbol2_bars.set_index('date', inplace=True)
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
        # convert date to string 
        merged['date'] = merged['date'].dt.strftime('%Y-%m-%d %H:%M:%S')
        # only keep h m s 
        merged['date'] = merged['date'].str[-8:]

        # convert date to datetime 
        ax[0,0].clear()
        sns.lineplot(y=merged['ratio'], x=merged['date'], ax=ax[0,0], color='blue')
        sns.lineplot(y=merged['ratio_wma_long'], x=merged['date'], ax=ax[0,0], color='red', alpha=0.7)
        sns.lineplot(y=merged['ratio_wma_short'], x=merged['date'], ax=ax[0,0], color='red', alpha=0.2)
        vix3m_vix_ratio_object.apply_default_lineplot_formatting(ax[0,0], title='VIX3M/VIX Ratio', ylabel='Ratio', xlabel='')

        ax[0,1].clear()
        ax1_twin.clear()
        sns.lineplot(y=merged['ratio_wma_long_ratio_wma_short_crossover'], x=merged['date'], ax=ax1_twin, color='grey', label='crossover', alpha=0.3)
        # ax1_twin.clear()
        sns.lineplot(y=merged['ratio_wma_long_ratio_wma_short_crossover_cumsum'], x=merged['date'], ax=ax[0,1], color='green', label='crossover cumsum')
        vix3m_vix_ratio_object.apply_default_lineplot_formatting(ax[0,1], title='Crossover Cumsum', ylabel='Crossover Cumsum', xlabel='')
        ax[0,1].axhline(y=0, color='green', linestyle='-', alpha=0.5)
        ax1_twin.axhline(y=0, color='grey', linestyle='--', alpha=0.3)
        # show legend 
        ax[0,1].legend(loc='upper left')
        ax1_twin.legend(loc='lower left')


        print('%s: VIX3M: %.4f'%(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), merged['close_vix3m'].iloc[-1]))
        print('%s: VIX:   %.4f'%(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), merged['close_vix'].iloc[-1]))
        print('%s: Ratio: %.5f, %speriod avg: %.5f, Crossover: %.5f'%(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), merged['close_vix3m'].iloc[-1]/merged['close_vix'].iloc[-1], wma_period_long, merged['ratio_wma_long'].iloc[-1], merged['ratio_wma_long_ratio_wma_short_crossover'].iloc[-1] ))
        print('%s: Cumulative Crossover: %.5f \n'%(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), merged['ratio_wma_long_ratio_wma_short_crossover_cumsum'].iloc[-1] ))
    
    # animate the plot 
    animate(1)
    ani = FuncAnimation(fig, animate, interval=60000)
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    plot_realtime_monitor_vix3m_vix_ratio()
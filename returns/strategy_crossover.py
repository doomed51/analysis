"""
    Class that implements a crossover strategy. initialized with base_df, signal_df, and signal_column_name.
"""
import math

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from utils import utils_strategyAnalyzer as sa
from returns.strategy import Strategy

class CrossoverStrategy(Strategy):
    def __init__(self, symbol, base_df, signal_df, target_column_name, signal_column_name):
        self.symbol = symbol
        self.target_column_name = target_column_name
        self.signal_column_name = signal_column_name
        self.target_df = base_df.reset_index()
        self.signal_df = signal_df.sort_index(ascending=True).reset_index()
        self._align_target_and_signal_()
        self.underlying_pxhistory = self._load_underlying_pxhistory()
        if 'close' in self.signal_df.columns:
            self.signal_df = self.signal_df.drop(columns=['close'])
        
        # add close from base to signal joining on date 
        self.signal_df = self.target_df[['date', 'close', 'symbol']].rename(
            columns={'symbol': 'symbol_underlying'}).merge(
                self.signal_df, on='date', how='inner')


    def _align_base_and_signal_(self):
        # make sure date column in both dataframes is formatted the same 
        self.target_df['date'] = pd.to_datetime(self.target_df['date'])
        self.signal_df['date'] = pd.to_datetime(self.signal_df['date'])
        # only include dates that are in both base and signal
        self.target_df = self.target_df[self.target_df['date'].isin(self.signal_df['date'])]
        self.signal_df = self.signal_df[self.signal_df['date'].isin(self.target_df['date'])]



    def _calculateSignal(self, signal_df):
        # calculated as target column - signal column
        signal_df['signal'] = self.target_df[self.target_column_name] - signal_df[self.signal_column_name]
        # smooth signal column
        #signal_df['signal'] = signal_df['signal'].rolling(20).mean()        

        return signal_df

    def plotSignalOverview(self, signal_rounding = 4):
        fig, ax = plt.subplots(2,4)
        fig.suptitle('%s Signal Overview: %s'%(self.target_df['symbol'][0], self.signal_column_name))

        # 0,0
        self.draw_signal_vs_fwdReturn_heatmap(ax[0,0], signal_rounding=signal_rounding)
        
        # 0,1        
        self.draw_signal_autocorrelation(ax[0,1])

        # 0,2 signal distribution 
        self.draw_signal_histogram(ax[0,2])

        # 0,3
        self.draw_signal_and_percentiles(ax[0,3])

        # 1,0
        self.draw_signal_decile_vs_fwdReturn_heatmap(ax[1,0], signal_rounding=signal_rounding)

        # 1,1 decile vs 'signal' column
        self.draw_violin_signal_and_deciles(ax[1,1])

        # 1,2
        # 1,3 plot underlying on log plot 
        self.draw_underlying_close(ax[1,3])

        # Link underlying and signal x-axis 
        ax[0,3].get_shared_x_axes().join(ax[0,3], ax[1,3])

        return fig

    def DEPRECATED_plotSignalReturnsHeatmap(self, signal_columnName, maxperiod_fwdreturns=100, signal_rounding=2):
        fig, ax = plt.subplots()
        fig.suptitle('Signal Returns Heatmap')
        self.drawSignalReturnsHeatmap(ax, maxperiod_fwdreturns, signal_columnName, signal_rounding=signal_rounding)
        return fig

    def DEPRECATED_drawSignalReturnsHeatmap(self, ax, signal_columnName, maxperiod_fwdreturns, signal_rounding = 2):        
        mean_fwdReturns = sa.bucketAndCalcSignalReturns(self.signal_df, signal_columnName, signal_rounding, maxperiod_fwdreturns)
        sns.heatmap(mean_fwdReturns, annot=False, cmap='RdYlGn', ax=ax)

        # plot formatting
        ax.set_xticklabels([int(x.get_text().replace('fwdReturns', '')) for x in ax.get_xticklabels()])
        ax.tick_params(axis='x', rotation=0)
        ax.set_title('%s vs. Fwd. Returns'%(signal_columnName))
        ax.set_ylabel(signal_columnName)
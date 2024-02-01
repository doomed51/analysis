"""
    Class that implements a crossover strategy. initialized with base_df, signal_df, and signal_column_name.
"""
import math

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from utils import utils_strategyAnalyzer as sa

class CrossoverStrategy:
    def __init__(self, base_df, signal_df, target_column_name, signal_column_name):
        
        self.target_column_name = target_column_name
        self.signal_column_name = signal_column_name
        self.base_df = base_df.reset_index()
        self.signal_df = signal_df.sort_index(ascending=True).reset_index()
        
        if 'close' in self.signal_df.columns:
            self.signal_df = self.signal_df.drop(columns=['close'])
        
        # add close from base to signal joining on date 
        self.signal_df = self.base_df[['date', 'close', 'symbol']].rename(
            columns={'symbol': 'symbol_underlying'}).merge(
                self.signal_df, on='date', how='inner')
        print(self.signal_df)


    def _align_base_and_signal_(self):
        # make sure date column in both dataframes is formatted the same 
        self.base_df['date'] = pd.to_datetime(self.base_df['date'])
        self.signal_df['date'] = pd.to_datetime(self.signal_df['date'])
        # only include dates that are in both base and signal
        self.base_df = self.base_df[self.base_df['date'].isin(self.signal_df['date'])]
        self.signal_df = self.signal_df[self.signal_df['date'].isin(self.base_df['date'])]



    def _calculateSignal(self, signal_df):
        # calculated as target column - signal column
        signal_df['signal'] = self.base_df[self.target_column_name] - signal_df[self.signal_column_name]
        # smooth signal column
        #signal_df['signal'] = signal_df['signal'].rolling(20).mean()        

        return signal_df

    def plotSignalOverview(self, signal_rounding = 4):
        fig, ax = plt.subplots(2,4)
        fig.suptitle('%s Signal Overview: %s'%(self.base_df['symbol'][0], self.signal_column_name))
        print(self.signal_column_name)

        # 0,0
        self.drawSignalReturnsHeatmap(ax[0,0], maxperiod_fwdreturns=100, signal_columnName=self.signal_column_name, signal_rounding=signal_rounding)
        
        # 0,1        
        autocorrelations = sa.calculateAutocorrelations(self.signal_df, self.signal_column_name)
        ax[0,1].stem(autocorrelations, linefmt='--')
        ax[0,1].set_title('%s Autocorrelation'%(self.signal_column_name))

        # 0,2 signal distribution 
        self._plot_histogram_with_pctile_vlines(ax=ax[0,2], data=self.signal_df, x_col_name=self.signal_column_name)

        # 0,3
        self.drawSignalAndBounds(ax[0,3])

        # 1,0
        self.signal_df['%s_decile'%(self.signal_column_name)] = pd.qcut(self.signal_df['%s_normalized'%(self.signal_column_name)], 10, labels=False)
        self.drawSignalReturnsHeatmap(ax[1,0], maxperiod_fwdreturns=100, signal_columnName='%s_decile'%(self.signal_column_name), signal_rounding=signal_rounding)
        # override title
        ax[1,0].set_title('%s Deciles vs. fwd returns'%(self.signal_column_name))

        # 1,1 decile vs 'signal' column
        sns.violinplot(data=self.signal_df, x='%s_decile'%(self.signal_column_name), y=self.signal_column_name, ax=ax[1,1])
        ax[1,1].set_title('%s Deciles vs. %s'%(self.signal_column_name, self.target_column_name))
        # format plot 
        ax[1,1].grid(True, which='both', axis='both', linestyle='-', alpha=0.2)
        ax[1,1].axvline(self.signal_df['%s_decile'%(self.signal_column_name)].iloc[-1], color='red', alpha=0.5)
        # add text label
        ax[1,1].text(self.signal_df['%s_decile'%(self.signal_column_name)].iloc[-1], ax[1,1].get_ylim()[1], 'current signal value: %s'%(round(self.signal_df['%s'%(self.signal_column_name)].iloc[-1], 5)), rotation=90, verticalalignment='top', fontsize=10)


        # 1,2

        # 1,3 plot underlying on log plot 
        ax[1,3].set_yscale('log')
        sns.lineplot(data=self.signal_df, x='date', y='close', ax=ax[1,3])
        ax[1,3].set_title('Underlying close')
        ax[1,3].grid(True, which='both', axis='both', linestyle='-', alpha=0.2)

        # Link underlying and signal x-axis 
        ax[0,3].get_shared_x_axes().join(ax[0,3], ax[1,3])

        return fig
    
    def _plot_histogram_with_pctile_vlines(self, ax, data, x_col_name, bins=50):
        # if index is not set as date, set it 
        if data.index.name != 'date':
            data = data.set_index('date')
        # set index to date
        sns.histplot(data=data, x=x_col_name, ax=ax, bins=bins)
        ax.set_title('%s Distribution'%(x_col_name))
        # vlines: pctile 10, pctile 90, mean 
        ax.axvline(data[x_col_name].quantile(0.95), color='red', alpha=0.5)
        ax.axvline(data[x_col_name].quantile(0.9), color='red', alpha=0.5)
        ax.axvline(data[x_col_name].quantile(0.1), color='red', alpha=0.5)
        ax.axvline(data[x_col_name].quantile(0.05), color='red', alpha=0.5)
        ax.axvline(data[x_col_name].mean(), color='black', alpha=0.5)

        # vline text labels 
        ax.text(data[x_col_name].quantile(0.95), ax.get_ylim()[1], '95th percentile: %s'%(round(data[x_col_name].quantile(0.95), 5)), rotation=90, verticalalignment='top', fontsize=12)
        ax.text(data[x_col_name].quantile(0.9), ax.get_ylim()[1], '90th percentile: %s'%(round(data[x_col_name].quantile(0.9), 5)), rotation=90, verticalalignment='top', fontsize=12)
        ax.text(data[x_col_name].quantile(0.1), ax.get_ylim()[1], '10th percentile: %s'%(round(data[x_col_name].quantile(0.1), 5)), rotation=90, verticalalignment='top', fontsize=12)
        ax.text(data[x_col_name].quantile(0.05), ax.get_ylim()[1], '5th percentile: %s'%(round(data[x_col_name].quantile(0.05), 5)), rotation=90, verticalalignment='top', fontsize=12)
        ax.text(data[x_col_name].mean(), ax.get_ylim()[1], 'mean: %s'%(round(data[x_col_name].mean(),5)), rotation=90, verticalalignment='top', fontsize=16, color='black')

    def plotSignalReturnsHeatmap(self, signal_columnName, maxperiod_fwdreturns=100, signal_rounding=2):
        fig, ax = plt.subplots()
        fig.suptitle('Signal Returns Heatmap')
        self.drawSignalReturnsHeatmap(ax, maxperiod_fwdreturns, signal_columnName, signal_rounding=signal_rounding)
        return fig

    def drawSignalReturnsHeatmap(self, ax, signal_columnName, maxperiod_fwdreturns, signal_rounding = 2):        
        mean_fwdReturns = sa.bucketAndCalcSignalReturns(self.signal_df, signal_columnName, signal_rounding, maxperiod_fwdreturns)
        sns.heatmap(mean_fwdReturns, annot=False, cmap='RdYlGn', ax=ax)

        # plot formatting
        ax.set_xticklabels([int(x.get_text().replace('fwdReturns', '')) for x in ax.get_xticklabels()])
        ax.tick_params(axis='x', rotation=0)
        ax.set_title('%s vs. Fwd. Returns'%(signal_columnName))
        ax.set_ylabel(signal_columnName)


    """
        Plots the base and signal timeseries on the provided axis
    """
    def drawBaseAndSignal(self, ax, drawPercentiles=True, **kwargs): 
        percentileWindow = kwargs.get('percentileWindow', 252)
        # set title
        ax.set_title('Underlying vs. Signal')

        # plot the base and signal timeseries 
        sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name], ax=ax, label=self.signal_column_name)
        # add percentile lines 
        if drawPercentiles:
            sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name].rolling(percentileWindow).quantile(0.8), ax=ax, label='90th percentile', color='red', alpha=0.3)
            sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name].rolling(percentileWindow).quantile(0.6), ax=ax, label='50th percentile', color='red', alpha=0.3)
            sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name].rolling(percentileWindow).quantile(0.4), ax=ax, label='10th percentile', color='red', alpha=0.3)
            sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name].rolling(percentileWindow).quantile(0.2), ax=ax, label='10th percentile', color='red', alpha=0.3)
        ax.legend(loc='upper left')

        # set style & format plot
        ax.grid(True, which='both', axis='both', linestyle='-', alpha=0.2)
        ax.axhline(0, color='grey', linestyle='-', alpha=0.5)
        ax.set_ylabel(self.target_column_name)
        ax.set_xlabel('date')

    """
        Plots the signal and percentile bounds on the provided axis
    """
    def drawSignalAndBounds(self, ax, upperbound = 0.95, lowerbound = 0.05):
        ax.set_title('%s with Percentile Bounds'%(self.signal_column_name))

        sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name], ax=ax, label='signal')

        # plot 252 day rolling quintile lines
        sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name].rolling(252).quantile(0.05), ax=ax, label='5th percentile', color='red', alpha=0.6)
        sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name].rolling(252).quantile(0.2), ax=ax, label='20th percentile', color='red', alpha=0.45)
        sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name].rolling(252).quantile(0.4), ax=ax, label='40th percentile', color='red', alpha=0.3)
        sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name].rolling(252).quantile(0.6), ax=ax, label='60th percentile', color='red', alpha=0.3)
        sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name].rolling(252).quantile(0.8), ax=ax, label='80th percentile', color='red', alpha=0.45)
        sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name].rolling(252).quantile(0.95), ax=ax, label='95th percentile', color='red', alpha=0.6)

        # format plot
        ax.grid(True, which='both', axis='both', linestyle='-', alpha=0.2)
        ax.axhline(0, color='grey', linestyle='-', alpha=0.5)
        #ax.legend(loc='upper left')

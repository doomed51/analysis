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
        self.base_df = base_df.reset_index(drop=True)
        self.signal_df = self._calculateSignal(signal_df).reset_index(drop=True)

    def _calculateSignal(self, signal_df):
        # calculated as target column - signal column
        signal_df['signal'] = self.base_df[self.target_column_name] - signal_df[self.signal_column_name]
        # smooth signal column
        #signal_df['signal'] = signal_df['signal'].rolling(20).mean()        

        return signal_df

    def plotSignalOverview(self): 
        signal_rounding = 3
        fig, ax = plt.subplots(2,2)
        fig.suptitle('%s Signal Overview'%(self.base_df['symbol'][0]))
        
        # plot signal returns heatmap
        self.drawSignalReturnsHeatmap(ax[0,0], maxperiod_fwdreturns=100, signal_columnName=self.signal_column_name, signal_rounding=signal_rounding)
        
        # plot the underlying, and the components of the signal
        self.drawBaseAndSignal(ax[0,1])
        #ax[0,1].legend(loc='upper left')
        
        # plot autocorrelation of signal 
        ##autocorrelations = sa.calculateAutocorrelations(self.signal_df, self.signal_column_name)
        ##ax[1,0].stem(autocorrelations, linefmt='--')
        ##ax[1,0].set_title('Signal Autocorrelation')

        # plot the signal against its percentile bounds
        self.drawSignalAndBounds(ax[1,1])
        # share x-axis iwht ax[0,1]
        ax[1,1].get_shared_x_axes().join(ax[1,1], ax[0,1])
        
        #signal_mod1 = self.signal_df.copy() 
        # change the signal column to be 1 if columnval >0, -1 if the columnval <0
        print('%s_normalized'%(self.signal_column_name))
        #self.signal_df['%s_normalized'%(self.signal_column_name)] = self.signal_df['%s_normalized'%(self.signal_column_name)].apply(lambda x: 1 if x > 0 else -1)
        # sort sma_normalized into 5 quintiles
        print(self.signal_df.tail())
        self.signal_df['%s_normalized'%(self.signal_column_name)] = pd.qcut(self.signal_df['%s_normalized'%(self.signal_column_name)], 5, labels=False)
        #self.signal_df['sma_normalized']=self.signal_df['sma_normalized'].apply(lambda x: 1 if x > 0 else -1)
        
        self.drawSignalReturnsHeatmap(ax[1,0], maxperiod_fwdreturns=100, signal_columnName='%s_normalized'%(self.signal_column_name), signal_rounding=signal_rounding)
        
        fig.tight_layout()
        print(fig)
        return fig
    
    def plotSignalReturnsHeatmap(self, signal_columnName, maxperiod_fwdreturns=100):
        fig, ax = plt.subplots()
        fig.suptitle('Signal Returns Heatmap')
        self.drawSignalReturnsHeatmap(ax, maxperiod_fwdreturns, signal_columnName)
        return fig

    def drawSignalReturnsHeatmap(self, ax, signal_columnName, maxperiod_fwdreturns, signal_rounding = 2):        
        mean_fwdReturns = sa.bucketAndCalcSignalReturns(self.signal_df, signal_columnName, signal_rounding, maxperiod_fwdreturns)
        sns.heatmap(mean_fwdReturns, annot=False, cmap='RdYlGn', ax=ax)

        # set title
        ax.set_title('Signal vs. Fwd. Returns')

    """
        Plots the base and signal timeseries on the provided axis
    """
    def drawBaseAndSignal(self, ax, drawPercentiles=True, **kwargs): 
        percentileWindow = kwargs.get('percentileWindow', 252)
        # set title
        ax.set_title('Underlying vs. Signal')

        # plot the base and signal timeseries 
        sns.lineplot(x=self.base_df['date'], y=self.base_df[self.target_column_name], ax=ax, label=self.target_column_name)
        sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name], ax=ax, label=self.signal_column_name)
        # add percentile lines 
        if drawPercentiles:
            sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name].rolling(percentileWindow).quantile(0.8), ax=ax, label='90th percentile', color='red', alpha=0.3)
            sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name].rolling(percentileWindow).quantile(0.6), ax=ax, label='50th percentile', color='red', alpha=0.3)
            sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name].rolling(percentileWindow).quantile(0.4), ax=ax, label='10th percentile', color='red', alpha=0.3)
            sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name].rolling(percentileWindow).quantile(0.2), ax=ax, label='10th percentile', color='red', alpha=0.3)
        ax.legend(loc='upper left')

        # plot the underlying 
        ax2 = ax.twinx()
        sns.lineplot(x=self.base_df['date'], y=self.base_df['close'], ax=ax2, color='black', label='close')
        ax2.set_yscale('log')

        # set style & format plot
        ax.grid(True, which='both', axis='both', linestyle='-', alpha=0.2)
        ax.axhline(0, color='grey', linestyle='-', alpha=0.5)
        ax.set_ylabel(self.target_column_name)
        ax.set_xlabel('date')
        ax2.set_ylabel('close')
        ax2.legend(loc='upper right')

    """
        Plots the signal and percentile bounds on the provided axis
    """
    def drawSignalAndBounds(self, ax, upperbound = 0.95, lowerbound = 0.05):
        # set title
        ax.set_title('Signal with Percentile Bounds')

        # plot signal on bottom plot
        #ax.plot(self.signal_df['date'], self.signal_df['signal'], label='signal')
        sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name], ax=ax, label='signal')

        # add rolling percentile lines
        #sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name].rolling(252).quantile(upperbound), ax=ax, label='90th percentile', color='red', alpha=0.3)
        #sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name].rolling(252).quantile(lowerbound), ax=ax, label='10th percentile', color='red', alpha=0.3)

        # plot 1000 day rolling quintile lines
        sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name].rolling(252).quantile(0.05), ax=ax, label='5th percentile', color='red', alpha=0.6)
        sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name].rolling(252).quantile(0.2), ax=ax, label='20th percentile', color='red', alpha=0.45)
        sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name].rolling(252).quantile(0.4), ax=ax, label='40th percentile', color='red', alpha=0.3)
        sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name].rolling(252).quantile(0.6), ax=ax, label='60th percentile', color='red', alpha=0.3)
        sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name].rolling(252).quantile(0.8), ax=ax, label='80th percentile', color='red', alpha=0.45)
        sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name].rolling(252).quantile(0.95), ax=ax, label='95th percentile', color='red', alpha=0.6)


        # add percentile labels
        #ax.text(self.signal_df['date'].iloc[0], self.signal_df[self.signal_column_name].quantile(upperbound), '%s percentile: %0.5f'%(int(upperbound*100), self.signal_df['signal'].quantile(upperbound)), color='red', fontsize=10)
        #ax.text(self.signal_df['date'].iloc[0], self.signal_df[self.signal_column_name].quantile(lowerbound), '%s percentile: %0.5f'%(int(lowerbound*100), self.signal_df['signal'].quantile(lowerbound)), color='red', fontsize=10)

        # format plot
        ax.grid(True, which='both', axis='both', linestyle='-', alpha=0.2)
        ax.axhline(0, color='grey', linestyle='-', alpha=0.5)
        ax.legend(loc='upper left')

        # plot undelying close on a secondary axis
        ax2 = ax.twinx()
        sns.lineplot(x=self.base_df['date'], y=self.base_df['close'], ax=ax2, color='black', label='%s close'%(self.base_df['symbol'][0]))
        ax2.set_yscale('log')
        ax2.legend(loc='upper right')

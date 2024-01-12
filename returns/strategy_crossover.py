"""
    Class that implements a crossover strategy. initialized with base_df, signal_df, and signal_column_name.
"""
import math

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

class CrossoverStrategy:
    def __init__(self, base_df, signal_df, target_column_name, signal_column_name):
        self.target_column_name = target_column_name
        self.signal_column_name = signal_column_name
        self.base_df = base_df
        self.signal_df = self._calculateSignal(signal_df)

    def _calculateSignal(self, signal_df):
        # calculated as target column - signal column
        signal_df['signal'] = self.base_df[self.target_column_name] - signal_df[self.signal_column_name]
        # smooth signal column
        signal_df['signal'] = signal_df['signal'].rolling(50).mean()        

        return signal_df

    def get_trades(self, entry_signal, exit_signal):
        # get entry and exit signals
        entry_signals = self.signal_df[self.signal_df[self.signal_column_name] == entry_signal]
        exit_signals = self.signal_df[self.signal_df[self.signal_column_name] == exit_signal]

        # create a list of trades
        trades = []
        for i in range(len(entry_signals)):
            entry_date = entry_signals.iloc[i]['date']
            exit_date = exit_signals.iloc[i]['date']
            trade = self.base_df[(self.base_df['date'] >= entry_date) & (self.base_df['date'] <= exit_date)]
            trades.append(trade)
        return trades

    def get_trade_returns(self, entry_signal, exit_signal):
        trades = self.get_trades(entry_signal, exit_signal)
        trade_returns = []
        for trade in trades:
            trade_returns.append(trade['logReturn'].sum())
        return trade_returns

    def plotSignalOverview(self): 
        fig, ax = plt.subplots(2,2, sharex=True)
        fig.suptitle('Signal Overview')
        
        # tight layout
        self.drawBaseAndSignal(ax[0,0])
        self.drawSignalAndBounds(ax[1,0])
        
        fig.tight_layout()

        return fig
    
    def plotSignalReturnsHeatmap(self, maxperiod_fwdreturns=100):
        fig, ax = plt.subplots()
        fig.suptitle('Signal Returns Heatmap')
        self.drawSignalReturnsHeatmap(ax, maxperiod_fwdreturns)
        return fig

    def drawSignalReturnsHeatmap(self, ax, maxperiod_fwdreturns):        
        signal_rounding = 4 # how much to bucket together the signal column
        signaldf = self.signal_df.copy()
        # drop rows where signal is nan
        signaldf.dropna(subset=['signal'], inplace=True)
        # add fwdreturn column for each fwdreturn period
        for i in range(1, maxperiod_fwdreturns+1):
            if 'fwdReturns%s'%(i) in signaldf.columns: # skip if col exists
                continue
            signaldf['fwdReturns%s'%(i)] = signaldf['close'].pct_change(i).shift(-i)
        # x100 and round up to 2 decimals the signal column
        signaldf['signal_normalized'] = signaldf['signal'].apply(lambda x: round(x, signal_rounding))
        
        unique_signals = signaldf['signal_normalized'].unique()
        # 90th percentile of unique signals
        p95 = signaldf['signal_normalized'].quantile(0.7)
        p5 = signaldf['signal_normalized'].quantile(0.2)
        # create a dataframe with the unique signals as the index
        df = pd.DataFrame(index=unique_signals)

        # for each fwdreturns column, get the avgfwdreturns for each unique signal
        for i in range(1, maxperiod_fwdreturns+1):
            df['fwdReturns%s'%(i)] = signaldf.groupby('signal_normalized')['fwdReturns%s'%(i)].mean()
        df.sort_index(inplace=True, ascending=False)

        sns.heatmap(df, annot=False, cmap='RdYlGn', ax=ax)
        # add percentile hlines of signal 
        ax.axhline(p95, color='black', linestyle='-', alpha=0.3)
        ax.axhline(p5, color='black', linestyle='-', alpha=0.3)


        #ax.set_title('Signal Returns Heatmap')


    """
        Plots the base and signal timeseries on the provided axis
    """
    def drawBaseAndSignal(self, ax): 
        # set title
        ax.set_title('Base vs. Signal')

        # plot the base and signal timeseries 
        sns.lineplot(x=self.base_df['date'], y=self.base_df[self.target_column_name], ax=ax, label=self.target_column_name)
        sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name], ax=ax, label=self.signal_column_name)

        # plot the underlying 
        ax2 = ax.twinx()
        sns.lineplot(x=self.base_df['date'], y=self.base_df['close'], ax=ax2, color='black', label='close')

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
        sns.lineplot(x=self.signal_df['date'], y=self.signal_df['signal'], ax=ax, label='signal')

        # plot percentile bounds
        ax.axhline(self.signal_df['signal'].quantile(upperbound), color='red', linestyle='-', alpha=0.4)
        ax.axhline(self.signal_df['signal'].quantile(lowerbound), color='red', linestyle='-', alpha=0.4)

        # add percentile labels
        ax.text(self.signal_df['date'].iloc[0], self.signal_df['signal'].quantile(upperbound), '%s percentile: %0.5f'%(int(upperbound*100), self.signal_df['signal'].quantile(upperbound)), color='red', fontsize=10)
        ax.text(self.signal_df['date'].iloc[0], self.signal_df['signal'].quantile(lowerbound), '%s percentile: %0.5f'%(int(lowerbound*100), self.signal_df['signal'].quantile(upperbound)), color='red', fontsize=10)

        # format plot
        ax.grid(True, which='both', axis='both', linestyle='-', alpha=0.2)
        ax.axhline(0, color='grey', linestyle='-', alpha=0.5)
        ax.legend(loc='upper left')


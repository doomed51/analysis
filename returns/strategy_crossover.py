"""
    Class that implements a crossover strategy. initialized with base_df, signal_df, and signal_column_name.
"""
import matplotlib.pyplot as plt

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
    """
        Plots the base and signal timeseries on the provided axis
    """
    def drawBaseAndSignal(self, ax): 
        # set title
        ax.set_title('Base vs. Signal')

        # plot the base and signal timeseries 
        ax.plot(self.base_df['date'], self.base_df[self.target_column_name], label=self.target_column_name)
        ax.plot(self.signal_df['date'], self.signal_df[self.signal_column_name], label=self.signal_column_name)

        # plot the underlying 
        ax2 = ax.twinx()
        ax2.plot(self.base_df['date'], self.base_df['close'], color='black', label='close')

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
        ax.plot(self.signal_df['date'], self.signal_df['signal'], label='signal')

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


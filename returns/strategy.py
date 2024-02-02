"""
    Base class for defining a strategy consisting of: 
    - a symbol : str 
    - a signal : str column name of the signal for the strat 
    - a signal dataframe : pd.DataFrame containing the signal column 
    - a target: str column name of what the signal is targeting (e.g. sma crossover) 
    - a target dataframe : pd.DataFrame containing the col. being targeted by the signal 
"""
import pandas as pd 
import seaborn as sns

from utils import utils_strategyAnalyzer as sa

class Strategy:
    def __init__(self, symbol, signal, signal_df, target, target_df):
        self.symbol = symbol
        self.signal_column_name = signal
        self.signal_df = signal_df.sort_index(ascending=True).reset_index()
        self.target_column_name = target
        self.target_df = target_df

    """
        Makes sure date column in target and signal are formatted the same 
        Only includes dates that are in target and signal
    """
    def _align_target_and_signal_(self):
        self.target_df['date'] = pd.to_datetime(self.target_df['date'])
        self.signal_df['date'] = pd.to_datetime(self.signal_df['date'])

        self.target_df = self.target_df[self.target_df['date'].isin(self.signal_df['date'])]
        self.signal_df = self.signal_df[self.signal_df['date'].isin(self.target_df['date'])]

    """
        Plots autocorrelation of the signal 
    """
    def draw_signal_autocorrelation(self, ax, max_lag=100):
        autocorrelations = sa.calculateAutocorrelations(self.signal_df, self.signal_column_name, max_lag)
        ax.stem(autocorrelations, linefmt='--')
        ax.set_title('Autocorrelation of %s'%(self.signal_column_name), fontsize=14, fontweight='bold')
        ax.set_xlabel('lag')
        ax.set_ylabel('autocorrelation')
        ax.grid(True, which='both', axis='both', linestyle='-', alpha=0.2)

    def draw_signal_histogram(self, ax, drawPercetiles=True, **kwargs):
        bins = kwargs.get('bins', 50)
        # set title
        ax.set_title('Distribution of %s'%(self.signal_column_name), fontsize=14, fontweight='bold')

        # plot the histogram of the signal 
        sns.histplot(self.signal_df[self.signal_column_name], ax=ax, kde=True, bins=bins)
        if drawPercetiles:
            ax.axvline(self.signal_df[self.signal_column_name].quantile(0.01), color='red', linestyle='--', alpha=0.5)
            ax.axvline(self.signal_df[self.signal_column_name].quantile(0.05), color='red', linestyle='--', alpha=0.5)
            ax.axvline(self.signal_df[self.signal_column_name].quantile(0.1), color='red', linestyle='--', alpha=0.5)
            ax.axvline(self.signal_df[self.signal_column_name].quantile(0.5), color='brown', linestyle='--', alpha=0.5)
            ax.axvline(self.signal_df[self.signal_column_name].quantile(0.9), color='red', linestyle='--', alpha=0.5)
            ax.axvline(self.signal_df[self.signal_column_name].quantile(0.95), color='red', linestyle='--', alpha=0.5)
            ax.axvline(self.signal_df[self.signal_column_name].quantile(0.99), color='red', linestyle='--', alpha=0.5)

            # add text labels: <percentile> : <value>
            ax.text(self.signal_df[self.signal_column_name].quantile(0.01), ax.get_ylim()[1], '1st: %.5f'%(round(self.signal_df[self.signal_column_name].quantile(0.01), 5)), fontsize=16, rotation=90, verticalalignment='top', color='black')
            ax.text(self.signal_df[self.signal_column_name].quantile(0.05), ax.get_ylim()[1], '5th: %.5f'%(round(self.signal_df[self.signal_column_name].quantile(0.05),5)), fontsize=16, rotation=90, verticalalignment='top', color='black')
            ax.text(self.signal_df[self.signal_column_name].quantile(0.1), ax.get_ylim()[1], '10th: %.5f'%(round(self.signal_df[self.signal_column_name].quantile(0.1),5)), fontsize=16, rotation=90, verticalalignment='top', color='black')
            ax.text(self.signal_df[self.signal_column_name].quantile(0.5), ax.get_ylim()[1], '50th: %.5f'%(round(self.signal_df[self.signal_column_name].quantile(0.5),5)), fontsize=16, rotation=90, verticalalignment='top', color='black')
            ax.text(self.signal_df[self.signal_column_name].quantile(0.9), ax.get_ylim()[1], '90th: %.5f'%(round(self.signal_df[self.signal_column_name].quantile(0.9),5)), fontsize=16, rotation=90, verticalalignment='top', color='black')
            ax.text(self.signal_df[self.signal_column_name].quantile(0.95), ax.get_ylim()[1], '95th: %.5f'%(round(self.signal_df[self.signal_column_name].quantile(0.95),5)), fontsize=16, rotation=90, verticalalignment='top', color='black')
            ax.text(self.signal_df[self.signal_column_name].quantile(0.99), ax.get_ylim()[1], '99th: %.5f'%(round(self.signal_df[self.signal_column_name].quantile(0.99),5)), fontsize=16, rotation=90, verticalalignment='top', color='black')

        # additional plot formatting
        ax.grid(True, which='both', axis='both', linestyle='-', alpha=0.2)
        ax.set_ylabel('count')
        ax.set_xlabel(self.signal_column_name)

    """
        Plots the base and signal timeseries on the provided axis
    """
    def draw_signal_and_percentiles(self, ax, drawPercentiles=True, **kwargs): 
        precentile_rolling_window = kwargs.get('percentileWindow', 252)
        # set title
        ax.set_title('Signal and Percentiles of %s'%(self.signal_column_name), fontsize=14, fontweight='bold')

        # plot the base and signal timeseries 
        sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name], ax=ax, label=self.signal_column_name)
        # add percentile lines 
        if drawPercentiles:
            sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name].rolling(precentile_rolling_window).quantile(0.99), ax=ax, label='99th percentile', color='red', alpha=0.6)
            sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name].rolling(precentile_rolling_window).quantile(0.95), ax=ax, label='95th percentile', color='red', alpha=0.3)
            sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name].rolling(precentile_rolling_window).quantile(0.9), ax=ax, label='90th percentile', color='red', alpha=0.3)
            sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name].rolling(precentile_rolling_window).quantile(0.8), ax=ax, label='80th percentile', color='red', alpha=0.3)
            #sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name].rolling(precentile_rolling_window).quantile(0.7), ax=ax, label='70th percentile', color='red', alpha=0.3)
            #sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name].rolling(precentile_rolling_window).quantile(0.6), ax=ax, label='60th percentile', color='red', alpha=0.2)
            sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name].rolling(precentile_rolling_window).quantile(0.5), ax=ax, label='50th percentile', color='brown', alpha=0.5)
            #sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name].rolling(precentile_rolling_window).quantile(0.4), ax=ax, label='40th percentile', color='red', alpha=0.2)
            #sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name].rolling(precentile_rolling_window).quantile(0.3), ax=ax, label='30th percentile', color='red', alpha=0.3)
            sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name].rolling(precentile_rolling_window).quantile(0.2), ax=ax, label='20th percentile', color='red', alpha=0.3)
            sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name].rolling(precentile_rolling_window).quantile(0.1), ax=ax, label='10th percentile', color='red', alpha=0.3)
            sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name].rolling(precentile_rolling_window).quantile(0.05), ax=ax, label='5th percentile', color='red', alpha=0.3)
            sns.lineplot(x=self.signal_df['date'], y=self.signal_df[self.signal_column_name].rolling(precentile_rolling_window).quantile(0.01), ax=ax, label='1st percentile', color='red', alpha=0.6)

        # additional plot formatting
        ax.axhline(0, color='grey', linestyle='-', alpha=0.5)
        ax.grid(True, which='both', axis='both', linestyle='-', alpha=0.2)
        ax.legend(loc='upper left')
        ax.set_ylabel(self.target_column_name)
        ax.set_xlabel('date')
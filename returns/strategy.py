"""
    Base class for defining a strategy consisting of: 
    - a symbol : str 
    - a signal : str column name of the signal for the strat 
    - a signal dataframe : pd.DataFrame containing the signal column 
    - a target: str column name of what the signal is targeting (e.g. sma crossover) 
    - a target dataframe : pd.DataFrame containing the col. being targeted by the signal 
"""
import config
import pandas as pd 
import seaborn as sns
import interface_localDB as db

from utils import utils_strategyAnalyzer as sa

class Strategy:
    def __init__(self, symbol, signal, signal_df, target, target_df):
        self.symbol = symbol
        self.signal_column_name = signal
        self.signal_df = signal_df.sort_index(ascending=True).reset_index()
        self.target_column_name = target
        self.target_df = target_df
        self.underlying_pxhistory = None

    """
        Makes sure date column in target and signal are formatted the same 
        Only includes dates that are in target and signal
    """
    def _align_target_and_signal_(self):
        self.target_df['date'] = pd.to_datetime(self.target_df['date'])
        self.signal_df['date'] = pd.to_datetime(self.signal_df['date'])

        self.target_df = self.target_df[self.target_df['date'].isin(self.signal_df['date'])]
        self.signal_df = self.signal_df[self.signal_df['date'].isin(self.target_df['date'])]

    # load underlying history from db 
    def _load_underlying_pxhistory(self):
        with db.sqlite_connection(config.dbname_stock) as conn:
            return db.getPriceHistory(conn, self.symbol, '1day')

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

    """
        Plots distribution of the signal with percentiles 
    """
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
        Plots the violin plot of the signal vs it's deciles
    """
    def draw_violin_signal_and_deciles(self, ax, **kwargs):
        # plot the violin plot 
        sns.violinplot(x=self.signal_df['%s_decile'%(self.signal_column_name)], y=self.signal_df[self.signal_column_name], ax=ax)
        
        # additional plot formatting
        ax.set_title('Distribution of %s vs Deciles'%(self.signal_column_name), fontsize=14, fontweight='bold')
        ax.set_xlabel('%s decile'%(self.signal_column_name))
        ax.set_ylabel(self.signal_column_name)
        ax.grid(True, which='both', axis='both', linestyle='-', alpha=0.2)
        ax.axvline(self.signal_df['%s_decile'%(self.signal_column_name)].iloc[-1], color='red', alpha=0.5)
        ax.text(self.signal_df['%s_decile'%(self.signal_column_name)].iloc[-1], ax.get_ylim()[1], 'current %s value: %s'%(self.signal_column_name, round(self.signal_df['%s'%(self.signal_column_name)].iloc[-1], 5)), rotation=90, verticalalignment='top', fontsize=10)

    """
        Plots the heatmap of the signal's decile vs fwd returns
    """
    def draw_signal_decile_vs_fwdReturn_heatmap(self, ax, maxperiod_fwdreturns=35, signal_rounding=4):
        
        signal_colname = '%s_decile'%(self.signal_column_name)
        # if the column '%s_decile'%(self.signal_column_name) doesn't exist, create it
        if signal_colname not in self.signal_df.columns:
            self.signal_df['%s_decile'%(self.signal_column_name)] = pd.qcut(self.signal_df['%s_normalized'%(self.signal_column_name)], 10, labels=False)
        # calculate the heatmap 
        heatmap = sa.bucketAndCalcSignalReturns(self.signal_df, signal_colname, maxperiod_fwdreturns=maxperiod_fwdreturns)
        # plot the heatmap 
        sns.heatmap(heatmap, ax=ax, cmap='RdYlGn', center=0, annot=False, fmt='.2f')
        # set title
        ax.set_title('%s decile vs. fwd returns'%(self.signal_column_name), fontsize=14, fontweight='bold')
        # additional plot formatting
        ax.set_xlabel('fwd returns')
        ax.set_ylabel('%s decile'%(self.signal_column_name))

    def draw_signal_vs_fwdReturn_heatmap(self, ax, maxperiod_fwdreturns=35, signal_rounding=4):
        # calculate the heatmap 
        heatmap = sa.bucketAndCalcSignalReturns(self.signal_df, self.signal_column_name, maxperiod_fwdreturns=maxperiod_fwdreturns, signal_rounding=signal_rounding)
        # plot the heatmap 
        sns.heatmap(heatmap, ax=ax, cmap='RdYlGn', center=0, annot=False, fmt='.2f')

        # additional plot formatting
        ax.set_title('%s vs. fwd returns'%(self.signal_column_name), fontsize=14, fontweight='bold')
        ax.set_xticklabels([int(x.get_text().replace('fwdReturns', '')) for x in ax.get_xticklabels()])
        ax.set_xlabel('fwd returns')
        ax.set_ylabel(self.signal_column_name)

    def draw_underlying_close(self, ax):
        ax.set_yscale('log')
        sns.lineplot(data=self.underlying_pxhistory, x='date', y='close', ax=ax)
        ax.set_title('%s close'%(self.symbol))
        ax.grid(True, which='both', axis='both', linestyle='-', alpha=0.2)

    """
        Plots the base and signal timeseries on the provided axis
    """
    def draw_signal_and_percentiles(self, ax, drawPercentiles=True, **kwargs): 
        # max rolling window is entire dataset 
        precentile_rolling_window = kwargs.get('percentileWindow', 400)
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
        # hide legend
        ax.get_legend().remove()
        ax.set_ylabel(self.target_column_name)
        ax.set_xlabel('date')
    
    """
        Plots the signals negative & positive persistence. That is, when the signal crosses 0, how long does it stay positive or negative. Autocorrelation of signal where signal < 0, and signal > 0. 
    """
    def draw_crossover_negative_positive_persistence(self, ax, **kwargs):
        print(self.signal_df)
        
        # set title
        ax.set_title('Crossover Negative & Positive Persistence of %s'%(self.signal_column_name), fontsize=14, fontweight='bold')
        signal_negative = pd.DataFrame()
        # plot autocorrelation of signal where signal < 0
        signal_negative['signal_negative'] = self.signal_df[self.signal_column_name].apply(lambda x: x if x < 0 else None)
        signal_negative = signal_negative.dropna()

        autocorrelations = sa.calculateAutocorrelations(signal_negative, 'signal_negative', max_lag=100)
        ax.stem(autocorrelations, linefmt='--', label='signal < 0')

        signal_positive = pd.DataFrame()
        # plot autocorrelation of signal where signal > 0
        signal_positive['signal_positive'] = self.signal_df[self.signal_column_name].apply(lambda x: x if x > 0 else None)
        signal_positive = signal_positive.dropna()
        autocorrelations2 = sa.calculateAutocorrelations(signal_positive, 'signal_positive', max_lag=100)
        ax.stem(autocorrelations2, linefmt='-', label='signal > 0')

        #add legend 
        ax.legend()

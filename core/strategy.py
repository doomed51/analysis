"""
    Base class for analyzing various characteristics of a strategy defined by: 
    - a symbol : str of the underlying 
    - a signal : str column name of the signal generated by the strat 
    - a signal dataframe: pd.DataFrame containing a date, and signal column 
    - a target: str column name of what the singal is a function of  
    - a target dataframe : pd.DataFrame containing the col. being targeted by the signal 
"""
import config
import matplotlib.pyplot as plt
import pandas as pd 
import seaborn as sns
from interface import interface_localDB as db
from utils import utils_strategyAnalyzer as sa
from utils import utils as ut

class Strategy:
    """

        Args:
            symbol (str): The symbol of the asset.

        Attributes:
            pxHistory (dataframe): The price history of the asset with all desired signals or indicators.

    """
    def __init__(self, name, symbol, interval='1day', signal_name='close'):
        self.name = name 
        self.symbol = symbol
        self.interval = interval
        self.signal_name = signal_name
        self.pxhistory = self._load_pxhistory(symbol=self.symbol, interval=self.interval)
        self._calc_zscore('close')

        sns.set_style('darkgrid')

    # load underlying history from db 
    def _load_pxhistory(self, symbol, interval):
        with db.sqlite_connection(config.dbname_stock) as conn:
             return db.getPriceHistory(conn, symbol, interval)
    
    ######### COLUMN CALCULATION FUNCTIONS 
    """"
        Behold, herein lie lambda functions generating the required calculated columns for the strategy  
    """

    def _calc_rolling_percentile_for_col(self, target_col_name = 'close', rollingWindow=252):
        self.pxhistory['%s_percentile'%(target_col_name)] = self.pxhistory[target_col_name].rolling(rollingWindow).apply(lambda x: pd.qcut(x, 10, labels=False, duplicates='drop')[-1], raw=True)
        self._calc_zscore('%s_percentile'%(target_col_name))

    def _calc_zscore(self, colname, rollingWindow=252, _pxHistory = None): 
        """
            Calculate the z-score of a column.
            Params: 
                colname: str column name to calculate z-score on
                rollingWindow: int rolling window to calculate z-score on. Settingto 0 uses entire population 
                _pxHistory: pd.DataFrame to calculate z-score on. Default is None, which uses the objects default pxhistory
        """
        if _pxHistory is None:
            if rollingWindow == 0:
                self.pxhistory['%s_zscore'%(colname)] = self.pxhistory[colname] - self.pxhistory[colname].mean() / self.pxhistory[colname].std()
            else: 
                self.pxhistory['%s_zscore'%(colname)] = self.pxhistory[colname].rolling(rollingWindow).apply(lambda x: (x[-1] - x.mean()) / x.std(), raw=True)
        else:
            _pxHistory['%s_zscore'%(colname)] = _pxHistory[colname] - _pxHistory[colname].mean() / _pxHistory[colname].std()
    
    def _calc_ntile(self, numBuckets, colname, _pxHistory = None):
        if _pxHistory is None:
            self.pxhistory['%s_ntile'%(colname)] = pd.qcut(self.pxhistory[colname], numBuckets, labels=False, duplicates='drop')
        else:
            _pxHistory['%s_ntile'%(colname)] = pd.qcut(_pxHistory[colname], numBuckets, labels=False, duplicates='drop')
    
    def _calc_deciles(self, colname, _pxHistory = None):
        self._calc_ntile(10, colname, _pxHistory)
        self.pxhistory.rename(columns={'%s_ntile'%(colname): '%s_decile'%(colname)}, inplace=True)
    
    def _calc_percentiles(self, colname, _pxHistory = None, lookback=252):
        if _pxHistory is None:
            self.pxhistory['%s_percentile'%(colname)] = self.pxhistory[colname].rolling(lookback).apply(lambda x: pd.qcut(x, 100, labels=False, duplicates='drop')[-1], raw=True)
        else:
            _pxHistory['%s_percentile'%(colname)] = _pxHistory[colname].rolling(lookback).apply(lambda x: pd.qcut(x, 100, labels=False, duplicates='drop')[-1], raw=True)

    def _calc_log_fwd_return(self, maxperiod=20, colname='close'):
        for i in range(1, maxperiod+1):
            if '%s_fwdReturns%s'%(colname, i) in self.pxhistory.columns:
                continue
            self.pxhistory['%s_logFwdReturns%s'%(colname, i)] = self.pxhistory[colname].pct_change(i).shift(-i).apply(lambda x: np.log(1+x))

    def _calc_fwd_returns(self, maxperiod_fwdreturns=20, colname='close'):
        for i in range (1, maxperiod_fwdreturns+1):
            if '%s_fwdReturns%s'%(colname, i) in self.pxhistory.columns:
                continue
            self.pxhistory['%s_fwdReturns%s'%(colname, i)] = self.pxhistory[colname].pct_change(i).shift(-i)

    ######### PLOTTING FUNCTIONS 
    ##########
    ## Behold, herein lie generic plotting functions. 
    ## They draw plots on the provided axis.  
    
    def draw_distribution(self, ax, y='close', drawPercetiles=True, **kwargs):
            bins = kwargs.get('bins', 50)
            percentiles_to_plot = kwargs.get('percentiles_to_plot', [0.01, 0.05, 0.1, 0.5, 0.9, 0.95, 0.99])
            # set title
            ax.set_title('Distribution of %s'%(y), fontsize=14, fontweight='bold')

            # plot the histogram of the signal 
            sns.histplot(self.pxhistory[y], ax=ax, kde=True, bins=bins)
            if drawPercetiles:
                #for p in percentiles_to_plot:
                #    ax.axvline(self.pxhistory[y].quantile(p), color='grey', linestyle='--', alpha=0.5)
                #    ax.text(self.pxhistory[y].quantile(p), ax.get_ylim()[1], '%.2fth: %.5f'%(p*100, round(self.pxhistory[y].quantile(p), 5)), fontsize=11, rotation=90, verticalalignment='top', color='grey', alpha=0.7)
                for p in percentiles_to_plot:
                    ax.axvline(p, color='grey', linestyle='--', alpha=0.5)
                    ax.text(p, ax.get_ylim()[1], '%.5f'%(round(p, 5)), fontsize=11, rotation=90, verticalalignment='top', color='grey', alpha=0.7)
            
            # plot last value of signal 
            ax.axvline(self.pxhistory[y].iloc[-1], color='red', linestyle='--', alpha=0.5)
            ax.text(self.pxhistory[y].iloc[-1], ax.get_ylim()[1], 'Last: %.5f'%(self.pxhistory[y].iloc[-1]), fontsize=11, rotation=90, verticalalignment='top', color='red', alpha=0.7)

            # plot the mean 
            ax.axvline(self.pxhistory[y].mean(), color='blue', linestyle='--', alpha=0.5, label='mean')
            #ax.text(self.pxhistory[y].mean(), ax.get_ylim()[1], 'Mean: %.5f'%(self.pxhistory[y].mean()), fontsize=11, rotation=90, verticalalignment='top', color='blue', alpha=0.7)

            # additional plot formatting
            ax.grid(True, which='both', axis='both', linestyle='-', alpha=0.2)
            ax.set_ylabel('count')
            ax.set_xlabel(y)
            ax.legend()

    def draw_heatmap_signal_returns(self, ax, y='logReturn_decile', maxperiod_fwdreturns=20):
        # calculate the heatmap 
        heatmap = sa.bucketAndCalcSignalReturns(self.pxhistory, y, signal_rounding=1, maxperiod_fwdreturns=maxperiod_fwdreturns)

        # for the columns with 'fwdReturns' in the name, remove it 
        heatmap.columns = [col.replace('fwdReturns', '') for col in heatmap.columns]

        # plot the heatmap
        sns.heatmap(heatmap, ax=ax, cmap='RdYlGn', center=0, annot=False, fmt='.2f')

        # plot formatting
        ax.set_title('%s vs. Forward Returns'%(y), fontsize=14, fontweight='bold')
        ax.set_ylabel(y)

    def draw_lineplot(self, ax, y='close', y_alt=None, **kwargs):
        """
        Draw a line plot on the given axes.

        Parameters:
        - ax: The axes object to draw the plot on.
        - y: The column name to use as the y-axis data. Default is 'close'.
        - y_alt: The column name to use as an alternate y-axis data. Default is None.
        - **kwargs: Additional keyword arguments for customization.

        Keyword Arguments:
        - hlines_to_plot: The list of additional levels to plot.
        - percentile_source: The column name to use as the source for percentiles. Default is the value of y.
        - n_periods_to_plot: The number of previous periods to plot. Default is 0 (plot all periods).

        Returns:
        None
        """
        hlines_to_plot = kwargs.get('hlines_to_plot', [])
        n_periods_to_plot = kwargs.get('n_periods_to_plot', 0)

        # (optional) slice the pxhistory to only plot the last n periods
        if n_periods_to_plot>0:
            _pxhistory = self.pxhistory.tail(n_periods_to_plot)
        else:
            _pxhistory = self.pxhistory
        # draw the lineplot 
        sns.lineplot(x=_pxhistory['date'], y=_pxhistory[y], ax=ax, color='blue', alpha=0.7, label=y)
        
        # (optional) draw alternate lineplot 
        if y_alt:
            ax2 = ax.twinx()
            sns.lineplot(x=_pxhistory['date'], y=_pxhistory[y_alt], ax=ax2, color='black', alpha=0.3)
        
        # (optional) draw percentiles 
        if hlines_to_plot:
            for p in hlines_to_plot:
                ax.axhline(p, color='blue', linestyle='--', alpha=0.3)
                ax.text(ax.get_xlim()[1], p, '%.5f'%(p), fontsize=9, horizontalalignment='left', color='blue', alpha=0.7)

        # format plot  
        ax.set_title('%s'%(y), fontsize=14, fontweight='bold')
        ax.grid(True, which='both', axis='both', linestyle='-', alpha=0.2)
        ax.set_ylabel(y)
        ax.set_xlabel('date')
        ax.legend()

    def draw_autocorrelation(self, ax, y='close', max_lag=100):
        """
        Draw the autocorrelation plot for a given column.

        Parameters:
        - ax (matplotlib.axes.Axes): The axes on which to draw the plot.
        - y (str): The column name of the time series to analyze. Default is 'close'.
        - max_lag (int): The maximum lag to consider for autocorrelation. Default is 100.

        Returns:
        None
        """
        autocorrelations = sa.calculateAutocorrelations(self.pxhistory, y, max_lag)
        ax.stem(autocorrelations, linefmt='--')
        
        ax.set_title('Autocorrelation (%s-%s)'%(self.symbol, y), fontsize=14, fontweight='bold')
        ax.set_ylabel('autocorrelation')
        ax.set_xlabel('lag')

    def draw_barplot(self, ax, y, x, **kwargs):
        """
        Draw a bar plot on the given axes.

        Parameters:
        - ax (matplotlib.axes.Axes): The axes object to draw the plot on.
        - y (str): The column name to use as the y-axis data.
        - x (str): The column name to use as the x-axis data.

        Keyword Arguments:
        - hue: The column name to use as the hue. Default is None.
        - order: The order of the x-axis categories. Default is None.
        - palette: The color palette to use. Default is 'viridis'.

        Returns:
        None
        """
        hue = kwargs.get('hue', None)
        order = kwargs.get('order', None)
        palette = kwargs.get('palette', 'viridis')

        sns.barplot(x=x, y=y, data=self.pxhistory, ax=ax, hue=hue, order=order, palette=palette)
        ax.set_title('%s vs. %s'%(y, x), fontsize=14, fontweight='bold')
        ax.set_ylabel(y)
        ax.set_xlabel(x)

    ##########
    ## BEHOLD, herein lie generic dashboard plotting functions. 
    ## They draw a combination of plots and return a figure. 

    def plot_grid_signal_decile_returns(self, colname_y='logReturn_decile', maxperiod_fwdreturns=20):
        """
        Plot a grid of bar plots showing some bucketed signal vs. mean forward returns over different periods. Works best with a signal bucketed in deciles. 

        Parameters:
        - colname_y (str): The column name to use for the y-axis of the bar plots. Default is 'logReturn_decile'.
        - maxperiod_fwdreturns (int): The maximum number of periods to calculate forward returns for. Default is 20.

        Returns:
        - fig: The matplotlib figure object containing the grid of bar plots.
        """
        self._calc_fwd_returns(maxperiod_fwdreturns=maxperiod_fwdreturns)
        # print the number of unique values for colname_y
        if self.pxhistory[colname_y].nunique() > 30:
            self._calc_deciles(colname_y)
            colname_y = '%s_decile'%(colname_y)

        num_columns = 5
        num_rows = maxperiod_fwdreturns // num_columns
        fig, ax = plt.subplots(num_rows, num_columns, figsize=(10, 5), sharey=True)
        
        # row, col = 0, 0
        # i=5
        # ntile_grouped = self.pxhistory.groupby('%s'%(colname_y)).agg({'close_fwdReturns%s'%(i): 'mean'})
        # sns.barplot(x=ntile_grouped.index, y='close_fwdReturns%s'%(i), data=ntile_grouped, ax=ax[row, col])
        # ax[row, col].set_title('FwdReturn %s'%(i))

        
        for i in range(1, maxperiod_fwdreturns+1):
            if i > maxperiod_fwdreturns:
                break
            row = (i-1) // num_columns
            col = (i-1) % num_columns

            #group by ntile and calculate mean of fwdReturns[i]
            ntile_grouped = self.pxhistory.groupby('%s'%(colname_y)).agg({'close_fwdReturns%s'%(i): 'mean'})
            sns.barplot(x=ntile_grouped.index, y='close_fwdReturns%s'%(i), data=ntile_grouped, ax=ax[row, col])
            ax[row, col].set_title('FwdReturn %s'%(i))

        return fig

    def plot_heatmap_grid(self, signal_col_name, lookback_periods=[]):
        """
            Useful when determining an appropriate lookback period for a rolling-winddow based signal. Plots a grid of heatmaps for the specified lookback periods.
        """

        # determine the number of rows and columns for the grid
        num_columns = 5
        # num_rows = len(lookback_periods) // num_columns
        num_rows = (len(lookback_periods) + num_columns - 1) // num_columns
        if num_rows == 0: num_rows = 1
        
        # if lookback_perdiod-signal_col_name does not exist already, create it 
        for lp in lookback_periods:
            if not '%s_%s'%(signal_col_name, lp) in self.pxhistory.columns:
                self.pxhistory['%s_%s'%(signal_col_name, lp)] = self.pxhistory[signal_col_name].rolling(lp).mean()
        
        # create the figure and axes
        fig, ax = plt.subplots(nrows=num_rows, ncols=num_columns, figsize=(10, 5))
        
        import numpy as np
        if num_rows == 1:
            ax = np.array([ax])
        if num_columns == 1:
            ax = ax[:, None]

        # iterate through the lookback periods and plot the heatmaps
        for i, lp in enumerate(lookback_periods):
            row = i // num_columns
            col = i % num_columns
            # _ax = ax[row, col]
            # sns.heatmap(self.pxhistory[['%s_%s'%(signal_col_name, lp)]], ax=ax[row, col], cmap='RdYlGn', center=0, annot=False, fmt='.2f')
            self.draw_heatmap_signal_returns(ax[row, col], y='%s_%s'%(signal_col_name, lp))
            # ax[row, col].set_title('%s_%s'%(signal_col_name, lp))

        return fig
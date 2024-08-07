from core import strategy as st
from core import indicators
from backtests import bt_vix3m_vix_ratio as btsts 

import ffn 
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

class StrategyVixAndVol(st.Strategy):
    """
    Analysis of a volatility forecast based on vix3m/vix ratio, and vvix percentiles.

    Args:
        interval (enum:interval): interval of price history data.
        signal_name (str): signal column name in price history data.


    Attributes:
        pxHistory (dataframe): The price history of the asset(VIX) with all desired 
        signals+ indicators.
        [OPTIONAL]
        ratio_moving_average_shortperiod (int): period of short moving average for vix3m/vix ratio.
        ratio_moving_average_longperiod (int): period of long moving average for vix3m/vix ratio.
        vvix_rvi_period_shortperiod (int): period of short RVI.
        vvix_rvi_period_longperiod (int): period of long RVI.

    """

    def __init__(self, interval='1day', signal_name='close', **kwargs):
        self.ratio_moving_average_shortperiod = kwargs.get('ma_period_short', 5)
        self.ratio_moving_average_longperiod = kwargs.get('ma_period_long', 20)
        self.lookback_period_crossover_cumsum = kwargs.get('lookback_period_crossover_cumsum', 5)
        self.vvix_rvi_period_shortperiod = kwargs.get('rvi_period_short', 5)
        self.vvix_rvi_period_longperiod = kwargs.get('rvi_period_long', 20)
        self.compensate_for_lookahead_bias = kwargs.get('compensate_for_lookahead_bias', False)
        
        self.symbol = 'VIX'
        self.interval = interval
        self.pxhistory = self._load_pxhistory(symbol=self.symbol, interval=self.interval)
        self.signal_name = signal_name

        ## Nested strategies
        self.vvix = st.Strategy(name='vvix', symbol='VVIX', signal_name='close', interval=self.interval)
        self.vix3m = st.Strategy(name='vix3m', symbol='VIX3M', signal_name='close', interval=self.interval)
        self.pxhistory = pd.merge(self.pxhistory, self.vix3m.pxhistory[['date', 'close']], on='date', how='inner', suffixes=('', '_vix3m'))
        
        ## vix3m/vix ratio and associated calcs
        self._calc_vix3m_vix_ratio()
        if self.compensate_for_lookahead_bias:
            self.pxhistory['vix3m_vix_ratio'] = self.pxhistory['vix3m_vix_ratio'].shift(1)
        self._calc_deciles(colname='vix3m_vix_ratio')
        self._calc_percentiles(colname='vix3m_vix_ratio')
        self._calc_zscore(colname='vix3m_vix_ratio')
        # 2nd degree calcs 
        self._calc_deciles(colname='vix3m_vix_ratio_zscore')

        ## Ratio Indicators and associated calcs 
        self.pxhistory = indicators.moving_average_weighted(self.pxhistory, 'vix3m_vix_ratio', self.ratio_moving_average_longperiod)
        self.pxhistory = self.pxhistory.rename(columns={'vix3m_vix_ratio_wma': 'vix3m_vix_ratio_ma_long'})
        self.pxhistory = indicators.moving_average_weighted(self.pxhistory, 'vix3m_vix_ratio', self.ratio_moving_average_shortperiod)
        self.pxhistory = self.pxhistory.rename(columns={'vix3m_vix_ratio_wma': 'vix3m_vix_ratio_ma_short'})
        self.pxhistory = indicators.moving_average_crossover(self.pxhistory, 'vix3m_vix_ratio_ma_long', 'vix3m_vix_ratio_ma_short')
        colname_crossover = '%s_%s_crossover'%('vix3m_vix_ratio_ma_long', 'vix3m_vix_ratio_ma_short')
        self.pxhistory = indicators.intra_day_cumulative_signal(self.pxhistory, colname_crossover, intraday_reset=False, lookback_period=self.lookback_period_crossover_cumsum)
        #crossover momentum 
        self.pxhistory = indicators.slope(self.pxhistory, colname=colname_crossover, lookback_periods=5)
        self.pxhistory = indicators.slope(self.pxhistory, colname='%s_cumsum'%(colname_crossover), lookback_periods=5)
        
        # MA crossover calcs 
        self._calc_deciles(colname=colname_crossover)
        self._calc_percentiles(colname=colname_crossover)
        self._calc_zscore(colname=colname_crossover, rescale=True)
        
        ## MA crossover intra-day cumsum 
        self._calc_zscore(colname='%s_cumsum'%(colname_crossover))
        self._calc_deciles(colname='%s_cumsum'%(colname_crossover))
        self._calc_percentiles(colname='%s_cumsum'%(colname_crossover))

        ## backtest signals 
        self.pxhistory['strat_ratio_decile_and_crossover_slope'] = self.pxhistory.apply(lambda row: self.__ratio_decile_and_crossover_slope(row=row, decile_short=5, decile_long=8), axis=1)
        self.calc_trigger_points('strat_ratio_decile_and_crossover_slope')
        # print(self.pxhistory[['date', 'strat_ratio_decile_and_crossover_slope', 'strat_ratio_decile_and_crossover_slope_trigger']])
        # print(self.pxhistory.columns)
        # exit()

        ## Nested VVIX strategy
        self.vvix._calc_deciles(colname='close')
        # Close indicators
        self.vvix.pxhistory = indicators.relative_volatility_index(self.vvix.pxhistory, 'close', 20).rename(columns={'close_rvi': 'close_rvi_%s'%(self.vvix_rvi_period_shortperiod)})
        self.vvix.pxhistory = indicators.relative_volatility_index(self.vvix.pxhistory, 'close', 90).rename(columns={'close_rvi': 'close_rvi_%s'%(self.vvix_rvi_period_longperiod)}) 
        self.vvix.pxhistory['close_rvi_crossover'] = self.vvix.pxhistory['close_rvi_%s'%(self.vvix_rvi_period_shortperiod)] - self.vvix.pxhistory['close_rvi_%s'%(self.vvix_rvi_period_longperiod)]
        # RVI calcs
        self.vvix._calc_deciles(colname='close_rvi_crossover')
        self.vvix._calc_deciles(colname='close_zscore')
        self.vvix._calc_deciles(colname='close_rvi_%s'%(self.vvix_rvi_period_longperiod))
        self.vvix._calc_zscore(colname='close_rvi_%s'%(self.vvix_rvi_period_longperiod))
    
    def plot_overview_dashboard(self, signal_col_name='vix3m_vix_ratio', **kwargs):
        print(self.pxhistory.columns)
        if self.pxhistory['interval'].iloc[0] in ['1min', '5mins', '15mins', '30mins']:
            self.pxhistory['date'] = self.pxhistory['date'].dt.strftime('%Y-%m-%d %H:%M:%S')

        fig, ax = plt.subplots(3, 5)
        

        periods_to_plot = kwargs.get('periods_to_plot', 390)
        maxperiod_fwdreturns = kwargs.get('maxperiod_fwdreturns', 20)
        percentile_lookback_period = kwargs.get('percentile_lookback_period', 252)
        fig.suptitle('Vix3m Ratio Dash')

        ###################################################################################################
        ################################### ROW 1: ratio  #################################################

        # g, bin_edges = pd.qcut(self.pxhistory[signal_col_name], 10, labels=False, duplicates='drop', retbins=True)
        self.pxhistory['%s_percentile_90'%(signal_col_name)] = self.pxhistory[signal_col_name].rolling(percentile_lookback_period).quantile(0.9)
        self.pxhistory['%s_percentile_10'%(signal_col_name)] = self.pxhistory[signal_col_name].rolling(percentile_lookback_period).quantile(0.1)
        
        # self.draw_lineplot(ax[0,0], y=signal_col_name, y_alt='close', drawPercetiles=True, hlines_to_plot=[bin_edges[6]], n_periods_to_plot=periods_to_plot)
        self.draw_lineplot(ax[0,0], y='%s_zscore'%(signal_col_name), y_alt='close', n_periods_to_plot=periods_to_plot)
        ax[0,0].axhline(0, color='black', linestyle='-', alpha=0.5)
        # sns.lineplot(data=self.pxhistory.tail(periods_to_plot), x='date', y='%s_zscore'%(signal_col_name), ax=ax[0,0], color='black', alpha=0.5)
        # sns.lineplot(data=self.pxhistory.tail(periods_to_plot), x='date', y='vix3m_vix_ratio_ma_short', ax=ax[0,0], color='red', alpha=0.3)
        # sns.lineplot(data=self.pxhistory.tail(periods_to_plot), x='date', y='vix3m_vix_ratio_ma_long', ax=ax[0,0], color='red', alpha=0.5)  
        # sns.lineplot(data=self.pxhistory.tail(periods_to_plot), x='date', y='%s_percentile_90'%(signal_col_name), ax=ax[0,0])
        # sns.lineplot(data=self.pxhistory.tail(periods_to_plot), x='date', y='%s_percentile_10'%(signal_col_name), ax=ax[0,0])
        # add text to the plot
        # ax[0,0].text(self.pxhistory['date'].iloc[-1], round(self.pxhistory['%s_percentile_90'%(signal_col_name)].iloc[-1], 3), '%s'%(self.pxhistory['%s_percentile_90'%(signal_col_name)].iloc[-1]), fontsize=9, color='black')
        # ax[0,0].text(self.pxhistory['date'].iloc[-1], round(self.pxhistory['%s_percentile_10'%(signal_col_name)].iloc[-1],3), '%s'%(self.pxhistory['%s_percentile_10'%(signal_col_name)].iloc[-1]), fontsize=9, color='black')

        self.draw_heatmap_signal_returns(ax[0,1], y='%s_percentile'%(signal_col_name), maxperiod_fwdreturns=maxperiod_fwdreturns, title = '%s Percentile'%(str.split(signal_col_name, '_')[-2:][1]))
        self.draw_heatmap_signal_returns(ax[0,2], y='%s_decile'%(signal_col_name), maxperiod_fwdreturns=maxperiod_fwdreturns, title = '%s Decile'%(str.split(signal_col_name, '_')[-2:][1]))
        # self.draw_heatmap_signal_returns(ax[0,3], y='%s_zscore'%(signal_col_name), maxperiod_fwdreturns=maxperiod_fwdreturns)
        self.draw_heatmap_signal_returns(ax[0,3], y='vix3m_vix_ratio_zscore', maxperiod_fwdreturns=maxperiod_fwdreturns, title = '%s Z-score'%(str.split(signal_col_name, '_')[-2:][1]))
        self.draw_autocorrelation(ax[0,4], y=signal_col_name, max_lag=50)
        # self.draw_distribution(ax[0,3], y=signal_col_name, drawPercetiles=True, percentiles_to_plot=bin_edges)
        
        ###################################################################################################
        ################################### ROW 2: Ratio - MA Crossover ###################################

        row2_signal_col_name = '%s_%s_crossover'%('vix3m_vix_ratio_ma_long', 'vix3m_vix_ratio_ma_short')
        # g, bin_edges = pd.qcut(self.pxhistory[row2_signal_col_name], 10, labels=False, duplicates='drop', retbins=True)
        self.pxhistory['%s_percentile_90'%(row2_signal_col_name)] = self.pxhistory[row2_signal_col_name].rolling(percentile_lookback_period).quantile(0.9)
        self.pxhistory['%s_percentile_10'%(row2_signal_col_name)] = self.pxhistory[row2_signal_col_name].rolling(percentile_lookback_period).quantile(0.1)
        # sns.lineplot(data=self.pxhistory.tail(periods_to_plot), x='date', y='%s_percentile_90'%(signal_col_name), ax=ax[1,0])
        # sns.lineplot(data=self.pxhistory.tail(periods_to_plot), x='date', y='%s_percentile_10'%(signal_col_name), ax=ax[1,0])
        # ax[1,0].text(self.pxhistory['date'].iloc[-1], self.pxhistory['%s_percentile_90'%(signal_col_name)].iloc[-1], '%s'%(self.pxhistory['%s_percentile_90'%(signal_col_name)].iloc[-1]), fontsize=9, color='black')
        # ax[1,0].text(self.pxhistory['date'].iloc[-1], self.pxhistory['%s_percentile_10'%(signal_col_name)].iloc[-1], '%s'%(self.pxhistory['%s_percentile_10'%(signal_col_name)].iloc[-1]), fontsize=9, color='black')
        # self.draw_lineplot(ax[1,0], y=signal_col_name, y_alt='close', hlines_to_plot=[bin_edges[4], bin_edges[9]], n_periods_to_plot=periods_to_plot)
        # sns.lineplot(data=self.pxhistory.tail(periods_to_plot), x='date', y='%s'%(row2_signal_col_name), ax=ax[1,0], color='blue', label='%s_zscore'%(row2_signal_col_name))
        self.draw_lineplot(ax[1,0], y='%s_zscore'%(row2_signal_col_name), y_alt='close', n_periods_to_plot=periods_to_plot, plot_title='Ratio MA %s'%(str.split(row2_signal_col_name, '_')[-2:][1]))
        # sns.lineplot(data=self.pxhistory.tail(periods_to_plot), x='date', y=row2_signal_col_name, ax=ax[1,0].twinx(), alpha=0.1)
        # ax[1,0].axhline(0, color='black', linestyle='-', alpha=0.5)
        # set title to last two words of colname (seperated by _)
        # self.apply_default_lineplot_formatting(ax=ax[1,0], title='Ratio MA %s'%(str.split(row2_signal_col_name, '_')[-2:][1]), xlabel='', ylabel='zscore')
        self.draw_heatmap_signal_returns(ax[1,1], y='%s_percentile'%(row2_signal_col_name), maxperiod_fwdreturns=maxperiod_fwdreturns, title = '%s Percentile'%(str.split(row2_signal_col_name, '_')[-2:][1]))
        self.draw_heatmap_signal_returns(ax[1,2], y='%s_decile'%(row2_signal_col_name), maxperiod_fwdreturns=maxperiod_fwdreturns, title = '%s Decile'%(str.split(row2_signal_col_name, '_')[-2:][1]))
        self.draw_heatmap_signal_returns(ax[1,3], y='%s_zscore'%(row2_signal_col_name), maxperiod_fwdreturns=maxperiod_fwdreturns, title = '%s Z-score'%(str.split(row2_signal_col_name, '_')[-2:][1]))
        self.draw_autocorrelation(ax[1,4], y=row2_signal_col_name, max_lag=50)
        # self.draw_distribution(ax[1,3], y=signal_col_name, drawPercetiles=True, percentiles_to_plot=bin_edges)

        #############
        ## row 3
        #############
        # g, bin_edges = pd.qcut(self.vvix.pxhistory['close'], 10, labels=False, duplicates='drop', retbins=True)
        hlines_to_plot = ([
            # self.vvix.pxhistory['close'].quantile(0.1), 
            # self.vvix.pxhistory['close'].quantile(0.9), 
            # bin_edges[4],
            # bin_edges[9]
        ])
        self.vvix.pxhistory['close_percentile_90'] = self.vvix.pxhistory['close'].rolling(252).quantile(0.9)
        self.vvix.pxhistory['close_percentile_1'] = self.vvix.pxhistory['close'].rolling(252).quantile(0.1)
        self.vvix.pxhistory['close_zscore_percentile_90'] = self.vvix.pxhistory['close_zscore'].rolling(252).quantile(0.9)
        self.vvix.pxhistory['close_zscore_percentile_10'] = self.vvix.pxhistory['close_zscore'].rolling(252).quantile(0.1)

        row_3_signal_col_name = 'vix3m_vix_ratio_ma_long_vix3m_vix_ratio_ma_short_crossover_cumsum'
        sns.lineplot(data=self.pxhistory.tail(periods_to_plot), x='date', y=row_3_signal_col_name, ax=ax[2,0], label='Ratio - MA Crossover Cumsum', color='blue')
        self.apply_default_lineplot_formatting(ax=ax[2,0], title='Crossover Cumsum', xlabel='', ylabel='ma crossover cumsum')
        ax[2,0].axhline(0, color='black', linestyle='-', alpha=0.5)
        self.draw_heatmap_signal_returns(ax[2,1], y='%s_zscore'%(row_3_signal_col_name), maxperiod_fwdreturns=maxperiod_fwdreturns, title = '%s Z-score'%(str.split(row_3_signal_col_name, '_')[-2:][1]))
        self.draw_heatmap_signal_returns(ax[2,2], y='%s_decile'%(row_3_signal_col_name), maxperiod_fwdreturns=maxperiod_fwdreturns, title = '%s Decile'%(str.split(row_3_signal_col_name, '_')[-2:][1]))
        self.draw_heatmap_signal_returns(ax[2,3], y='%s_percentile'%(row_3_signal_col_name), maxperiod_fwdreturns=maxperiod_fwdreturns, title = '%s Percentile'%(str.split(row_3_signal_col_name, '_')[-2:][1]))
        self.draw_autocorrelation(ax[2,4], y=row_3_signal_col_name, max_lag=50)

        """" 
            VVIX ROW 
        """
        # self.vvix.draw_lineplot(ax[2,0], y='close_zscore', hlines_to_plot=hlines_to_plot, n_periods_to_plot=periods_to_plot)
        # sns.lineplot(data=self.vvix.pxhistory.tail(periods_to_plot), x='date', y='close_zscore_percentile_90', ax=ax[2,0])
        # sns.lineplot(data=self.vvix.pxhistory.tail(periods_to_plot), x='date', y='close_zscore_percentile_10', ax=ax[2,0])
        # ax[2,0].text(self.vvix.pxhistory['date'].iloc[-1], self.vvix.pxhistory['close_percentile_90'].iloc[-1], '%s'%(self.vvix.pxhistory['close_percentile_90'].iloc[-1]), fontsize=9, color='black')
        # ax[2,0].text(self.vvix.pxhistory['date'].iloc[-1], self.vvix.pxhistory['close_percentile_1'].iloc[-1], '%s'%(self.vvix.pxhistory['close_percentile_1'].iloc[-1]), fontsize=9, color='black')
        
        # ############  2,1 - 2,3
        # self.vvix.draw_heatmap_signal_returns(ax[2,1], y='close_zscore', maxperiod_fwdreturns=maxperiod_fwdreturns)
        # self.vvix.draw_heatmap_signal_returns(ax[2,2], y='close_rvi_%s_zscore'%(self.vvix_rvi_period_longperiod), maxperiod_fwdreturns=maxperiod_fwdreturns)
        # # self.vvix.draw_heatmap_signal_returns(ax[2,3], y='close_rvi_delta_decile', maxperiod_fwdreturns=maxperiod_fwdreturns)
        # self.vvix.draw_autocorrelation(ax[2,3], y='close_rvi_delta', max_lag=50)
        """ VVIX ROW END """

        # share x-axis
        ax[0,0].get_shared_x_axes().join(ax[0,0],ax[1,0], ax[2,0])

        plt.subplots(layout="constrained")
        plt.rcParams['figure.constrained_layout.use'] = True

        return fig

    def plot_vvix_dashboard(self, signal_col_name='close', **kwargs):   
        # draw lineplot 
        fig, ax = plt.subplots(1, 1)
        n_periods_to_plot = kwargs.get('n_periods_to_plot', 390)
        
        self.vvix.draw_lineplot(ax, y=signal_col_name, y_alt='close', n_periods_to_plot=n_periods_to_plot)

        fig.autofmt_xdate()
        return fig 

    def plot_intraday_dashboard(self, signal_col_name='vix3m_vix_ratio'): 
        """
            Plots a dashboard that can be used to monitor intra-day changes in the signal
        """
        fig, ax = plt.subplots(2, 2)

        ## row 1 with intra-day plots to provide a way to monitor intra-day changes in the signal
        # self.draw_lineplot(ax[0,0], y=signal_col_name)

        self.draw_lineplot(ax[0,0], y='%s_ma_long_%s_ma_short_crossover_zscore'%(signal_col_name, signal_col_name))

        rescaled = ffn.rescale(self.pxhistory['%s_ma_long_%s_ma_short_crossover_zscore'%(signal_col_name, signal_col_name)], -1, 1)
        rescaled.plot(ax=ax[0,1])

        sns.histplot(self.pxhistory['%s_ma_long_%s_ma_short_crossover_zscore'%(signal_col_name, signal_col_name)], ax=ax[1,0], bins=100, kde=True)
        sns.histplot(rescaled, ax=ax[1,1], bins=100, kde=True)
        ax = ax[0,1]
        ax.grid(True, which='both', axis='both', linestyle='-', alpha=0.2)
        ax.set_xlabel('date')
        # ax[1,0] vvix aurto correlation
        # self.vvix.draw_autocorrelation(ax=ax[1,1], max_lag=50)

        #_draw_realtime_lineplot_of_signal(ax[0,1], signal_col_name)

        #_draw_realtime_distribution(ax[0,2], signal_col_name)

        ## row 2 with 30m plots to provide a medium term overview of the signal 
        #_draw_lineplot(col=ratio, interval=30 min, lookback=40 days )

        #_draw_heatmap(col=ratio, interval=30min, maxperiod_fwdreturns=20)

        #_draw_histogram(col=ratio, interval=30min, lookback=40 days)

        ## row 3 with 1 day, longer term plots that provide a overview of the signal over its entire available lifetime 
        #_draw_lineplot(col=ratio, interval=1 day)

        #_draw_heatmap(col=ratio, interval=1 day, maxperiod_fwdreturns=20)

        #_draw_histogram(col=ratio, interval=1 day)
        return fig
    
    def plot_ratio_ma_diff_heatmap_grid(self, lookback_periods=[]): 
        if lookback_periods == []:
            print('plot_ratio_ma_diff_heatmap_grid: No lookback periods provided')
            exit()
        
        signal_col_name = 'vix3m_vix_ratio_ma'
        for lp in lookback_periods:
            if not '%s_%s'%(signal_col_name, lp) in self.pxhistory.columns:
                self.pxhistory['%s_%s'%(signal_col_name, lp)] = self.pxhistory['vix3m_vix_ratio'].rolling(window=lp).mean()
                self.pxhistory['%s_diff_%s'%(signal_col_name, lp)] = self.pxhistory['vix3m_vix_ratio'] - self.pxhistory['%s_%s'%(signal_col_name, lp)]
                self._calc_deciles(colname='%s_diff_%s'%(signal_col_name, lp))
                self._calc_percentiles(colname='%s_diff_%s'%(signal_col_name, lp))
    
    def _calc_vix3m_vix_ratio(self, _pxhistory=None):
        """
            Calculate the ratio of VIX3M to VIX
        """
        if _pxhistory: 
            _pxhistory['vix3m_vix_ratio'] = _pxhistory['close_vix3m'] / _pxhistory['close']
        else:
            self.pxhistory['vix3m_vix_ratio'] = self.pxhistory['close_vix3m'] / self.pxhistory['close']

    ###### Signal generation functions

    def run_strategy_backtests(self, **kwargs):
        if self.pxhistory['interval'].iloc[0] in ['1min', '5mins', '15mins', '30mins']:
            print('no intraday strategies yet')
            return None

        ## Strategy 1: Ratio decile and crossover slope
        ratio_decile_short = kwargs.get('ratio_decile_short', 1)
        ratio_decile_long = kwargs.get('ratio_decile_long', 7)
        ratio_decile_flat = kwargs.get('ratio_decile_flat', [])
        close_symbol = 'vix' # symbol that returns are calculated on 
        target_close = self.pxhistory[['date', 'close']]
        target_close.set_index('date', inplace=True)
        target_close.columns = [close_symbol] 


        # Ratio decile and crossover cumsum slope 
        self.pxhistory['ratio_decile_and_crossover_cumsum_slope'] = self.pxhistory.apply(lambda x: btsts.ratio_decile_and_crossover_cumsum_slope(x, ratio_decile_short, ratio_decile_long), axis=1)
        SIGNAL_ratio_decile_and_crossover_slope = self.pxhistory[['date', 'ratio_decile_and_crossover_cumsum_slope']]
        SIGNAL_ratio_decile_and_crossover_slope.set_index('date', inplace=True)
        SIGNAL_ratio_decile_and_crossover_slope.columns = [close_symbol]
        backtest_ratio_decile_and_crossover_slope = btsts.construct_backtest(SIGNAL_ratio_decile_and_crossover_slope, 'vix', target_close, 'ratio decile(1,7) and crossover cumsum slope')

        # Ratio decile 
        self.pxhistory['SIGNAL_ratio_decile_only'] = self.pxhistory.apply(lambda x: btsts.ratio_decile_only(x, ratio_decile_short, ratio_decile_long, ratio_decile_flat), axis=1)
        SIGNAL_ratio_decile_only = self.pxhistory[['date', 'SIGNAL_ratio_decile_only']]
        SIGNAL_ratio_decile_only.set_index('date', inplace=True)
        SIGNAL_ratio_decile_only.columns = [close_symbol]
        backtest_ratio_decile_only = btsts.construct_backtest(SIGNAL_ratio_decile_only, 'vix', target_close, 'ratio decile(1,7) only')

        self.pxhistory['SIGNAL_ratio_decile_short_only']  = self.pxhistory.apply(lambda x: btsts.ratio_decile_short_only(x, ratio_decile_short), axis=1)
        SIGNAL_ratio_decile_short_only = self.pxhistory[['date', 'SIGNAL_ratio_decile_short_only']]
        SIGNAL_ratio_decile_short_only.set_index('date', inplace=True)
        SIGNAL_ratio_decile_short_only.columns = [close_symbol]
        backtest_ratio_decile_short_only = btsts.construct_backtest(SIGNAL_ratio_decile_short_only, 'vix', target_close, 'ratio decile(1) short only')
        
        self.pxhistory['SIGNAL_ratio_decile_5_short_only']  = self.pxhistory.apply(lambda x: btsts.ratio_decile_short_only(x, 5), axis=1)
        SIGNAL_ratio_decile_5_short_only = self.pxhistory[['date', 'SIGNAL_ratio_decile_5_short_only']]
        SIGNAL_ratio_decile_5_short_only.set_index('date', inplace=True)
        SIGNAL_ratio_decile_5_short_only.columns = [close_symbol]
        SIGNAL_ratio_decile_5_short_only = btsts.construct_backtest(SIGNAL_ratio_decile_5_short_only, 'vix', target_close, 'ratio decile(5) short only')



        ## Run the strategies 
        results = btsts.run(backtest_ratio_decile_short_only, SIGNAL_ratio_decile_5_short_only, backtest_ratio_decile_only)
        # 3x5 grid 
        # fig, ax = plt.subplots(2, 2)
        # plt.subplots(layout="constrained")
        # plt.rcParams['figure.constrained_layout.use'] = True
        # fig.suptitle('Select Backtests using Vix3m/Vix Ratio')

        # ## Plot the backtests
        # # btsts.plot_backtests(results, ax[0,0])
        # results.plot(ax=ax[0,0])

        # return fig
        return results

    def plot_strategy_backtests(self, strategy_objects, **kwargs):
        fig, ax = plt.subplots(2, 2, sharex=True, sharey=True)
        # plt.subplots(layout="constrained")
        # plt.rcParams['figure.constrained_layout.use'] = True
        fig.suptitle('Select Backtests using Vix3m/Vix Ratio')
        row_num = 0  
        col_num = 0
        for i, strat in enumerate(strategy_objects):
            print(row_num, col_num)
            results = strat.run_strategy_backtests()
            try: 
                results.plot(ax=ax[row_num,col_num])
            except:
                print('could not plot')
                print(row_num, col_num)
            col_num += 1
            if col_num % 2 == 0:
                row_num += 1
                col_num=0
        return fig


    def calc_trigger_points(self, colname):
        """
            Calculate the trigger ratio and crossover slope
        """
        # add column that is 1 when the colname is -ve in the previous row and 0 or +ve now, AND -1 when the previous row is +ve and the current row is to 0 or -ve
        col = self.pxhistory[colname]
        
        # Initialize the trigger points column
        self.pxhistory['%s_trigger'%(colname)] = 0
        
        # Set the trigger points based on direction change
        self.pxhistory.loc[(col.shift(1) <= 0) & (col > 0), '%s_trigger'%(colname)] = 1
        self.pxhistory.loc[(col.shift(1) >= 0) & (col < 0), '%s_trigger'%(colname)] = -1

    def __ratio_decile_and_crossover_slope(self, row, decile_short, decile_long):
        if row['interval'] in ['5mins', '30mins']:
            if row['date'].time() >= (pd.to_datetime('15:00:00').time()):
                return 0.0
        
        if row['vix3m_vix_ratio_decile'] <= decile_short: 
            if row['vix3m_vix_ratio_ma_long_vix3m_vix_ratio_ma_short_crossover_cumsum_slope'] > 0:
                return -0.2
        
        elif row['vix3m_vix_ratio_decile'] >= decile_long:
            if row['vix3m_vix_ratio_ma_long_vix3m_vix_ratio_ma_short_crossover_cumsum_slope'] < 0:
                return 0.2
        else: return 0.0
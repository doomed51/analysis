import pandas as pd
import seaborn as sns
import sqlite3
import config

class TermStructure:
    def __init__(self, symbol, interval, symbol_underlying):
        self.dbPath_termStructure = config.dbname_termstructure
        self.symbol = symbol.upper()
        self.symbol_underlying = symbol_underlying.upper()
        self.interval = interval

        # load data from db 
        self.ts_raw = self.get_raw_term_structure()
        self.ts_pctContango = self.get_term_structure_pct_contango(self.ts_raw, _1to2=True, _1to3=True, _2to3=True, _3to4=True, _4to7=True, _1to8=True, averageContango=True)
        self.underlying_pxhistory = self.get_underlying_pxhistory()

    def get_raw_term_structure(self):
        symbol = self.symbol.upper()
        tablename = f'{symbol}_{self.interval}'
        #with db.sqlite_connection(config.dbname_stock) as conn:
        with sqlite3.connect(self.dbPath_termStructure) as conn:
            ts_raw = pd.read_sql(f'SELECT * FROM {tablename}', conn)
        ts_raw['date'] = pd.to_datetime(ts_raw['date'])
        ts_raw['symbol'] = symbol
        ts_raw.set_index('date', inplace=True)
        #ts_raw.reset_index(drop=True, inplace=True)
        return ts_raw

    def get_underlying_pxhistory(self):
        # set type 
        if self.symbol_underlying in config._indexList:
            type = 'index'
        else:
            type = 'stock'
        with sqlite3.connect(config.dbname_stock) as conn:
            underlying_pxhistory = pd.read_sql(f'SELECT * FROM {self.symbol_underlying}_{type}_{self.interval}', conn)
        underlying_pxhistory['date'] = pd.to_datetime(underlying_pxhistory['date'])
        underlying_pxhistory.set_index('date', inplace=True)
        print(underlying_pxhistory.tail())
        return underlying_pxhistory

    def get_term_structure_pct_contango(self, tsraw_deprecated, **kwargs):
        symbol = self.ts_raw['symbol'][0]
        self.ts_raw.drop(columns='symbol', inplace=True)
        ts_pctContango = (self.ts_raw.pct_change(axis='columns', periods=-1).drop(columns='month8')*-1)
        print(self.ts_raw.tail())
        print(ts_pctContango.tail())
        for key, value in kwargs.items():
            if key == 'averageContango':
                ts_pctContango['averageContango'] = ts_pctContango.mean(axis=1)
            elif value:
                ts_pctContango[f'{key}MoContango'] = ((self.ts_raw[f'month{key[-1]}'] - self.ts_raw[f'month{key[1]}'])/self.ts_raw[f'month{key[1]}'])*100
                #ts_pctContango = ts_pctContango.join(self.ts_raw[f'{key}MoContango'], on='date')
       
        ts_pctContango['symbol'] = symbol
        self.ts_raw['symbol'] = symbol
        #ts_pctContango.sort_values(by='date', inplace=True)
        return ts_pctContango

    def plot_term_structure(self, symbol_underlying, ax, numDays=5):
        ts = self.ts_raw.reset_index()
        # drop symbol and interval columns 
        symbol = ts['symbol'][0]
        ts.drop(columns=['symbol'], inplace=True)
        # sort ts by date, and get the last 5 rows
        ts['date'] = pd.to_datetime(ts['date'])
        ts = ts.sort_values(by='date').tail(numDays)

        colors = sns.color_palette('YlGnBu', n_colors=numDays) # set color scheme of lineplots     
        for i, color in zip(range(len(ts.tail(numDays))), colors):
            # when its the last item in the for loop print bug
            if i == len(ts.tail(numDays)) - 1:
                color = 'red'
            elif i == len(ts.tail(numDays)) - 2:
                color = 'orange'
            elif i == len(ts.tail(numDays)) - 3:
                color = 'blue'
            sns.lineplot(x=ts.columns[1:], y=ts.iloc[i, 1:], ax=ax, label=ts['date'].iloc[i].strftime('%Y-%m-%d'), color=color)
        
        ax.set_title(f'{symbol} Term Structure for last {numDays} days')
        # set gridstyle
        ax.grid(True, which='both', axis='both', linestyle='--')
        sns.set_style('darkgrid')

    def plot_historical_termstructure(self, ax, contangoColName='_4to7MoContango', **kwargs):
        smaPeriod_contango = kwargs.get('smaPeriod_contango', 20)
        self.ts_pctContango.reset_index(inplace=True)
        self.underlying_pxhistory.reset_index(inplace=True)
        #sns.lineplot(x='date', y='oneToTwoMoContango', data=ts_data, ax=ax, label='oneToTwoMoContango', color='blue')
        #sns.lineplot(x='date', y='oneToThreeMoContango', data=ts_data, ax=ax, label='oneToThreeMoContango', color='green')
        #sns.lineplot(x='date', y='twoToThreeMoContango', data=ts_data, ax=ax, label='twoToThreeMoContango', color='red')
        #sns.lineplot(x='date', y='threeToFourMoContango', data=ts_data, ax=ax, label='threeToFourMoContango', color='pink')
        sns.lineplot(x='date', y=contangoColName, data=self.ts_pctContango, ax=ax, label=contangoColName, color='green')
        # plot 90th percentile rolling 252 period contango
        sns.lineplot(x='date', y=self.ts_pctContango[contangoColName].rolling(252).quantile(0.9), data=self.ts_pctContango, ax=ax, label='90th percentile', color='red', alpha=0.3)
        sns.lineplot(x='date', y=self.ts_pctContango[contangoColName].rolling(252).quantile(0.5), data=self.ts_pctContango, ax=ax, label='50th percentile', color='brown', alpha=0.4)
        sns.lineplot(x='date', y=self.ts_pctContango[contangoColName].rolling(252).quantile(0.1), data=self.ts_pctContango, ax=ax, label='10th percentile', color='red', alpha=0.3)

        # plot 5 period sma of contango
        sns.lineplot(x='date', y=self.ts_pctContango[contangoColName].rolling(smaPeriod_contango).mean(), data=self.ts_pctContango, ax=ax, label='%s period sma'%(smaPeriod_contango), color='blue', alpha=0.6)
        sns.lineplot(x='date', y=self.ts_pctContango[contangoColName].rolling(int(smaPeriod_contango/2)).mean(), data=self.ts_pctContango, ax=ax, label='%s period sma'%(int(smaPeriod_contango/2)), color='red', alpha=0.6)
        #sns.lineplot(x='date', y='currentToLastContango', data=ts_data, ax=ax, label='currentToLastContango', color='red')
        #sns.lineplot(x='date', y='averageContango', data=ts_data, ax=ax, label='averageContango', color='orange')

        # format plot 
        ax.set_title('Historical Contango')
        ax.grid(True, which='both', axis='both', linestyle='--')
        ax.axhline(0, color='black', linestyle='-', alpha=0.5)
        ax.legend(loc='upper left')

        ax2 = ax.twinx()
        sns.lineplot(x='date', y='close', data=self.underlying_pxhistory, ax=ax2, label=self.underlying_pxhistory['symbol'][0], color='black', alpha=0.3)

        ax2.set_yscale('log')
        ax2.grid(False)

    def plot_termstructure_autocorrelation(self, ts_data, ax, contangoColName='fourToSevenMoContango', max_lag=60):
        # Calculate autocorrelations for different lags
        autocorrelations = [ts_data[contangoColName].autocorr(lag=i) for i in range(max_lag)]

        # Create the 

        # plot stem of autocorrelation
        ax.stem(range(max_lag), autocorrelations, use_line_collection=True, linefmt='--')
        ax.set_title(f'{contangoColName} Autocorrelation')

        # format plot
        ax.set_ylabel('Autocorrelation')
        ax.set_xlabel('Lag')

        ax.grid(True, which='both', axis='both', linestyle='--')

    def plot_termstructure_distribution(self, ts_data, ax, contangoColName='fourToSevenMoContango'):
        ts_data.reset_index(inplace=True)
        sns.histplot(ts_data[contangoColName], ax=ax, bins=100, kde=True)

        # add vlines 
        ax.axvline(ts_data[contangoColName].mean(), color='black', linestyle='-', alpha=0.3)
        ax.axvline(ts_data[contangoColName].quantile(0.9), color='red', linestyle='--', alpha=0.3)
        ax.axvline(ts_data[contangoColName].quantile(0.1), color='red', linestyle='--', alpha=0.3)
        # vline at last close 
        ax.axvline(ts_data[contangoColName].iloc[-1], color='green', linestyle='-', alpha=0.6)

        # set vline labels 
        ax.text(ts_data[contangoColName].mean(), 0.5, 'mean: %0.2f'%(ts_data[contangoColName].mean()), color='black', fontsize=10, horizontalalignment='left')
        ax.text(ts_data[contangoColName].quantile(0.9) + 2, 10, '90th percentile: %0.2f'%(ts_data[contangoColName].quantile(0.9)), color='red', fontsize=10, horizontalalignment='right')
        ax.text(ts_data[contangoColName].quantile(0.1) - 3, 3, '10th percentile: %0.2f'%(ts_data[contangoColName].quantile(0.1)), color='red', fontsize=10)
        ax.text(ts_data[contangoColName].iloc[-1], 100, 'last: %0.2f'%(ts_data[contangoColName].iloc[-1]), color='green', fontsize=10, horizontalalignment='left')

        # format plot
        ax.set_title(f'{contangoColName} Distribution')
        ax.set_xlabel('Contango')
        ax.set_ylabel('Frequency')
        ax.grid(True, which='both', axis='both', linestyle='--')

if __name__ == '__main__':
    vixts = TermStructure('vix', '1day', symbol_underlying='UVXY')
    print(vixts.ts_pctContango.tail())
    
    import utils_tabbedPlotsWindow as pltWindow
    import matplotlib.pyplot as plt

    tpw = pltWindow.plotWindow()
    tpw.MainWindow.resize(2560, 1380)
    fig, ax = plt.subplots(2,2)

    vixts.plot_term_structure(symbol_underlying='UVXY', ax=ax[0,0], numDays=10)
    vixts.plot_historical_termstructure(ax=ax[0,1])

    tpw.addPlot('termstructure', fig)

    tpw.show()
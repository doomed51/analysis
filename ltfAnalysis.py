"""
    Dashboard for lower timeframe analyses. 1min, 5min, 15min, 30min

"""
from sys import argv

from utils import utils_tabbedPlotsWindow as pltWindow
from utils import utils_strategyAnalyzer as sa
from returns import strategy_crossover as sc

import pandas as pd 
import interface_localDB as db 

import config 
import momentum 

class ltfAnalysis:
    def __init__(self, symbol, interval):
        self.symbol = symbol
        self.interval = interval
        self.df_pxHistory = self._loadData()
        self.df_momo = pd.DataFrame()

    """
        Load data from local db
    """
    def _loadData(self):
        with db.sqlite_connection(config.dbname_stock) as conn:
            return db.getPriceHistory(conn, self.symbol, self.interval)

    def addMomo(self, lookback):
        if self.df_momo.empty:
            self.df_momo = momentum.calcMomoFactor(self.df_pxHistory, lag=lookback)
        else:
            self.df_momo = momentum.calcMomoFactor(self.df_momo, lag=lookback)
        # rename momo column to momo%s lag
        self.df_momo.rename(columns={'momo': 'momo%s'%(lookback)}, inplace=True)

    def plotMomoOverview(self):
        
        pass 

    def _plotSignalOverview(self):
        pass

    def _plotSignal(self):
        pass

    def _plotMomo(self):
        pass

    def _plotMomoSignal(self):
        pass

    def _plotMomoSignalOverview(self):
        pass

    def _plotMomoSignalHistory():
        pass

if __name__ == '__main__':
    # error if no arg passed
    if len(argv) < 3:
        print('ERROR: Not enough arguments passed: < symbol interval >')
        exit(1)
    else:
        # initialize new lfAnalysis object
        symbol = argv[1].upper()
        interval = argv[2].lower()
        ltf = ltfAnalysis(symbol, interval)
        ltf.addMomo(lookback=20)
        ltf.addMomo(lookback=40)
        print(ltf.df_momo.tail())

        momoCrossover = sc.CrossoverStrategy(ltf.df_momo, ltf.df_momo, 'momo40', 'momo20')

        print(momoCrossover.signal_df.tail())
        tpw = pltWindow.plotWindow()
        tpw.MainWindow.resize(2560, 1380)       
        tpw.addPlot('MOMO crossover', momoCrossover.plotSignalOverview())
        tpw.show()
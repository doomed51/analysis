"""
    Script to manage analyses of lower timeframe vix3m / vix ratio 

"""
import config

import matplotlib.pyplot as plt
import seaborn as sns 
import pandas as pd 
import bt 

from interface import interface_localDB as db

from utils import utils as ut
from utils import utils_tabbedPlotsWindow as tpw

# import strategies
from strategy_implementation import strategy_vix3m_vix_ratio as vv
from strategy_implementation import strategy_vix3m_intraday as vix3m 

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
        momoCrossover = sc.CrossoverStrategy(symbol, ltf.df_momo, ltf.df_momo, 'momo40', 'momo20')
        momoCrossover._calculateSignal()
        
        # add fwdReturn5 to signal_df
        momoCrossover.signal_df['fwdReturn15'] = ltf.df_pxHistory['close'].pct_change(15).shift(-15)
        # add crossover -ve or +ve column crossover_toggle
        momoCrossover.signal_df['crossover_toggle'] = momoCrossover.signal_df['crossover'].apply(lambda x: 1 if x > 0 else -1)

        print('Loading plot testing window...')
        testplot.plotly_implementation_subplots(momoCrossover.signal_df)
        
        ## Window with tabbed plots implementation 
        #tpw = pltWindow.plotWindow()
        #tpw.MainWindow.resize(2560, 1380)       
        #tpw.addPlot('MOMO crossover', momoCrossover.plotSignalOverview())
        #tpw.show()
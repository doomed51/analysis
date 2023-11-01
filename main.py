import sys
sys.path.append('..')
from utils import utils_tabbedPlotsWindow as pltWindow
from rich import print

import config

import matplotlib.pyplot as plt
import interface_localDB as db

import seasonality 
import plotReturns
import momentumPlots as momoPlots

""" 
     helper function to list all the unique symbols in the db
"""
def listSymbols():
    with db.sqlite_connection(config.dbname_stock) as conn:
        symbols = db.listSymbols(conn)
    print('Symbols in DB:')
    print(symbols)


# set symbol to cli arg if provided
if len(sys.argv) > 1:
    ## if the argument is 'list' then list all the symbols in the db
    if sys.argv[1] == 'list':
        listSymbols()
        exit()
    symbol = sys.argv[1]
else:
    print('[red]ERROR: no symbol provided[/red]')
    exit()

overview_fig = seasonality.logReturns_overview_of_seasonality(symbol)
overview_ytd_fig = seasonality.logReturns_overview_of_seasonality(symbol, ytdlineplot=True)
logReturns_fig = plotReturns.plotReturnsAndPrice(symbol)

### load data for momentum plots
with db.sqlite_connection(config.dbname_stock) as conn:
    pxHistory = db.getPriceHistory(conn, symbol, '1day')
    pxHistory_30mins = db.getPriceHistory(conn, symbol, '30mins')
    pxHistory_5mins = db.getPriceHistory(conn, symbol, '5mins')
import momentum 

tpw = pltWindow.plotWindow()

# add seasonality plots to plot window
tpw.addPlot('seasonality', overview_fig)
tpw.addPlot('seasonality vs. YTD', overview_ytd_fig)
tpw.addPlot('log returns', logReturns_fig)
tpw.addPlot('momentum', momoPlots.plotMomoScatter(pxHistory))
tpw.addPlot('momo indicator', momoPlots.plotMomoandpx(pxHistory, 12, 30))

plt.tight_layout()
tpw.show()
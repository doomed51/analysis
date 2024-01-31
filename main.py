import sys
sys.path.append('..')
from utils import utils_tabbedPlotsWindow as pltWindow
from returns import strategy_seasonality
from returns import strategy_crossover as crossover
from rich import print

import config
import datetime 

import matplotlib.pyplot as plt
import interface_localDB as db

import seasonality 
import plotReturns
import momentum
import momentumPlots as momoPlots

""" 
     helper function to list all the unique symbols in the db
"""
def listSymbols():
    with db.sqlite_connection(config.dbname_stock) as conn:
        symbols = db.listSymbols(conn)
        lookup = db.getLookup_symbolRecords(conn)

    # print symbol where interval = 1day
    lookup = lookup[lookup['interval'] == '1day']
    # add column numYears as number of years between firstRecordDate and current date
    lookup['numYears'] = ((datetime.datetime.now() - lookup['firstRecordDate']).dt.days)/252
    
    print('[green]\nSymbols in the database:[/green]')
    print('[green]------------------------[/green]')
    print(lookup[['symbol', 'numYears']].sort_values(by='numYears', ascending=False))


# set symbol to cli arg if provided
if len(sys.argv) > 1:
    ## if the argument is 'list' then list all the symbols in the db
    if sys.argv[1] == 'list':
        listSymbols()
        exit()
    symbol = sys.argv[1].upper()

else:
    print('[red]ERROR: no symbol provided[/red]')
    exit()


### load data for momentum plots
with db.sqlite_connection(config.dbname_stock) as conn:
    pxHistory = db.getPriceHistory(conn, symbol, '1day')
    pxHistory_30mins = db.getPriceHistory(conn, symbol, '30mins')
    pxHistory_5mins = db.getPriceHistory(conn, symbol, '5mins')

# load seasonality figures 
overview_fig = seasonality.logReturns_overview_of_seasonality(symbol)
overview_ytd_fig = seasonality.logReturns_overview_of_seasonality(symbol, ytdlineplot=True)
logReturns_fig = plotReturns.plotReturnsAndPrice(symbol)

# fetch top momo periods by fwdreturn correlation
topr2 = momentum.getTopMomoPeriods(pxHistory, top=5)

# get momo & sma(momo) for top periods  
pxHistory = momentum.calcMomoFactor(pxHistory, lag=topr2['momoPeriod'][0])
pxHistory['sma_slow'] = pxHistory['momo'].rolling(20).mean()
pxHistory['sma_fast'] = pxHistory['momo'].rolling(10).mean()
pxHistory['sma_crossover'] = pxHistory['sma_fast'] - pxHistory['sma_slow']

# intiaialize momo-sma crossover strategy
strategy_momoSmaCrossover = crossover.CrossoverStrategy(base_df=pxHistory, signal_df=pxHistory, target_column_name='momo', signal_column_name='sma_crossover')

strategy_momoVanilla = crossover.CrossoverStrategy(base_df=pxHistory, signal_df=pxHistory, target_column_name='close', signal_column_name='momo')

# initialize window 
tpw = pltWindow.plotWindow()
tpw.MainWindow.resize(2560, 1380)
#tpw.MainWindow.showMaximized() 

# Add tabs 
tpw.addPlot('momo Overview', strategy_momoVanilla.plotSignalOverview())
tpw.addPlot('momo-sma Overview', strategy_momoSmaCrossover.plotSignalOverview())

tpw.addPlot('seasonality', overview_fig)
tpw.addPlot('seasonality vs. YTD', overview_ytd_fig)

tpw.addPlot('top momo quintiles', momoPlots.plotMomoQuintiles(pxHistory, momoPeriods=topr2['momoPeriod'].unique(), fwdReturnPeriods=topr2['fwdReturnPeriod'].unique(), numQuintileBins=5))
tpw.addPlot('Momo scatter', momoPlots.plotMomoAndFwdReturns(pxHistory, topr2))
tpw.addPlot('Momo scatter (topr2)', momoPlots.plotMomoandPx_filteredByPercentile(pxHistory, topr2))


# Additional plots for specific symbols
if symbol.upper() == 'XFLT': # long 25th, close on 8th 
    xfltStrategy = strategy_seasonality.strategy_dayOfMonthSeasonality(symbol, startDay=25, endDay=8)
    xfltStrategy['strategyName'] = 'long 25, close 8'

    # long dec, close jan 
    xfltStrategy2 = strategy_seasonality.strategy_monthToMonth(symbol, startMonth=12, endMonth=1)
    xfltStrategy2['strategyName'] = 'long dec, close jan'

    logReturns_fig = strategy_seasonality.plotResults([xfltStrategy, xfltStrategy2])
    tpw.addPlot('Strategy | Seasonality ', logReturns_fig)

elif symbol.upper() == 'DBO': 
    # long jan, close june 
    dboStrategy = strategy_seasonality.strategy_monthToMonth(symbol, startMonth=1, endMonth=6)
    dboStrategy['strategyName'] = 'long jan, close june'

    # long 24 close 29
    dboStrategy2 = strategy_seasonality.strategy_dayOfMonthSeasonality(symbol, startDay=24, endDay=29)
    dboStrategy2['strategyName'] = 'long 24, close 29'
    
    # short 29, close 1
    dboStrategy3 = strategy_seasonality.strategy_dayOfMonthSeasonality(symbol, startDay=29, endDay=1, direction=-1)
    dboStrategy3['strategyName'] = 'short 29, close 1'

    # merge strategies
    mergedStrategy = strategy_seasonality.mergeStrategies([dboStrategy, dboStrategy2])
    #dboStrategy._append(dboStrategy2)
    #mergedStrategy = mergedStrategy._append(dboStrategy3)
    #mergedStrategy = mergedStrategy.sort_values(by='date', ascending=True)
    #mergedStrategy['cumsum'] = mergedStrategy['logReturn'].cumsum()
    mergedStrategy['strategyName'] = 'all merged'
    
    logReturns_fig = strategy_seasonality.plotResults([dboStrategy, dboStrategy3, dboStrategy2])
    tpw.addPlot('Strat | Seasonality', logReturns_fig)

elif symbol.upper() == 'DXJ':
    dxjStrategy = strategy_seasonality.strategy_dayOfMonthSeasonality(symbol, startDay=23, endDay=27)
    dxjStrategy['strategyName'] = 'long 23, close 27'

    # short 4 close 12
    dxjStrategy2 = strategy_seasonality.strategy_dayOfMonthSeasonality(symbol, startDay=4, endDay=12, direction=-1)
    dxjStrategy2['strategyName'] = 'short 4, close 12'
    
    # long feb, close april
    dxjStrategy3 = strategy_seasonality.strategy_monthToMonth(symbol, startMonth=2, endMonth=4)
    dxjStrategy3['strategyName'] = 'long feb, close april'

    logReturns_fig = strategy_seasonality.plotResults([dxjStrategy, dxjStrategy2, dxjStrategy3])
    tpw.addPlot('Strat | Seasonality', logReturns_fig)

#  nothing useful
elif symbol.upper() == 'FXY': 
    # open long nov, close jan 
    fxyStrategy = strategy_seasonality.strategy_monthToMonth(symbol, startMonth=11, endMonth=1)
    fxyStrategy['strategyName'] = 'long nov, close jan'

    # open long day 5, close day 17
    fxyStrategy2 = strategy_seasonality.strategy_dayOfMonthSeasonality(symbol, startDay=19, endDay=24)
    fxyStrategy2['strategyName'] = 'long 19, close 24'

    # short jan, close june
    fxyStrategy3 = strategy_seasonality.strategy_monthToMonth(symbol, startMonth=1, endMonth=6, direction=-1)
    fxyStrategy3['strategyName'] = 'short jan, close june'

    # short day 29 close day 5
    fxyStrategy4 = strategy_seasonality.strategy_dayOfMonthSeasonality(symbol, startDay=29, endDay=5, direction=-1)
    fxyStrategy4['strategyName'] = 'short 29, close 5'

    # long 4 close 9
    fxyStrategy5 = strategy_seasonality.strategy_dayOfMonthSeasonality(symbol, startDay=4, endDay=9)
    fxyStrategy5['strategyName'] = 'long 4, close 9'

    logReturns_fig2 = strategy_seasonality.plotResults([fxyStrategy, fxyStrategy2, fxyStrategy3, fxyStrategy4, fxyStrategy5])
    tpw.addPlot('Strat | Seasonality', logReturns_fig2)

#  minute evidence of yearly seasonality but nothing actionable  
elif symbol.upper() == 'GLD':
    # long sept, close feb
    gldStrategy = strategy_seasonality.strategy_monthToMonth(symbol, startMonth=9, endMonth=2)
    gldStrategy['strategyName'] = 'long sept, close feb'

    logReturns_fig = strategy_seasonality.plotResults([gldStrategy], benchmark='gld')
    tpw.addPlot('Strat | Seasonality', logReturns_fig)

elif symbol.upper() == 'HSY': 
    hsyStrategy = strategy_seasonality.strategy_monthToMonth(symbol, startMonth=9, endMonth=5)
    logReturns_fig = strategy_seasonality.plotResults([hsyStrategy])
    tpw.addPlot('Strategy - sept drop', logReturns_fig)

elif symbol.upper() == 'HYG': 
    
    # intra month: long june, close july
    hygStrategy = strategy_seasonality.strategy_monthToMonth(symbol, startMonth=6, endMonth=7)
    hygStrategy['strategyName'] = 'long june, close july'
    
    # intra month, bond flow: short 30th, close 3rd
    hygStrategy_intramonth = strategy_seasonality.strategy_dayOfMonthSeasonality(symbol, startDay=30, endDay=7, direction=-1)
    hygStrategy_intramonth['strategyName'] = 'short 30, close 7'
    
    # intra month, bond flow: long 20th, close 30th
    hygStrategy_intramonth_2 = strategy_seasonality.strategy_dayOfMonthSeasonality(symbol, startDay=20, endDay=30)
    hygStrategy_intramonth_2['strategyName'] = 'long 20, close 30'

    hygStrategy_intramonth_3 = strategy_seasonality.strategy_dayOfMonthSeasonality(symbol, startDay=24, endDay=29)
    hygStrategy_intramonth_3['strategyName'] = 'long 24, close 30'

    # merge strategies
    mergedStrategy = hygStrategy._append(hygStrategy_intramonth)
    mergedStrategy = mergedStrategy._append(hygStrategy_intramonth_2)
    mergedStrategy = mergedStrategy.sort_values(by='date', ascending=True).reset_index(drop=True) # sort by date
    mergedStrategy['cumsum'] = mergedStrategy['logReturn'].cumsum() # recalculate cumsum
    mergedStrategy['strategyName'] = 'all merged'

    # merge just the intra month strategies
    mergedStrategy_intramonth = hygStrategy_intramonth._append(hygStrategy_intramonth_2)
    mergedStrategy_intramonth = mergedStrategy_intramonth.sort_values(by='date', ascending=True).reset_index(drop=True) # sort by date
    mergedStrategy_intramonth['cumsum'] = mergedStrategy_intramonth['logReturn'].cumsum() # recalculate cumsum
    mergedStrategy_intramonth['strategyName'] = 'intra month merged'

    logReturns_fig = strategy_seasonality.plotResults([hygStrategy_intramonth_2, hygStrategy_intramonth_3, hygStrategy_intramonth])
    tpw.addPlot('Strategy - monthly seasonality', logReturns_fig)

    #hygStrategy2 = strategy_seasonality.strategy_monthToMonth(symbol, startMonth=11, endMonth=1)
    #logReturns_fig2 = strategy_seasonality.plotResults([hygStrategy_intramonth_2])
    #tpw.addPlot('Strategy - monthly seasonality2', logReturns_fig2)

# IEI long 21, close 30 
elif symbol.upper() == 'IEI':
    # long 21, close 30
    ieiStrategy = strategy_seasonality.strategy_dayOfMonthSeasonality(symbol, startDay=21, endDay=30)
    ieiStrategy['strategyName'] = 'long 21, close 30'

    # short 30, close 5
    ieiStrategy2 = strategy_seasonality.strategy_dayOfMonthSeasonality(symbol, startDay=30, endDay=10, direction=-1)
    ieiStrategy2['strategyName'] = 'short 30, close 10'

    logReturns_fig = strategy_seasonality.plotResults([ieiStrategy, ieiStrategy2])
    tpw.addPlot('Strategy - intra-month seasonality', logReturns_fig)
    
elif symbol.upper() == 'JNK': 
    # long 20, close 30 
    jnkStrategy = strategy_seasonality.strategy_dayOfMonthSeasonality(symbol, startDay=20, endDay=30)
    jnkStrategy['strategyName'] = 'long 20, close 30'

    # short 30, close 11
    jnkStrategy2 = strategy_seasonality.strategy_dayOfMonthSeasonality(symbol, startDay=30, endDay=11, direction=-1)
    jnkStrategy2['strategyName'] = 'short 30, close 11'

    merged = strategy_seasonality.mergeStrategies([jnkStrategy, jnkStrategy2])
    merged['strategyName'] = 'merged'

    logReturns_fig = strategy_seasonality.plotResults([jnkStrategy, jnkStrategy2, merged])
    tpw.addPlot('Strategy | Seasonality', logReturns_fig)

elif symbol.upper() == 'KRE': 
    #kreStrategy = strategy_seasonality.strategy_monthToMonth(symbol, startMonth=6, endMonth=7)
    kreStrategy = strategy_seasonality.strategy_dayOfMonthSeasonality(symbol, startDay=23, endDay=6)
    xlfStrategy = strategy_seasonality.strategy_dayOfMonthSeasonality('XLF', startDay=23, endDay=6)

    # remove any rows in xlfStrategy that are < min date in kreStrategy
    xlfStrategy = xlfStrategy[xlfStrategy['date'] >= kreStrategy['date'].min()]
    xlfStrategy['cumsum'] = xlfStrategy['logReturn'].cumsum()

    mergeStrategy = kreStrategy._append(xlfStrategy)
    # drop logReturns = 0, and order by date sorted by old to new 
    mergeStrategy = mergeStrategy.sort_values(by='date', ascending=True)
    # recalculcate cumsum
    mergeStrategy['cumsum'] = mergeStrategy['logReturn'].cumsum()
    
    logReturns_fig = strategy_seasonality.plotResults([kreStrategy, xlfStrategy, mergeStrategy])

    tpw.addPlot('Strategy - day23 to 6', logReturns_fig)

elif symbol.upper() == 'RFV': 
    #long sept, close jan
    rfvStrategy = strategy_seasonality.strategy_monthToMonth(symbol, startMonth=6, endMonth=7)
    logReturns_fig = strategy_seasonality.plotResults([rfvStrategy], benchmark=symbol)
    tpw.addPlot('Strategy-seasonality', logReturns_fig)

# date updated: Dec 3, 2023
#  noting of interest in seasonality
elif symbol.upper() == 'SCO':
    # short 30, close 5 
    scoStrategy = strategy_seasonality.strategy_dayOfMonthSeasonality(symbol, startDay=26, endDay=5, direction=-1)
    scoStrategy['strategyName'] = 'short 26, close 5'

    logReturns_fig = strategy_seasonality.plotResults([scoStrategy])
    tpw.addPlot('Strategy - intra-month seasonality', logReturns_fig)

elif symbol.upper() == 'SOXL': 
    soxlStrategy = strategy_seasonality.strategy_monthToMonth(symbol, startMonth=12, endMonth=2)
    soxlStrategy['strategyName'] = 'long dec, close feb'

    # long sept close feb
    soxlStrategy2 = strategy_seasonality.strategy_monthToMonth(symbol, startMonth=9, endMonth=2)
    soxlStrategy2['strategyName'] = 'long sept, close feb'

    logReturns_fig = strategy_seasonality.plotResults([soxlStrategy, soxlStrategy2])
    tpw.addPlot('Strategy | Seasonality', logReturns_fig)

    tpw.addPlot('Strategy - dec2feb rtrn dist', strategy_seasonality.plotReturnDistribution(soxlStrategy2))

elif symbol.upper() == 'SPY': 
    # long sept, close dec
    spyStrategy = strategy_seasonality.strategy_monthToMonth(symbol, startMonth=9, endMonth=12)
    spyStrategy['strategyName'] = 'long sept, close dec'

    # long sept, close may 
    spyStrategy2 = strategy_seasonality.strategy_monthToMonth(symbol, startMonth=9, endMonth=5)
    spyStrategy2['strategyName'] = 'long sept, close may'


    logReturns_fig = strategy_seasonality.plotResults([spyStrategy, spyStrategy2])
    tpw.addPlot('Strat | Seasonallity', logReturns_fig)

## sso long 29, close 6 
# nothing of interest in seasonality
elif symbol.upper() == 'SSO':
    ssoStrategy = strategy_seasonality.strategy_dayOfMonthSeasonality(symbol, startDay=30, endDay=6)
    ssoStrategy['strategyName'] = 'long 30, close 6'
    
    # long sept close nov 
    ssoStrategy2 = strategy_seasonality.strategy_monthToMonth(symbol, startMonth=9, endMonth=11)
    ssoStrategy2['strategyName'] = 'long sept, close nov'
    
    logReturns_fig = strategy_seasonality.plotResults([ssoStrategy, ssoStrategy2])
    tpw.addPlot('Strategy | Seasonality', logReturns_fig)

## last updated: Dec 4, 2023
# short 21, close 30 shows some promise, but execution is difficult
elif symbol.upper() == 'TBT':
    # long aug, close oct 
    tbtStrategy = strategy_seasonality.strategy_monthToMonth(symbol, startMonth=8, endMonth=10)
    tbtStrategy['strategyName'] = 'long aug, close oct'

    # short april, close august
    tbtStrategy2 = strategy_seasonality.strategy_monthToMonth(symbol, startMonth=4, endMonth=8, direction=-1)
    tbtStrategy2['strategyName'] = 'short april, close aug'

    # short 21, close 30
    tbtStrategy3 = strategy_seasonality.strategy_dayOfMonthSeasonality(symbol, startDay=21, endDay=30, direction=-1)
    tbtStrategy3['strategyName'] = 'short 21, close 30'

    logReturns_fig = strategy_seasonality.plotResults([tbtStrategy, tbtStrategy2, tbtStrategy3])
    tpw.addPlot('Strat | Seasonality', logReturns_fig)

# last updated: Dec 3, 2023
#   Strong evidence of eom seasonality, but lagging returns   
elif symbol.upper() == 'TLT': # long 10th, close on 30th
    tltStrategy = strategy_seasonality.strategy_dayOfMonthSeasonality(symbol, startDay=21, endDay=30)
    tltStrategy['strategyName'] = 'long 21, close 30'

    # short day 0, close 12 
    tltStrategy2 = strategy_seasonality.strategy_dayOfMonthSeasonality(symbol, startDay=1, endDay=12, direction=-1)
    tltStrategy2['strategyName'] = 'short 1, close 12'

    # short day 30, close day 5
    tltStrategy3 = strategy_seasonality.strategy_dayOfMonthSeasonality(symbol, startDay=30, endDay=5, direction=-1)
    tltStrategy3['strategyName'] = 'short 30, close 5'

    # long oct, close nov 
    tltStrategy4 = strategy_seasonality.strategy_monthToMonth(symbol, startMonth=10, endMonth=11)
    tltStrategy4['strategyName'] = 'long oct, close nov'

    # merge long and strat 2
    #mergedStrategy = tltStrategy._append(tltStrategy2)
    #mergedStrategy = mergedStrategy.sort_values(by='date', ascending=True)
    #mergedStrategy.reset_index(drop=True, inplace=True)
    #mergedStrategy['cumsum'] = mergedStrategy['logReturn'].cumsum()
    #mergedStrategy['strategyName'] = 'Merged - long21 & short1'

    #logReturns_fig = strategy_seasonality.plotResults([tltStrategy, tltStrategy2, tltStrategy3,tltStrategy4, mergedStrategy])
    #tpw.addPlot('Bondflow Strategy', logReturns_fig)

# date updated: Dec 3, 2023
#  consistent negative returns, beginning of month in particular 
elif symbol.upper() == 'UNG': 
    # long 7th day, close 14th day
    ungStrategy = strategy_seasonality.strategy_dayOfMonthSeasonality(symbol, startDay=7, endDay=14)
    ungStrategy['strategyName'] = 'long 7, close 14'

    # short 29 close 7
    ungStrategy2 = strategy_seasonality.strategy_dayOfMonthSeasonality(symbol, startDay=28, endDay=7, direction=-1)
    ungStrategy2['strategyName'] = 'short 29, close 7'
    
    # short 14, close 20
    ungStrategy3 = strategy_seasonality.strategy_dayOfMonthSeasonality(symbol, startDay=14, endDay=21, direction=-1)
    ungStrategy3['strategyName'] = 'short 14, close 20'

    # short 14, close 7
    ungStrategy4 = strategy_seasonality.strategy_dayOfMonthSeasonality(symbol, startDay=14, endDay=7, direction=-1)
    ungStrategy4['strategyName'] = 'short 14, close 7'

    logReturns_fig = strategy_seasonality.plotResults([ungStrategy, ungStrategy2, ungStrategy3, ungStrategy4])
    tpw.addPlot('Strategy | Seasonality', logReturns_fig)

elif symbol.upper() == 'VIX': # open oct, close dec => expect negative returns 
    vixStrategy = strategy_seasonality.strategy_monthToMonth(symbol, startMonth=9, endMonth=11, direction=-1)
    vixStrategy['strategyName'] = 'short sept, close nov'

    vixStrategy2 = strategy_seasonality.strategy_monthToMonth(symbol, startMonth=2, endMonth=4, direction=-1)
    vixStrategy2['strategyName'] = 'short feb, close april'

    logReturns_fig = strategy_seasonality.plotResults([vixStrategy, vixStrategy2])
    tpw.addPlot('Strategy | Seasonality', logReturns_fig)

# date updated: Dec 3, 2023
# nothing of interest in seasonality
elif symbol.upper() == 'XBI':
    # long march, close july 
    xbiStrategy = strategy_seasonality.strategy_monthToMonth(symbol, startMonth=10, endMonth=7)
    xbiStrategy['strategyName'] = 'long oct, close july'

    logReturns_fig = strategy_seasonality.plotResults([xbiStrategy], benchmark=symbol)
    tpw.addPlot('Strat | Seasonallity', logReturns_fig)

# dec. 19 2023
elif symbol.upper() == 'XIU':
    # long 24 close 5
    xiuStrategy = strategy_seasonality.strategy_dayOfMonthSeasonality(symbol, startDay=24, endDay=5)
    xiuStrategy['strategyName'] = 'long 24, close 5'

    logReturns_fig = strategy_seasonality.plotResults([xiuStrategy])
    tpw.addPlot('Strat | Seasonallity', logReturns_fig)
    

# last updated: Dec 3, 2023 
#  limited evidence of seasonality, weak returns
elif symbol.upper() == 'XLE': 
    # long 29, close 6
    xleStrategy = strategy_seasonality.strategy_dayOfMonthSeasonality(symbol, startDay=29, endDay=6)
    xleStrategy['strategyName'] = 'long 29, close 6'

    # long sept, close may
    xleStrategy2 = strategy_seasonality.strategy_monthToMonth(symbol, startMonth=9, endMonth=5)
    xleStrategy2['strategyName'] = 'long sept, close may'

    logReturns_fig = strategy_seasonality.plotResults([xleStrategy, xleStrategy2], benchmark='xle')
    tpw.addPlot('Strat | Seasonallity', logReturns_fig)

#XLI 
elif symbol.upper() == 'XLI':
    # long 23, close 6
    xliStrategy = strategy_seasonality.strategy_dayOfMonthSeasonality(symbol, startDay=23, endDay=6)
    xliStrategy['strategyName'] = 'long 23, close 6'

    logReturns_fig = strategy_seasonality.plotResults([xliStrategy], benchmark='spy')
    tpw.addPlot('Strat | Seasonality', logReturns_fig)
# last update: Dec 3, 2023
#   Strong evidence of eom seasonality, with good returns 
elif symbol.upper() == 'XLF': # long on 23rd, close on 6th 
    xlfStrategy = strategy_seasonality.strategy_dayOfMonthSeasonality(symbol, startDay=23, endDay=6)
    xlfStrategy['strategyName'] = 'long 23, close 6'
    logReturns_fig = strategy_seasonality.plotResults([xlfStrategy])
    tpw.addPlot('Strat - mthly ssn', logReturns_fig)
    tpw.addPlot('Strat - mthly ssn rtrn dist', strategy_seasonality.plotReturnDistribution(xlfStrategy))

# last update: dec 3, 2023
#   some evidence of eom seasonality, returns ok when long and short strats are run together
elif symbol.upper() == 'XLP': 
    # long 24, close 5 
    xlpStrategy = strategy_seasonality.strategy_dayOfMonthSeasonality(symbol, startDay=24, endDay=5)
    xlpStrategy['strategyName'] = 'long 24, close 5'

    # short 17, close 24
    xlpStrategy2 = strategy_seasonality.strategy_dayOfMonthSeasonality(symbol, startDay=17, endDay=24, direction=-1)
    xlpStrategy2['strategyName'] = 'short 17, close 24'

    # long 24, close 30 
    xlpStrategy3 = strategy_seasonality.strategy_dayOfMonthSeasonality(symbol, startDay=24, endDay=30)
    xlpStrategy3['strategyName'] = 'long 24, close 30'

    # long feb, close may
    xlpStrategy4 = strategy_seasonality.strategy_monthToMonth(symbol, startMonth=2, endMonth=5)
    xlpStrategy4['strategyName'] = 'long feb, close may'

    # merge short 17 to 24, and long 24 to 30
    mergedStrategy = xlpStrategy2._append(xlpStrategy3)
    mergedStrategy = mergedStrategy.sort_values(by='date', ascending=True)
    mergedStrategy.reset_index(drop=True, inplace=True)
    mergedStrategy['cumsum'] = mergedStrategy['logReturn'].cumsum()
    mergedStrategy['strategyName'] = 'Merged - s17c24, l24c30'

    logReturns_fig = strategy_seasonality.plotResults([xlpStrategy, xlpStrategy2, xlpStrategy3, xlpStrategy4, mergedStrategy])
    tpw.addPlot('Strat | Seasonality', logReturns_fig)

# last updated: Dec 3, 2023
#  strong evidence of eom seasonality, flat to negative returns 2022 onwards; but 1.5+ since inception
elif symbol.upper() == 'XLU':
    # long 23rd, close 3rd 
    xluStrategy = strategy_seasonality.strategy_dayOfMonthSeasonality(symbol, startDay=23, endDay=3)
    xluStrategy['strategyName'] = 'long 23, close 3'
    
    # long feb, close may
    xluStrategy2 = strategy_seasonality.strategy_monthToMonth(symbol, startMonth=2, endMonth=5)
    xluStrategy2['strategyName'] = 'long feb, close may'

    logReturns_fig = strategy_seasonality.plotResults([xluStrategy, xluStrategy2])
    tpw.addPlot('Strat - long23close3', logReturns_fig)

# last updated: Dec 3, 2023
#  some evidence of seasonality but returns are at best marginally better than buy and hold 
elif symbol.upper() == 'XLV':
    # long sept, close dec
    xlvStrategy0 = strategy_seasonality.strategy_monthToMonth(symbol, startMonth=9, endMonth=12)
    xlvStrategy0['strategyName'] = 'long sept, close dec'
    # long 23, close 5
    xlvStrategy = strategy_seasonality.strategy_dayOfMonthSeasonality(symbol, startDay=24, endDay=5)
    xlvStrategy['strategyName'] = 'long 24, close 5'
    # short 18, close 24
    xlvStrategy2 = strategy_seasonality.strategy_dayOfMonthSeasonality(symbol, startDay=18, endDay=24, direction=-1)
    xlvStrategy2['strategyName'] = 'short 18, close 24'

    # merge all strategies
    mergedStrategy = xlvStrategy0._append(xlvStrategy)
    mergedStrategy = mergedStrategy._append(xlvStrategy2)
    mergedStrategy = mergedStrategy.sort_values(by='date', ascending=True)
    mergedStrategy.reset_index(drop=True, inplace=True)
    mergedStrategy['cumsum'] = mergedStrategy['logReturn'].cumsum()
    mergedStrategy['strategyName'] = 'All Merged'
    
    # merge just the intra month strategies
    mergedStrategy2 = xlvStrategy._append(xlvStrategy2)
    mergedStrategy2 = mergedStrategy2.sort_values(by='date', ascending=True)
    mergedStrategy2.reset_index(drop=True, inplace=True)
    mergedStrategy2['cumsum'] = mergedStrategy2['logReturn'].cumsum()
    mergedStrategy2['strategyName'] = 'intramonth merged'

    # merge long only strategies
    mergedLongOnly = xlvStrategy0._append(xlvStrategy)
    mergedLongOnly = mergedLongOnly.sort_values(by='date', ascending=True)
    mergedLongOnly.reset_index(drop=True, inplace=True)
    mergedLongOnly['cumsum'] = mergedLongOnly['logReturn'].cumsum()
    mergedLongOnly['strategyName'] = 'mergedLongOnly'

    # merge 2 and 0
    mergedStrategy3 = xlvStrategy0._append(xlvStrategy2)
    mergedStrategy3 = mergedStrategy3.sort_values(by='date', ascending=True)
    mergedStrategy3.reset_index(drop=True, inplace=True)
    mergedStrategy3['cumsum'] = mergedStrategy3['logReturn'].cumsum()
    mergedStrategy3['strategyName'] = 'intra short and month'
    
    logReturns_fig = strategy_seasonality.plotResults([xlvStrategy0, xlvStrategy, xlvStrategy2])#, mergedStrategy, , mergedLongOnly, mergedStrategy3])
    tpw.addPlot('Strat - long24close5', logReturns_fig)    

## YCS 
# last updated: Dec 3, 2023
elif symbol.upper() == 'YCS': 
    # long august, close november 
    ycsStrategy = strategy_seasonality.strategy_monthToMonth(symbol, startMonth=8, endMonth=11)
    ycsStrategy['strategyName'] = 'long aug, close nov'
    
    # long jan close march
    ycsStrategy2 = strategy_seasonality.strategy_monthToMonth(symbol, startMonth=1, endMonth=3)
    ycsStrategy2['strategyName'] = 'long jan, close march'

    merged_monthly = strategy_seasonality.mergeStrategies([ycsStrategy, ycsStrategy2])

    logReturns_fig = strategy_seasonality.plotResults([ycsStrategy, ycsStrategy2, merged_monthly])
    tpw.addPlot('Strat | Seasonality', logReturns_fig)
plt.tight_layout()
tpw.show()
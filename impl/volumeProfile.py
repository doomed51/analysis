import sys
sys.path.append('..')

import argparse 
import config

from interface import interface_localDB as db
from utils import utils as ut

import pandas as pd
import matplotlib.pyplot as plt

from rich import print

######## GLOBAL VARS
dbname_stocks = config.dbname_stock
#####################
# Create the parser
parser = argparse.ArgumentParser(description='My CLI Application')

# Add arguments
parser.add_argument('symbol')

# Parse the command-line arguments
args = parser.parse_args()

# Access the values of the arguments
symbol = args.symbol.upper()

tableName = db._constructTableName(symbol, '1day')

with db.sqlite_connection(dbname_stocks) as conn:
    symbolRecord = db.getPriceHistoryWithTablename(conn, tableName)


## function that plots a lineplot of volume over the available date range 
def plotVolume(symbolRecord, numDays = 0):
    # convert date column to datetime
    symbolRecord['date'] = pd.to_datetime(symbolRecord['date'])

    # sort by date
    symbolRecord = symbolRecord.sort_values(by='date')

    if numDays > 0: 
        symbolRecord = symbolRecord.tail(numDays)
        # add title
        plt.title('%s Volume over last %d days'%(symbol, numDays))
    else:
        # add title
        plt.title('%s Volume over time'%symbol)
    
    # plot volume over date range
    #symbolRecord.plot(x='date', y='volume', title='%s Volume'%symbol)
    plt.plot(symbolRecord['date'], symbolRecord['volume'])

    # rotate x axis labels
    plt.xticks(rotation=45)

## plot a histogram of volume
def plotVolumeHistogram(symbolRecord, numDays = 0):
    # convert date column to datetime
    symbolRecord['date'] = pd.to_datetime(symbolRecord['date'])

    # sort by date
    symbolRecord = symbolRecord.sort_values(by='date')

    if numDays > 0: 
        symbolRecord = symbolRecord.tail(numDays)

    # plot volume over date range
    plt.hist(symbolRecord['volume'], bins=50)

    # rotate x axis labels
    plt.xticks(rotation=45)

    # add title
    plt.title('%s Volume Histogram'%symbol)

## plot seasonality of volume for each day of the month 
def plotVolumeSeasonality(symbolRecord):
    # convert date column to datetime
    symbolRecord['date'] = pd.to_datetime(symbolRecord['date'])

    # sort by date
    symbolRecord = symbolRecord.sort_values(by='date')

    symbolRecord_aggregated = ut.aggregate_by_dayOfMonth(symbolRecord, 'volume')
    
    # plot barplot of aggregated mean and sd in different colours
    plt.bar(symbolRecord_aggregated['dayOfMonth'], symbolRecord_aggregated['mean']) 

    # add plot of sd as a lineplot
    plt.plot(symbolRecord_aggregated['dayOfMonth'], symbolRecord_aggregated['std'], color='red')

    # add legend    
    plt.legend(['std', 'mean'])

### plots a grid of 2x2 plots
def plotVolumeProfileMonitor(symbolRecord):
    index = 1

    # style plot
    plt.style.use('Solarize_Light2')

    plt.subplot(2, 2, index) 
    plotVolume(symbolRecord)

    index += 1
    plt.subplot(2, 2, index)
    plotVolumeHistogram(symbolRecord)

    index += 1
    plt.subplot(2, 2, index)
    plotVolumeSeasonality(symbolRecord)

    index+=1 
    plt.subplot(2, 2, index)
    plotVolume(symbolRecord, 100)

    plt.tight_layout()
    # make plot fullscreen
    mng = plt.get_current_fig_manager()
    #mng.window.state('zoomed')

    plt.show()

print(symbolRecord)
#plotVolume(symbolRecord)
plotVolumeProfileMonitor(symbolRecord)
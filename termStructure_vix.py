import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

## local libs
import interface_localDB as db
import utils_termStructure as vixts

### CONFIGS ### 
db_stock = '/workbench/historicalData/venv/saveHistoricalData/historicalData_index.db'
vvix_topPercentile = 0.9
vvix_bottomPercentile = 0.1
vvix_percentileLookbackDays = 252 ## 1 year lookback = 252 trading days

#####################################
## prepare vix term structure data 
#####################################
vix_ts_pctContango = vixts.getVixTermStructurePctContango(fourToSeven=True, currentToLast=True, averageContango=True)


## prepare price history data
###################################
############# VIX  ################
with db.sqlite_connection(db_stock) as conn:
    vix = db.getPriceHistory(conn,'VIX', '1day')
    vvix = db.getPriceHistory(conn, 'VVIX', '1day', withpctChange=False)
    spx = db.getPriceHistory(conn, 'SPX', '1day')

## make sure vix and vix_ts_pctContango start on the same date
#vix = vix[vix.index >= vix_ts_pctContango.index.min()]

###################################
############# VVIX ################
    

##  make sure vvix and vix_ts_pctContango start on the same date 
#vvix = vvix[vvix.index >= vix_ts_pctContango.index.min() - pd.Timedelta(days=252)]

## calculate percentile rank of VVIX
vvix['percentileRank'] = vvix['close'].rolling(vvix_percentileLookbackDays).apply(lambda x: pd.Series(x).rank(pct=True).iloc[-1])

vvix['percentileRank_90d'] = vvix['close'].rolling(90).apply(lambda x: pd.Series(x).rank(pct=True).iloc[-1])
vvix['percentileRank_60d'] = vvix['close'].rolling(60).apply(lambda x: pd.Series(x).rank(pct=True).iloc[-1])

"""
    for passed in dataframes (main, reference) return main with only the dates in reference 
"""
def _filterDates(main, reference):
    return main[main['date'].isin(reference['date'])]
#################################################
############## FINAL CLEANUP ... ################
#################################################
# reset index to eliminate duplicate indices resulting from joins 
vix_ts_pctContango.reset_index(inplace=True)
# make sure vix and vix_ts_pctContango start on the same date
#vix = vix[vix.index >= vix_ts_pctContango['Date'].min()]

## from vix_ts_pctContango remove any dates that are not in vix and vvix
vix_ts_pctContango = vix_ts_pctContango[vix_ts_pctContango['date'].isin(vix['date']) & vix_ts_pctContango['date'].isin(vvix['date'])]

# from vvix remove any dates that are not in vix and vix_ts_pctContango
#vvix = vvix[vvix.index.isin(vix.index) & vvix.index.isin(vix_ts_pctContango['date'])]
vvix = vvix[vvix['date'].isin(vix['date']) & vvix['date'].isin(vix_ts_pctContango['date'])]

# from vix remove any dates that are not in vvix and vix_ts_pctContango
vix = vix[vix['date'].isin(vvix['date']) & vix['date'].isin(vix_ts_pctContango['date'])]

#####################################################
################# PLOT FUNCTIONS ####################
#####################################################

""" plot the relationships between vix term structure and vix price history
 arguments:
  vix_ts_pctContango: the vix term structure data
  vix: the vix price history data
 generate a 1x3 figure with the following subplots:
  1. scatter of fourToSevenMoContango vs. VIX close_pctChange
  2. scatter of avgContango vs. VIX close_pctChange
  3. scatter of vvix percentileRank vs. VIX close_pctChange
 notes: 
  - vix pct change is shifted by 1 day so the scatters represent the
    relationship with next day's return
"""
def plotVixRelationships(vix_ts_pctContango, vix, vvix):
    fig2, ax2 = plt.subplots(2, 3, figsize=(15, 11))
    fig2.suptitle('Contango & VIX next day returns')
    
    # shift vix by 1 day for next day returns
    vix['pctChange'] = vix['pctChange'].shift(-1)

    # plot fourToSevenMoContango vs. VIX close_pctChange
    sns.scatterplot(x=vix_ts_pctContango['fourToSevenMoContango'], y=vix['pctChange'], ax=ax2[0,0])
    sns.regplot(x=vix_ts_pctContango['fourToSevenMoContango'], y=vix['pctChange'], ax=ax2[0,0], line_kws={'color': 'red'})
    ax2[0,0].set_title('4-7 Mo Contango')

    # plot avgContango vs. VIX close_pctChange
    sns.scatterplot(x=vix_ts_pctContango['averageContango'], y=vix['pctChange'], ax=ax2[0,1])
    sns.regplot(x=vix_ts_pctContango['averageContango'], y=vix['pctChange'], ax=ax2[0,1], line_kws={'color': 'red'})
    ax2[0,1].set_title('Avg Contango')

    # plot currentToLastMoContango vs. VIX close_pctChange
    sns.scatterplot(x=vix_ts_pctContango['currentToLastContango'], y=vix['pctChange'], ax=ax2[0,2])
    sns.regplot(x=vix_ts_pctContango['currentToLastContango'], y=vix['pctChange'], ax=ax2[0,2], line_kws={'color': 'red'})
    ax2[0,2].set_title('Current to Last Mo Contango')
    
    # plot vvix percentileRank vs. VIX close_pctChange
    sns.scatterplot(x=vvix['percentileRank'], y=vix['pctChange'], ax=ax2[1,0])
    sns.regplot(x=vvix['percentileRank'], y=vix['pctChange'], ax=ax2[1,0], line_kws={'color': 'red'})
    ax2[1,0].set_title('VVIX Percentile Rank')
    # reverse x axis
    ax2[1,0].invert_xaxis()

    # plot vvix percentileRank_30d vs. VIX close_pctChange
    sns.scatterplot(x=vvix['percentileRank_60d'], y=vix['pctChange'], ax=ax2[1,1])
    sns.regplot(x=vvix['percentileRank_60d'], y=vix['pctChange'], ax=ax2[1,1], line_kws={'color': 'red'})
    ax2[1,1].set_title('VVIX Percentile Rank 60d')
    # reverse x axis
    ax2[1,1].invert_xaxis()

    # plot vvix percentileRank_90d vs. VIX close_pctChange
    sns.scatterplot(x=vvix['percentileRank_90d'], y=vix['pctChange'], ax=ax2[1,2])
    sns.regplot(x=vvix['percentileRank_90d'], y=vix['pctChange'], ax=ax2[1,2], line_kws={'color': 'red'})
    ax2[1,2].set_title('VVIX Percentile Rank 90d')
    # reverse x axis
    ax2[1,2].invert_xaxis()


"""
view for day to day monitoring of VIX term structure changes. The following are displayed:
    - VIX: 4-7 month contango, and percentile rank of vvix
    - VIX: close 
    - VIX close pct change vs. vvix percentile rank scatter
"""
def plotVixTermStructureMonitor(vix_ts_pctContango, vix, vvix):

    # using seaborn, create figure with 2 subplots
    fig, ax = plt.subplots(1, 1, figsize=(15, 10))
    # set title
    fig.suptitle('VIX Term Structure')

    ###############################
    # plot fourtosevenMoContango, avgContanto, and percentile rank of vvix
    sns.lineplot(x='date', y='fourToSevenMoContango', data=vix_ts_pctContango, ax=ax)
    ## replace close with percentileRank for vvix 
    sns.lineplot(x=vvix['date'], y='close', data=vvix, ax=ax.twinx(), drawstyle='steps-pre', color='red', alpha=0.3)

    # plot avgcontango on the same axis as fourtosevenMoContango
    #sns.lineplot(x='date', y='averageContango', data=vix_ts_pctContango_last30, ax=ax[0])

    ###############################
    # Format plot
    ax.axhline(y=0, color='black', linestyle='-')
    ax.axhline(y=0.06, color='blue', linestyle='--', alpha=0.5)
    ax.set_title('4th to 7th Month Contango') 
    # set opacity of avgcontango to 0.5
    ax.lines[1].set_alpha(0.5)
    
    ## add a legend to the plot
    ax.legend(['4-7 Mo Contango', 'VVIX'], loc='upper left')
        
    ##############################
    ## plot vix close
    ##sns.lineplot(x='date', y='close', data=vix, ax=ax[1])
    
    ##############################
    # plot distribution of 4to7MoContango
    #sns.histplot(x='fourToSevenMoContango', data=vix_ts_pctContango, ax=ax[1])
    #ax[1].set_title('4th to 7th Month Contango Distribution')

    ##############################
    ## plot distribution of vvix percentileRank
    #sns.histplot(x='percentileRank', data=vvix, ax=ax[2])
    #ax[2].set_title('VVIX Percentile Rank Distribution')

    ## x-axes of both plots start on the same date (easier to compare)
    #ax[1].set_xlim(ax[0].get_xlim())

    ## plot scatter of vvix percentileRank vs vix next day return

    # shift vix by 1 day for next day returns 
    #vix['pctChange']= vix['pctChange'].shift(-1)



    ## join vvix percentileRank with vix pctChange 
    ##vvix = vvix.join(vix[['date', 'pctChange']], how='inner', lsuffix='_vvix', rsuffix='_vix', on='date')
    #vvix = vvix.merge(vix[['date', 'pctChange']], how='inner', on='date')

    ## plot the scatter with line of best fit
    #sns.scatterplot(x=vvix['percentileRank'], y=vvix['pctChange'], data=vvix, ax=ax[2])
    #sns.scatterplot(x='percentileRank', y='close_pctChange', data=vvix, ax=ax[2])
    #sns.regplot(x='percentileRank', y='pctChange', data=vvix, scatter=False, ax=ax[2], line_kws={'color': 'red'})
    #ax[2].set_title('VVIX Percentile Rank vs VIX Close Pct Change')

"""
function that plots intra-month, and month over month seasonality of 4-7mo. contango
 arguments:
    - vix_ts_pctContango: dataframe of vix term structure data
 plots the following:
 - mean and sd of 4-7 month contango aggregated by day of month
 - mean and sd of 4-7 month contango aggregated by month
"""
def plotVixTermStructureSeasonality(vix_ts_pctContango):
    # new df that aggregates 4-7 month contango by day of month
    vix_ts_pctContango_day = vix_ts_pctContango.groupby(vix_ts_pctContango['date'].dt.day).agg({'fourToSevenMoContango': ['mean', 'std']})

    # new df that aggregates 4-7 month contango by month
    vix_ts_pctContango_month = vix_ts_pctContango.groupby(vix_ts_pctContango['date'].dt.month).agg({'fourToSevenMoContango': ['mean', 'std']})

    # using seaborn, create figure with 2 subplots
    fig, ax = plt.subplots(2, 1, figsize=(15, 10))

    # set title
    fig.suptitle('VIX Term Structure Seasonality')

    # barplot mean and sd of 4-7 month contango aggregated by day of month
    sns.barplot(x=vix_ts_pctContango_day.index, y=vix_ts_pctContango_day['fourToSevenMoContango']['mean'], ax=ax[0], color='blue')
    #sns.barplot(x=vix_ts_pctContango_day.index, y=vix_ts_pctContango_day['fourToSevenMoContango']['std'], ax=ax[0].twinx(), color='red')
    ax[0].set_title('4th to 7th Month Contango by Day of Month')

    # barplot mean and sd of 4-7 month contango aggregated by month
    sns.barplot(x=vix_ts_pctContango_month.index, y=vix_ts_pctContango_month['fourToSevenMoContango']['std'], ax=ax[1], color='grey', alpha=0.5)
    sns.barplot(x=vix_ts_pctContango_month.index, y=vix_ts_pctContango_month['fourToSevenMoContango']['mean'], ax=ax[1].twinx(), color='red')
    ax[1].set_title('4th to 7th Month Contango by Month')
    # set x-axis labels to month names
    ax[1].set_xticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])


##################################################
############### call plots  
##################################################

# set seaborn style
sns.set()
sns.set_style('darkgrid')

# get spx price history
spx = _filterDates(spx, vix_ts_pctContango)

#plotVixRelationships(vix_ts_pctContango, vix, vvix)
plotVixTermStructureMonitor(vix_ts_pctContango, vix, spx)
#plotVixTermStructureSeasonality(vix_ts_pctContango)

plt.tight_layout()
plt.show()
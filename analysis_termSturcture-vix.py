import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

## local libs
import localDbInterface as db
import termStructure_vix as vixts

# read in vix futures data 
vix_ts_raw = vixts.getRawVixTermStructure()

# percent change between n and n+1 month futures
vix_ts_pctContango = vixts.getVixTermStructurePctContango(fourToSeven=True, currentToLast=True)

# add average contango across entire term structure
vix_ts_pctContango['averageContango'] = vix_ts_pctContango.mean(axis=1)

# get vix history from db 
vix = db.getPriceHistory('VIX', '1day')

## add pctchange of close column
vix['close_pctChange'] = vix['close'].pct_change()

## add vix close to the pctContango df
vix_ts_pctContango = vix_ts_pctContango.join(vix['close_pctChange'], on='Date')

## add a column that is 'contango' if fourToSevenMoContango is positive, 'backwardation' if negative
vix_ts_pctContango['firstToLastTermStruct'] = vix_ts_pctContango['currentToLastContango'].apply(lambda x: 'contango' if x > 0 else 'backwardation')

# reset index to eliminate duplicate indices resulting from joins 
vix_ts_pctContango.reset_index(inplace=True)


## Plot various results 

# set seaborn style
sns.set()

# using seaborn, create figure with 2 subplots
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(10, 10))

# using seaborn, plot fourtosevenMoContango, and averageContango
ax1=sns.lineplot(x='Date', y='fourToSevenMoContango', data=vix_ts_pctContango, ax=ax1)
#add black line at 0
ax1.axhline(y=0, color='black', linestyle='-')
#vix_ts_pctContango[['fourToSevenMoContango', 'averageContango']].plot()

# using seaborn, histogram of fourtosevenMoContango
ax4=sns.histplot(vix_ts_pctContango['fourToSevenMoContango'], bins=20, ax=ax4)
#ax4.axvline(x=0, color='black', linestyle='-')

# using seaborn, plot close
ax3=sns.lineplot(x='Date', y='close', data=vix, ax=ax3)

# using seaborn, plot averageContango
ax2=sns.lineplot(x='Date', y='averageContango', data=vix_ts_pctContango, ax=ax2)
ax2.axhline(y=0, color='black', linestyle='-')

## setup pairplot
#
#sns.pairplot(vix_ts_pctContango[['currentToLastContango', 'fourToSevenMoContango', 'averageContango', 'close_pctChange', 'firstToLastTermStruct']], hue='firstToLastTermStruct', height=2.5)


# Scatter of fourtosevenmonthcontango vs close_pctChange 
#
#sns.scatterplot(x='fourToSevenMoContango', y='close_pctChange', hue='firstToLastTermStruct', data=vix_ts_pctContango)
#sns.regplot(x='fourToSevenMoContango', y='close_pctChange', data=vix_ts_pctContango, scatter=False)

plt.show()
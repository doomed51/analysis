import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

import localDbInterface as db
import termStructure_vix as vixts

# get history for vixm from db
vixm = db.getPriceHistory('vixm', '1day')

# get history for vix from db
vix = db.getPriceHistory('vix', '1day')

# get pct contango from vixts
vix_ts_pctContango = vixts.getVixTermStructurePctContango(fourToSeven=True)

# join vixm and vix close columns on date
vixm_vix = vixm.join(vix['close'], on='Date', rsuffix='_vix')

# add fourtosevenmocontango column
vixm_vix = vixm_vix.join(vix_ts_pctContango['fourToSevenMoContango'], on='Date')

# add column with vixm close - vix close
vixm_vix['closeSpread'] = vixm_vix['close'] - vixm_vix['close_vix']

# add column with vixm close pct change
vixm_vix['closePctChange'] = vixm_vix['close'].pct_change()

# add column with vix close pct change
vixm_vix['closePctChange_vix'] = vixm_vix['close_vix'].pct_change()

# reset index
vixm_vix.reset_index(inplace=True)

print(vixm_vix)

# select only the rows where vix close > vixm close
datesWithNegativeSpread = vixm_vix[vixm_vix['close_vix'] > vixm_vix['close']]

# Plot results

# set seaborn style
sns.set()

# pariplot with closeSpread, closePctChange, closePctChange_vix, fourToSevenMoContango
# add a column that is 'contango' if fourToSevenMoContango is positive, 'backwardation' if negative
vixm_vix['contango'] = vixm_vix['fourToSevenMoContango'].apply(lambda x: 'contango' if x > 0 else 'backwardation')
sns.pairplot(vixm_vix[['fourToSevenMoContango', 'closeSpread', 'closePctChange', 'closePctChange_vix', 'contango']], height=2.5, hue='contango')

## MULTIAXIS LINEPLOT
#
#ax1 = sns.lineplot(x='Date', y='closeSpread', data=vixm_vix)
#ax1.legend(['vixm - vix'])
#ax2 = ax1.twinx() ## setup secondary axis
#sns.lineplot(x='Date', y='fourToSevenMoContango', data=vixm_vix, ax=ax2, color='green')

#sns.lineplot(x='Date', y='closePctChange', data=vixm_vix, ax=ax2, color='green')
#sns.lineplot(x='Date', y='closePctChange_vix', data=vixm_vix, ax=ax2, color='red')
#
####

# SCATTER: closeSpread vs fourtosevenmocontango
#sns.regplot(x='fourToSevenMoContango', y='closeSpread', data=vixm_vix, scatter=True)

# LINE: closeSpread over time
#sns.lineplot(x='Date', y='closeSpread', data=vixm_vix)

plt.show()


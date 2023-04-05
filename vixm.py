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

# add column with vixm close - vix close
vixm_vix['closeSpread'] = vixm_vix['close'] - vixm_vix['close_vix']

# add column with vixm close pct change
vixm_vix['closePctChange'] = vixm_vix['close'].pct_change()

# add column with vix close pct change
vixm_vix['closePctChange_vix'] = vixm_vix['close_vix'].pct_change()

# reset index
vixm_vix.reset_index(inplace=True)


# select only the rows where vix close > vixm close
datesWithNegativeSpread = vixm_vix[vixm_vix['close_vix'] > vixm_vix['close']]

# using seaborn, plot dualaxis lineplot of closeSpread, closePctChange, closePctChange_vix, with x axis as date, and closeSpread on a secondary axis
sns.set()
"""ax1 = sns.lineplot(x='Date', y='closeSpread', data=vixm_vix)
ax1.legend(['vixm - vix'])
ax2 = ax1.twinx() ## setup secondary axis
sns.lineplot(x='Date', y='closePctChange', data=vixm_vix, ax=ax2, color='green')
sns.lineplot(x='Date', y='closePctChange_vix', data=vixm_vix, ax=ax2, color='red')
ax2.legend(['vixm pct change', 'vix pct change'])"""

# plot historgram of closeSpread, highlight the closespread from the last 5 days in red

sns.distplot(vixm_vix['closeSpread'], bins=50)

# on the same plot, highlight the closespread from the last 5 days in red
#sns.distplot(datesWithNegativeSpread['closeSpread'], bins=50, color='red')

# plot heatmap of closespread vs vixm pct change
#sns.heatmap(vixm_vix[['closeSpread', 'closePctChange']].corr(), annot=True)

#sns.pairplot(datesWithNegativeSpread[['closeSpread', 'closePctChange', 'closePctChange_vix']], height=2.5)

plt.show()

print(vixm_vix)
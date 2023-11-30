import pandas as pd 
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf

from rich import print
from utils import utils

"""
    This function calculates the momentum feature for a given pxhistory, lag, and shift 
    inputs:
        pxhistory: dataframe of px history that includes a logReturn column
        lag: number of days to look back for pct change (momo)
        shift: number of days to shift momo
"""

def calcMomoFactor(universe, lag=1, shift=1, lagmomo=False):
    returns = universe.groupby('symbol', group_keys=False).apply(lambda group: (
    group.sort_values(by='date')
         .assign(momo=lambda x: (x['close'] / x['close'].shift(lag)) - 1,
                 lagmomo=lambda x: x['momo'].shift(shift))
        )
    ).reset_index(drop=True)
    if lagmomo == False:
        returns.drop(columns=['lagmomo'], inplace=True)
    return returns

"""
    This function returns an array of momoPeriods representing the top five r2 values for a given pxHistory
    inputs:
        pxHistory: dataframe of px history that includes a logReturn column
        top: number of momoPeriods to return
"""

def getTopMomoPeriods(pxHistory, top=5, **kwargs):
    print('[yellow]Calculating top %s momo periods...[/yellow]'%(top))
    momoPeriodMax = kwargs.get('rangeEnd', 252)
    fwdReturnPeriodMax = kwargs.get('fwdReturns', 101)


    # calculate forwardReturns for each fwdReturnPeriod in rangeStart to rangeEnd
    startTime = pd.Timestamp.now()
    for forwardReturnPeriod in range(1, fwdReturnPeriodMax):
        pxHistory['fwdReturns%s'%(forwardReturnPeriod)] = pxHistory['close'].pct_change(forwardReturnPeriod).shift(-forwardReturnPeriod)
        pxHistory = pxHistory.copy()

    # get momo for each ? in momoPeriods
   
    for period in range(1, momoPeriodMax):
        pxHistory = calcMomoFactor(pxHistory, lag=period)
        pxHistory.rename(columns={'momo': 'momo%s'%(period), 'lagmomo': 'lagMomo%s'%(period)}, inplace=True)
        pxHistory = pxHistory.copy()

    # for each momo and fowardReturnPeriod, calculate r2
    r2 = pd.DataFrame()
    startTime = pd.Timestamp.now()
    for momoPeriod in range(1, momoPeriodMax):
        for forwardReturnPeriod in range(1, fwdReturnPeriodMax):
            r2_ = smf.ols(formula="fwdReturns%s ~ momo%s"%(forwardReturnPeriod, momoPeriod), data=pxHistory).fit()
            r2 = r2._append({'momoPeriod': int(momoPeriod), 'fwdReturnPeriod': int(forwardReturnPeriod), 'r2': r2_.rsquared}, ignore_index=True)
    print('[green] Seconds to calculate r2:[/green] %s'%(pd.Timestamp.now() - startTime).seconds)

    # set dtype to int for momoPeriod and forwardReturnPeriod
    r2[['momoPeriod', 'fwdReturnPeriod']] = r2[['momoPeriod', 'fwdReturnPeriod']].astype(int)
    # sort by r2 and return the requested number of r2s
    sorted_r2 = r2.sort_values(by='r2', ascending=False).head(top).reset_index(drop=True)

    return sorted_r2
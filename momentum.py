import config 
import pandas as pd 
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf
import interface_analysisOptimizations as ao 

from ast import literal_eval
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

def calc_correlation(pxHistory_, momoPeriod, forwardReturnPeriod):
    # start timer 
   # startTime = pd.Timestamp.now()
    
    # add forward returns and momo columns
    pxHistory_['fwdReturns%s'%(forwardReturnPeriod)] = pxHistory_['close'].pct_change(forwardReturnPeriod).shift(-forwardReturnPeriod)
    pxHistory_ = calcMomoFactor(pxHistory_, lag=momoPeriod)
    pxHistory_.rename(columns={'momo': 'momo%s'%(momoPeriod)}, inplace=True)
    print('Calculating correlation for momo%s and fwdReturns%s'%(momoPeriod, forwardReturnPeriod))
    # calculate correlation
    correl = utils.calcCorrelation(pxHistory_, 'momo%s'%(momoPeriod), 'fwdReturns%s'%(forwardReturnPeriod))
    #print('[green] Time to add momo & rtrn columns:[/green] %s'%(pd.Timestamp.now() - startTime).microseconds)
    
    return correl

def _calc_optimized_momo_periods(pxHistory, top, **kwargs):
    momoPeriodMax = kwargs.get('momoPeriodMax', 361) # add 1 day
    fwdReturnPeriodMax = kwargs.get('fwdReturnPeriodMax', 361) # add 1 day

    # make dataframe of momoPeriods and fwdReturnPeriods to calculate correlation for
    correl = pd.DataFrame(columns=['momoPeriod', 'fwdReturnPeriod', 'correl'])
    correl['momoPeriod'] = range(1, momoPeriodMax)
    correl['fwdReturnPeriod'] = correl['momoPeriod'].apply(lambda x: range(1, fwdReturnPeriodMax)) 
    correl = correl.explode('fwdReturnPeriod') # flatten the fwdReturnPeriod column
    correl.reset_index(drop=True, inplace=True)

    # calculate correlations 
    starttimer = pd.Timestamp.now()
    correl['correl'] = correl[['momoPeriod', 'fwdReturnPeriod']].apply(lambda x: calc_correlation(pxHistory, x['momoPeriod'], x['fwdReturnPeriod']), axis=1)
    print('[yellow]  correl dataframe cycle time:[/yellow] %.2fs'%(pd.Timestamp.now() - starttimer).total_seconds())
    
    # sort and return top values 
    correl.sort_values(by='correl', ascending=False, inplace=True)
    return correl.head(top).reset_index(drop=True)

"""
    This function returns an array of momoPeriods and fwd returns that have the highest correlation 
    inputs:
        pxHistory: dataframe of px history that includes a logReturn column
        top: number of momoPeriods to return
    returns:
        dataframe of top [momoPeriods, fwdReturnPeriods] sorted by r2 values
"""
def getTopMomoPeriods(pxHistory, top=5, **kwargs):
    print('[yellow]Calculating top %s momo periods...[/yellow]'%(top))
    momoPeriodMax = kwargs.get('rangeEnd', 360)
    fwdReturnPeriodMax = kwargs.get('fwdReturns', 360)
    startTime = pd.Timestamp.now()

    # Calculate r2 for each [momoPeriod] and [fwdReturnPeriod]
    correl = pd.DataFrame(columns=['momoPeriod', 'fwdReturnPeriod', 'correl'])
    for momoPeriod in range(1, momoPeriodMax):
        startTime_inner = pd.Timestamp.now()
        for forwardReturnPeriod in range(1, fwdReturnPeriodMax):
            correl_ = calc_correlation(pxHistory, momoPeriod, forwardReturnPeriod)
            correl.loc[len(correl)] = {'momoPeriod': int(momoPeriod), 'fwdReturnPeriod': int(forwardReturnPeriod), 'correl': correl_}
        print('[yellow] time for inner loop %s/%s:[/yellow] %.2fs'%(momoPeriod, momoPeriodMax, (pd.Timestamp.now() - startTime_inner).total_seconds()))
            

    print('[green] Time to optimize vars for highest correlation:[/green] %.2fm'%((pd.Timestamp.now() - startTime).total_seconds()/60))
    
    sorted_correl = correl.sort_values(by='correl', ascending=False).head(top).reset_index(drop=True)
    print(sorted_correl)
    return sorted_correl

def getTopMomoPeriods_optimized(pxHistory, top=5, **kwargs):
    print('[yellow]Getting top %s momo periods...[/yellow]'%(top))
    momoPeriodMax = kwargs.get('rangeEnd', 362) # add 1 day
    fwdReturnPeriodMax = kwargs.get('fwdReturns', 362) # add 1 day

    analysis_name = 'opt_momo_fwdReturn'

    # check if we have optimized variables already 
    optimization_db = ao.AnalysisOptimizationsDB(config.dbname_analysisOptimizations)

    opt_vars=optimization_db.get_analysis_variables(pxHistory['symbol'][0], analysis_name)

    if opt_vars is not None: # return optimized variables from db
        # convert strings to lists
        opt_vars['momoPeriod'] = opt_vars['momoPeriod'].apply(lambda x: literal_eval(x))
        fwdReturnPeriods = opt_vars['fwdReturnPeriod'].apply(lambda x: literal_eval(x))[0]
        # explode the lists into rows
        opt_vars = opt_vars.explode('momoPeriod').reset_index(drop=True)
        opt_vars['fwdReturnPeriod'] = opt_vars.apply(lambda row: fwdReturnPeriods[row.name], axis=1)
        # calculcate correlation
        opt_vars['correl'] = opt_vars[['momoPeriod', 'fwdReturnPeriod']].apply(lambda x: calc_correlation(pxHistory, x['momoPeriod'], x['fwdReturnPeriod']), axis=1)
        # disconnect from db and return optimized variables
        optimization_db.disconnect()
        return opt_vars
    else: # calculate optimized variables since we don't have them saved
        print('[yellow]  no optimized variables found, calculating...[/yellow]')
        opt_momo_periods = _calc_optimized_momo_periods(pxHistory, top, momoPeriodMax=momoPeriodMax, fwdReturnPeriodMax=fwdReturnPeriodMax)
        optimization_db.save_opt_variables(pxHistory['symbol'][0], analysis_name, opt_momo_periods)
        optimization_db.disconnect()
        return opt_momo_periods

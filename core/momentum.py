import config 
import pandas as pd 
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf
from interface import interface_analysisOptimizations as ao 

from core import indicators
from ast import literal_eval
from rich import print
from utils import utils

"""
    Calculates momentum factor for a given pxhistory, lag, and shift 
    inputs:
        pxhistory: dataframe of px history that includes a logReturn column
        lag: lookback period 
        shift: (optional) number of periods to shift momo
"""
def calcMomoFactor(universe, lag=1, shift=1, lagmomo=False):
    # returns = universe.groupby('symbol', group_keys=False).apply(lambda group: (
    # group.sort_values(by='date')
    #      .assign(momo=lambda x: (x['close'] / x['close'].shift(lag)) - 1,
    #              lagmomo=lambda x: x['momo'].shift(shift))
    #     )
    # ).reset_index(drop=True)
    # if lagmomo == False:
    #     returns.drop(columns=['lagmomo'], inplace=True)

    return indicators.momentum_factor(universe, 'close', lag=lag, shift=shift, lag_momo=lagmomo)

"""
    Returns correlation between momoperiod and fwdreturnperiod 
"""
def calc_correlation(pxHistory_, momoPeriod, forwardReturnPeriod):
  
    # add forward returns and momo columns
    pxHistory_['fwdReturns%s'%(forwardReturnPeriod)] = pxHistory_['close'].pct_change(forwardReturnPeriod).shift(-forwardReturnPeriod)
    pxHistory_ = calcMomoFactor(pxHistory_, lag=momoPeriod)
    pxHistory_.rename(columns={'momo': 'momo%s'%(momoPeriod)}, inplace=True)
    # calculate correlation
    correl = utils.calcCorrelation(pxHistory_, 'momo%s'%(momoPeriod), 'fwdReturns%s'%(forwardReturnPeriod))
    
    return correl

"""
    Returns the momoPeriod and fwdReturnPeriod combod with the highest correlation for the given pxHistory
"""
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
    This function returns a dataframe of momoPeriods and fwd returns that have the highest correlation
"""
def getTopMomoPeriods(pxHistory, top=5, **kwargs):
    momoPeriodMax = kwargs.get('rangeEnd', 362) # add 1 day
    fwdReturnPeriodMax = kwargs.get('fwdReturns', 362) # add 1 day

    analysis_name = 'opt_momo_fwdReturn'

    # check if we have optimized variables already 
    optimization_db = ao.AnalysisOptimizationsDB(config.dbname_analysisOptimizations)

    opt_vars=optimization_db.get_analysis_variables(pxHistory['symbol'][0], analysis_name)

    if opt_vars is not None: # return optimized variables from db
        print('[yellow]Getting top %s momo periods from db...[/yellow]'%(top))
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

"""
    Implements a crossover function for momoperiod and its ema 
"""
def __DEPRECATED__calc_momo_ema_crossover(pxHistory, momoPeriod, emaPeriod):
    # add momo and ema columns
    pxHistory = calcMomoFactor(pxHistory, lag=momoPeriod)
    pxHistory['momo%s'%(momoPeriod)] = pxHistory['momo%s'%(momoPeriod)].shift(1)
    pxHistory['momoEma%s'%(momoPeriod)] = pxHistory['momo%s'%(momoPeriod)].ewm(span=emaPeriod).mean()
    # calculate crossover
    pxHistory['momoEmaCrossover%s'%(momoPeriod)] = pxHistory['momo%s'%(momoPeriod)] - pxHistory['momoEma%s'%(momoPeriod)]
    return pxHistory    

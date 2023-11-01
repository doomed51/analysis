import pandas as pd 
import matplotlib.pyplot as plt

from utils import utils

"""
    This function calculates the momentum feature for a given pxhistory, lag, and shift 
    inputs:
        pxhistory: dataframe of px history that includes a logReturn column
        lag: number of days to look back for pct change (momo)
        shift: number of days to shift momo
"""

def calcMomoFactor(universe, lag=1, shift=1):
    returns = universe.groupby('symbol').apply(lambda group: (
    group.sort_values(by='date')
         .assign(momo=lambda x: (x['close'] / x['close'].shift(lag)) - 1,
                 lagmomo=lambda x: x['momo'].shift(shift))
         .dropna()
        )
    ).reset_index(drop=True)
    
    return returns


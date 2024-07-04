"""
    This module acts as the interface to calculate indicators for a given dataframe and column names
"""

import pandas as pd
import numpy as np

def momenturm_factor(df, colname, lag=1, shift=1, lag_momo=False):
    """
    Calculates momentum factor for a given pxhistory, lag, and shift 
    inputs:
        pxhistory: dataframe of px history that includes a logReturn column
        lag: lookback period 
        shift: (optional) number of periods to shift momo
    """
    returns = df.groupby('symbol', group_keys=False).apply(lambda group: (
    group.sort_values(by='date')
         .assign(momo=lambda x: (x[colname] / x[colname].shift(lag)) - 1,
                 lagmomo=lambda x: x['momo'].shift(shift))
        )
    ).reset_index(drop=True)
    if lag_momo == False:
        returns.drop(columns=['lagmomo'], inplace=True)
    return returns

def moving_average_crossover(df, colname_long, colname_short):
    """
    Calculates the moving average crossover for a given dataframe and column names. 
    inputs:
        df: dataframe with price history
        colname_long: column name for the long moving average
        colname_short: column name for the short moving average
    """
     
    df['%s_%s_crossover'%(colname_long, colname_short)] = df[colname_short] - df[colname_long]
    # np.where(df[colname_short] > df[colname_long], 1, 0)
    return df

def relative_volatility_index(df, colname, length):
    """
    Calculates the relative volatility index for a given dataframe and column name. 
    Calculation: 
        1. Identify 'up' and 'down' periods/candles. An 'up' period is when the 
            closing price is higher than the previous periods close, while a 
            "down" period is the opposite.
        2. Calculate the standard deviation of the 'up' and 'down' days over 
            the chosen period.
        3. Divide the standard deviation of 'up' periods by the standard deviation 
            of 'down' periods, then multiply by 100 to get the RVI.
    
    inputs:
        df: dataframe with price history
        colname: column name to calculate RVI on
        length: lookback period
    """
    # Calculate the standard deviation of the closing prices
    df['std'] = df[colname].rolling(window=length).std()
    
    # Calculate the up standard deviation and down standard deviation
    df['std_up'] = np.where(df[colname] > df[colname].shift(1), df['std'], 0)
    df['std_down'] = np.where(df[colname] < df[colname].shift(1), df['std'], 0)
    
    # Calculate the average of up and down standard deviations
    avg_std_up = df['std_up'].rolling(window=length).mean()
    avg_std_down = df['std_down'].rolling(window=length).mean()
    
    # drop stdup and down columns
    df.drop(columns=['std', 'std_up', 'std_down'], inplace=True)

    # Calculate the RVI
    df['%s_rvi'%(colname)] = 100 * avg_std_up / (avg_std_up + avg_std_down)

    return df 
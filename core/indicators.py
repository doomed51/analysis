"""
    This module acts as the interface to calculate indicators for a given dataframe and column names
"""

import pandas as pd
import numpy as np
import ffn

from numba import jit, njit
from numpy.lib.stride_tricks import sliding_window_view


@njit
def exponentially_weighted_moving_average(values, length, alpha):
    """
    Calculates the exponentially weighted moving average of a series.
    inputs:
        arr: array of prices
        length: lookback period
        alpha: smoothing factor for calculating weights. lower alpha gives more weight to recent prices
    """
    weights = np.array([(1 - alpha) * (alpha ** i) for i in range(length)])[::-1]
    # print(weights)
    result = np.empty(len(values))

    for i in range(len(result)):
        # print(values[i])
        # print last 10 values in values 
        if i < length:
            result[i] = np.nan
        else:
            # print(values[i-length:i])
            result[i] = np.dot(values[i-length:i], weights) / weights.sum()
    
    # print('\n')
    # print(weights) 
    # print(len(values))
    
    return result

@njit 
def compute_deciles_with_rank(values, window_size):   
    """
        Calculate the deciles of a series of values.
    """
    windows = sliding_window_view(values, window_size)

    rolling_deciles = np.empty((windows.shape[0], 9))
    decile_ranks = np.empty(len(values))
    for i in range(windows.shape[0]):
        # deciles[i, :] = compute_deciles(windows[i])
        rolling_deciles[i, :] = np.percentile(windows[i], np.arange(10, 100, 10))
        current_value = values[i + window_size - 1]
        decile_ranks[i + window_size - 1] = find_decile(current_value, rolling_deciles[i])

    decile_ranks[:window_size - 1] = np.nan
    # return np.percentile(values, window, np.arange(10, 100, 10))
    return rolling_deciles, decile_ranks

@njit
def find_decile(value, deciles): 
    """
        Find the decile of a value given a list of deciles.
    """
    for i, decile in enumerate(deciles):
        if value <= decile:
            return i
    return 9

@njit
def momentum(prices, lookback):
    n = len(prices)
    momo = np.empty(n)
    
    for i in range(n):
        if i >= lookback:
            momo[i] = (prices[i] / prices[i - lookback]) - 1
        else:
            momo[i] = np.nan
    
    return momo

@njit
def momentum2(prices, lookback):
    n = len(prices)
    momo = np.empty(n)
    
    # Initialize arrays with NaN
    momo[:] = np.nan
    
    # Find the first non-NaN index
    start_idx = 0
    for i in range(n):
        if not np.isnan(prices[i]):
            start_idx = i
            break
    
    for i in range(start_idx + lookback, n):
        momo[i] = (prices[i] / prices[i - lookback]) - 1
    
    return momo

@njit
def rolling_zscore(values, rollingWindow):
    n = len(values)
    zscores = np.empty(n)
    zscores[:] = np.nan  # Initialize with NaNs

    for i in range(rollingWindow - 1, n):
        window = values[i - rollingWindow + 1:i + 1]
        mean = np.mean(window)
        std = np.std(window)
        zscores[i] = (values[i] - mean) / std

    return zscores

@njit
def zscore(values, rollingWindow=252, rescale=False):
    """
    Calculate the z-score of a column.
    Params: 
        colname: str column name to calculate z-score on
        rollingWindow: int rolling window to calculate z-score on. Setting to 0 uses entire population 
        _pxHistory: pd.DataFrame to calculate z-score on. Default is None, which uses the objects default pxhistory
    """
    
    if rollingWindow == 0:
        zscores = (values - np.mean(values)) / np.std(values)
    else:
        zscores = rolling_zscore(values, rollingWindow)

    # if rescale:
    #     zscores = ffn.rescale(zscores, -1, 1)

    return zscores

@njit
def rolling_std(arr, window):
    """
    Calculate the rolling standard deviation of a column.
    Params: 
        arr: np.array column to calculate rolling std on
        window: int rolling window 
    """
    result = np.empty(len(arr))
    result[:] = np.nan  # Initialize with NaNs
    for i in range(window - 1, len(arr)):
        result[i] = np.std(arr[i - window + 1:i])
    return result

def slope(df, colname, lookback_periods=10):
    """
    Calculates the slope of a given column over a lookback period. 
    inputs:
        df: dataframe with price history
        colname: column name to calculate the slope on
        lookback_periods: lookback period
    """
    df['%s_slope'%(colname)] = df[colname].rolling(window=lookback_periods).apply(lambda x: np.polyfit(np.arange(len(x)), x, 1)[0], raw=True)
    return df

def intra_day_cumulative_signal(pxhistory, colname, lookback_period=10, intraday_reset=False):
    """
    Adds column colname_CUMSUM_lookback_periodsP to the dataframe.
    inputs:
        df: dataframe with price history
        colname: column name to calculate the signal on
        lookback_periods: list of lookback periods to calculate the signal over
    """
    cumsum_col_name = '%s_cumsum'%(colname)
    if intraday_reset == True:
        # explicitly convert date to datetime obj 
        pxhistory['date'] = pd.to_datetime(pxhistory['date'])
        # Add a column to identify the day
        pxhistory['day'] = pxhistory['date'].dt.date

        # Calculate cumulative sum within each group (each day)
        pxhistory[cumsum_col_name] = pxhistory.groupby('day')[colname].cumsum()
        
        # Drop the auxiliary column used for day identification
        pxhistory.drop(columns=['day'], inplace=True)
    else:
        pxhistory[cumsum_col_name] = pxhistory[colname].rolling(window=lookback_period, min_periods=1).sum()
    return pxhistory

def momentum_factor(df, colname, lag=1, shift=1, lag_momo=False, use_absolute_values=False):
    """
    Calculates momentum factor for a given pxhistory, lag, and shift 
    inputs:
        pxhistory: dataframe of px history that includes a logReturn column
        lag: lookback period 
        shift: (optional) number of periods to shift momo
    """
    
    if use_absolute_values: 
        df['%s_abs'%(colname)] = df[colname].abs
        colname = '%s_abs'%(colname)

    returns = df.groupby('symbol', group_keys=False).apply(lambda group: (
    group.sort_values(by='date')
         .assign(momo=lambda x: (x[colname] / x[colname].shift(lag)) - 1,
                 lagmomo=lambda x: x['momo'].shift(shift))
        )
    ).reset_index(drop=True)

    if lag_momo == False:
        returns.drop(columns=['lagmomo'], inplace=True)
    return returns

def weighted_moving_average_returnsSeries(px_series, length):
    """
    Calculates the weighted moving average of a series. 
    inputs:
        px_series: series of prices
        length: lookback period
    """
    weights = np.arange(1, length + 1)
    return pd.Series(px_series).rolling(window=length).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)

def moving_average_crossover(df, colname_long, colname_short):
    """
    Adds column colname_long_colname_short_CROSSOVER 
    inputs:
        df: dataframe with price history
        colname_long: column name for the long moving average
        colname_short: column name for the short moving average
    """
     
    df['%s_%s_crossover'%(colname_long, colname_short)] = df[colname_short] - df[colname_long]
    # np.where(df[colname_short] > df[colname_long], 1, 0)
    return df

def moving_average_weighted(df, colname, length):
    """
    Calculates the weighted moving average of a series. 
    inputs:
        df: dataframe with price history
        colname: column name to calculate WMA on
        length: lookback period
    """
    weights = np.arange(1, length + 1)
    df['%s_wma'%(colname)] = df[colname].rolling(window=length).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
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

def rolling_deciles_with_rank(pxhistory, colname, window_size):
    
    values = pxhistory[colname].values
    return compute_deciles_with_rank(values, window_size)
    
    # windows = sliding_window_view(values, window_size)
    # deciles = np.empty((windows.shape[0], 9))
    # for i in range(windows.shape[0]):
    #     deciles[i, :] = compute_deciles(windows[i])
    # return deciles 

def calculate_decile_vanilla_pandas(numBuckets, colname, pxhistory, rollingWindow=252):
    if rollingWindow > 0:
        pxhistory['%s_ntile' % colname] = pxhistory[colname].rolling(rollingWindow).apply(lambda x: pd.qcut(x, numBuckets, labels=False, duplicates='drop').iloc[-1], raw=False)
    else:
        pxhistory['%s_ntile' % colname] = pd.qcut(pxhistory[colname], numBuckets, labels=False, duplicates='drop')
    
    return pxhistory 


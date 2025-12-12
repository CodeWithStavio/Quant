"""
Helper functions for Jesse strategies
-------------------------------------
Common utilities used across all strategy implementations.
"""

import numpy as np
from typing import Union, Tuple, Optional


def crossover(series1: np.ndarray, series2: Union[np.ndarray, float]) -> bool:
    """
    Check if series1 crosses above series2.

    Args:
        series1: First data series (e.g., fast MA)
        series2: Second data series or constant value (e.g., slow MA)

    Returns:
        True if crossover occurred in the last bar
    """
    if isinstance(series2, (int, float)):
        series2 = np.full_like(series1, series2)

    if len(series1) < 2:
        return False

    return series1[-2] <= series2[-2] and series1[-1] > series2[-1]


def crossunder(series1: np.ndarray, series2: Union[np.ndarray, float]) -> bool:
    """
    Check if series1 crosses below series2.

    Args:
        series1: First data series (e.g., fast MA)
        series2: Second data series or constant value (e.g., slow MA)

    Returns:
        True if crossunder occurred in the last bar
    """
    if isinstance(series2, (int, float)):
        series2 = np.full_like(series1, series2)

    if len(series1) < 2:
        return False

    return series1[-2] >= series2[-2] and series1[-1] < series2[-1]


def is_bullish_candle(open_price: float, close_price: float) -> bool:
    """Check if candle is bullish (close > open)"""
    return close_price > open_price


def is_bearish_candle(open_price: float, close_price: float) -> bool:
    """Check if candle is bearish (close < open)"""
    return close_price < open_price


def calculate_position_size(
    balance: float,
    risk_percent: float,
    entry_price: float,
    stop_loss_price: float
) -> float:
    """
    Calculate position size based on risk percentage.

    Args:
        balance: Account balance
        risk_percent: Risk per trade as decimal (e.g., 0.02 for 2%)
        entry_price: Entry price
        stop_loss_price: Stop loss price

    Returns:
        Position size in base currency
    """
    risk_amount = balance * risk_percent
    price_diff = abs(entry_price - stop_loss_price)

    if price_diff == 0:
        return 0

    position_size = risk_amount / price_diff
    return position_size


def atr_stop_loss(
    entry_price: float,
    atr_value: float,
    multiplier: float = 2.0,
    is_long: bool = True
) -> float:
    """
    Calculate stop loss based on ATR.

    Args:
        entry_price: Entry price
        atr_value: Current ATR value
        multiplier: ATR multiplier (default 2.0)
        is_long: True for long positions, False for short

    Returns:
        Stop loss price
    """
    atr_distance = atr_value * multiplier

    if is_long:
        return entry_price - atr_distance
    else:
        return entry_price + atr_distance


def atr_take_profit(
    entry_price: float,
    atr_value: float,
    multiplier: float = 3.0,
    is_long: bool = True
) -> float:
    """
    Calculate take profit based on ATR.

    Args:
        entry_price: Entry price
        atr_value: Current ATR value
        multiplier: ATR multiplier (default 3.0)
        is_long: True for long positions, False for short

    Returns:
        Take profit price
    """
    atr_distance = atr_value * multiplier

    if is_long:
        return entry_price + atr_distance
    else:
        return entry_price - atr_distance


def calculate_risk_reward(
    entry: float,
    stop_loss: float,
    take_profit: float
) -> float:
    """
    Calculate risk/reward ratio.

    Args:
        entry: Entry price
        stop_loss: Stop loss price
        take_profit: Take profit price

    Returns:
        Risk/reward ratio
    """
    risk = abs(entry - stop_loss)
    reward = abs(take_profit - entry)

    if risk == 0:
        return 0

    return reward / risk


def detect_divergence(
    price_series: np.ndarray,
    indicator_series: np.ndarray,
    lookback: int = 14
) -> Tuple[bool, bool]:
    """
    Detect bullish and bearish divergence.

    Args:
        price_series: Price data (typically close prices)
        indicator_series: Indicator data (e.g., RSI, MACD)
        lookback: Number of bars to look back

    Returns:
        Tuple of (bullish_divergence, bearish_divergence)
    """
    if len(price_series) < lookback or len(indicator_series) < lookback:
        return False, False

    price = price_series[-lookback:]
    indicator = indicator_series[-lookback:]

    # Find local lows and highs
    price_lows = []
    price_highs = []
    ind_lows = []
    ind_highs = []

    for i in range(1, len(price) - 1):
        # Local low
        if price[i] < price[i-1] and price[i] < price[i+1]:
            price_lows.append((i, price[i]))
            ind_lows.append((i, indicator[i]))
        # Local high
        if price[i] > price[i-1] and price[i] > price[i+1]:
            price_highs.append((i, price[i]))
            ind_highs.append((i, indicator[i]))

    bullish_div = False
    bearish_div = False

    # Check for bullish divergence (price lower low, indicator higher low)
    if len(price_lows) >= 2:
        if price_lows[-1][1] < price_lows[-2][1] and ind_lows[-1][1] > ind_lows[-2][1]:
            bullish_div = True

    # Check for bearish divergence (price higher high, indicator lower high)
    if len(price_highs) >= 2:
        if price_highs[-1][1] > price_highs[-2][1] and ind_highs[-1][1] < ind_highs[-2][1]:
            bearish_div = True

    return bullish_div, bearish_div


def calculate_slope(series: np.ndarray, period: int = 5) -> float:
    """
    Calculate the slope of a series using linear regression.

    Args:
        series: Data series
        period: Lookback period

    Returns:
        Slope value
    """
    if len(series) < period:
        return 0

    y = series[-period:]
    x = np.arange(period)

    # Linear regression
    slope = np.polyfit(x, y, 1)[0]
    return slope


def percentage_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change between two values"""
    if old_value == 0:
        return 0
    return ((new_value - old_value) / old_value) * 100


def normalize(series: np.ndarray, min_val: float = 0, max_val: float = 100) -> np.ndarray:
    """
    Normalize a series to a specified range.

    Args:
        series: Input data series
        min_val: Minimum output value
        max_val: Maximum output value

    Returns:
        Normalized series
    """
    s_min = np.min(series)
    s_max = np.max(series)

    if s_max == s_min:
        return np.full_like(series, (min_val + max_val) / 2)

    return min_val + (series - s_min) * (max_val - min_val) / (s_max - s_min)


def z_score(series: np.ndarray, lookback: int = 20) -> float:
    """
    Calculate z-score of the latest value.

    Args:
        series: Data series
        lookback: Lookback period for mean and std

    Returns:
        Z-score value
    """
    if len(series) < lookback:
        return 0

    data = series[-lookback:]
    mean = np.mean(data)
    std = np.std(data)

    if std == 0:
        return 0

    return (series[-1] - mean) / std


def is_higher_high(highs: np.ndarray, lookback: int = 10) -> bool:
    """Check if current high is higher than previous local high"""
    if len(highs) < lookback:
        return False

    recent = highs[-lookback:]
    max_idx = np.argmax(recent[:-1])

    return recent[-1] > recent[max_idx]


def is_lower_low(lows: np.ndarray, lookback: int = 10) -> bool:
    """Check if current low is lower than previous local low"""
    if len(lows) < lookback:
        return False

    recent = lows[-lookback:]
    min_idx = np.argmin(recent[:-1])

    return recent[-1] < recent[min_idx]


def is_higher_low(lows: np.ndarray, lookback: int = 10) -> bool:
    """Check if current low is higher than previous local low"""
    if len(lows) < lookback:
        return False

    recent = lows[-lookback:]
    min_idx = np.argmin(recent[:-1])

    return recent[-1] > recent[min_idx]


def is_lower_high(highs: np.ndarray, lookback: int = 10) -> bool:
    """Check if current high is lower than previous local high"""
    if len(highs) < lookback:
        return False

    recent = highs[-lookback:]
    max_idx = np.argmax(recent[:-1])

    return recent[-1] < recent[max_idx]

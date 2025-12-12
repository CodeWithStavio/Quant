"""
ADX_004: ADX Trend Filter Strategy
----------------------------------
Use ADX as a trend filter with MA crossovers.
Only trade when ADX indicates strong trend.

Entry Long: MA bullish + ADX strong trend
Entry Short: MA bearish + ADX strong trend

Optimal Timeframes: 1h, 4h
Complexity: 4/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class ADXTrendFilter(Strategy):
    """ADX Trend Filter Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ADX_004"
        self.strategy_name = "ADX Trend Filter"
        self.complexity = 4
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'adx_period', 'type': int, 'min': 10, 'max': 21, 'default': 14},
            {'name': 'adx_threshold', 'type': float, 'min': 20, 'max': 35, 'default': 25},
            {'name': 'fast_ma', 'type': int, 'min': 8, 'max': 15, 'default': 10},
            {'name': 'slow_ma', 'type': int, 'min': 20, 'max': 30, 'default': 20},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 5.0, 'default': 3.5},
        ]

    def _calculate_adx(self) -> float:
        period = self.hp['adx_period']
        high = self.candles[:, 3]
        low = self.candles[:, 4]
        close = self.candles[:, 2]

        tr = np.zeros(len(self.candles))
        plus_dm = np.zeros(len(self.candles))
        minus_dm = np.zeros(len(self.candles))

        for i in range(1, len(self.candles)):
            tr[i] = max(high[i] - low[i], abs(high[i] - close[i-1]), abs(low[i] - close[i-1]))
            up_move = high[i] - high[i-1]
            down_move = low[i-1] - low[i]
            if up_move > down_move and up_move > 0:
                plus_dm[i] = up_move
            if down_move > up_move and down_move > 0:
                minus_dm[i] = down_move

        atr = np.zeros(len(self.candles))
        plus_di_raw = np.zeros(len(self.candles))
        minus_di_raw = np.zeros(len(self.candles))

        atr[period] = np.sum(tr[1:period+1])
        plus_di_raw[period] = np.sum(plus_dm[1:period+1])
        minus_di_raw[period] = np.sum(minus_dm[1:period+1])

        for i in range(period + 1, len(self.candles)):
            atr[i] = atr[i-1] - (atr[i-1] / period) + tr[i]
            plus_di_raw[i] = plus_di_raw[i-1] - (plus_di_raw[i-1] / period) + plus_dm[i]
            minus_di_raw[i] = minus_di_raw[i-1] - (minus_di_raw[i-1] / period) + minus_dm[i]

        atr = np.where(atr == 0, 1, atr)
        plus_di = 100 * plus_di_raw / atr
        minus_di = 100 * minus_di_raw / atr

        di_sum = plus_di + minus_di
        di_sum = np.where(di_sum == 0, 1, di_sum)
        dx = 100 * np.abs(plus_di - minus_di) / di_sum

        adx = np.zeros(len(self.candles))
        if len(self.candles) > period * 2:
            adx[period * 2] = np.mean(dx[period:period * 2 + 1])
            for i in range(period * 2 + 1, len(self.candles)):
                adx[i] = (adx[i-1] * (period - 1) + dx[i]) / period

        return adx[-1]

    @property
    def adx(self) -> float:
        return self._calculate_adx()

    @property
    def fast_ema(self) -> float:
        return ta.ema(self.candles, period=self.hp['fast_ma'])

    @property
    def slow_ema(self) -> float:
        return ta.ema(self.candles, period=self.hp['slow_ma'])

    @property
    def fast_ema_prev(self) -> float:
        return ta.ema(self.candles[:-1], period=self.hp['fast_ma'])

    @property
    def slow_ema_prev(self) -> float:
        return ta.ema(self.candles[:-1], period=self.hp['slow_ma'])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def strong_trend(self) -> bool:
        return self.adx > self.hp['adx_threshold']

    @property
    def ma_bullish_cross(self) -> bool:
        return self.fast_ema_prev <= self.slow_ema_prev and self.fast_ema > self.slow_ema

    @property
    def ma_bearish_cross(self) -> bool:
        return self.fast_ema_prev >= self.slow_ema_prev and self.fast_ema < self.slow_ema

    @property
    def ma_bullish(self) -> bool:
        return self.fast_ema > self.slow_ema

    @property
    def ma_bearish(self) -> bool:
        return self.fast_ema < self.slow_ema

    def should_long(self) -> bool:
        return self.strong_trend and self.ma_bullish_cross

    def should_short(self) -> bool:
        return self.strong_trend and self.ma_bearish_cross

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry - (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry + (self.atr * self.hp['atr_multiplier_tp'])

    def go_short(self):
        entry = self.price
        stop = entry + (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry - (self.atr * self.hp['atr_multiplier_tp'])

    def update_position(self):
        if self.is_long and self.ma_bearish:
            self.liquidate()
        elif self.is_short and self.ma_bullish:
            self.liquidate()

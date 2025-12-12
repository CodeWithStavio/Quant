"""
ADX_003: ADX Breakout Strategy
------------------------------
Trade breakouts when ADX starts rising from low levels.
Low ADX = consolidation, rising ADX = breakout starting.

Entry: ADX crosses above threshold from below

Optimal Timeframes: 1h, 4h
Complexity: 4/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class ADXBreakout(Strategy):
    """ADX Breakout Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ADX_003"
        self.strategy_name = "ADX Breakout"
        self.complexity = 4
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'adx_period', 'type': int, 'min': 10, 'max': 21, 'default': 14},
            {'name': 'adx_breakout_level', 'type': float, 'min': 20, 'max': 30, 'default': 25},
            {'name': 'lookback', 'type': int, 'min': 10, 'max': 30, 'default': 20},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 5.0, 'default': 3.5},
        ]

    def _calculate_adx_components(self, candles=None):
        if candles is None:
            candles = self.candles

        period = self.hp['adx_period']
        high = candles[:, 3]
        low = candles[:, 4]
        close = candles[:, 2]

        tr = np.zeros(len(candles))
        plus_dm = np.zeros(len(candles))
        minus_dm = np.zeros(len(candles))

        for i in range(1, len(candles)):
            tr[i] = max(high[i] - low[i], abs(high[i] - close[i-1]), abs(low[i] - close[i-1]))
            up_move = high[i] - high[i-1]
            down_move = low[i-1] - low[i]
            if up_move > down_move and up_move > 0:
                plus_dm[i] = up_move
            if down_move > up_move and down_move > 0:
                minus_dm[i] = down_move

        atr = np.zeros(len(candles))
        plus_di_raw = np.zeros(len(candles))
        minus_di_raw = np.zeros(len(candles))

        if len(candles) > period:
            atr[period] = np.sum(tr[1:period+1])
            plus_di_raw[period] = np.sum(plus_dm[1:period+1])
            minus_di_raw[period] = np.sum(minus_dm[1:period+1])

            for i in range(period + 1, len(candles)):
                atr[i] = atr[i-1] - (atr[i-1] / period) + tr[i]
                plus_di_raw[i] = plus_di_raw[i-1] - (plus_di_raw[i-1] / period) + plus_dm[i]
                minus_di_raw[i] = minus_di_raw[i-1] - (minus_di_raw[i-1] / period) + minus_dm[i]

        atr = np.where(atr == 0, 1, atr)
        plus_di = 100 * plus_di_raw / atr
        minus_di = 100 * minus_di_raw / atr

        di_sum = plus_di + minus_di
        di_sum = np.where(di_sum == 0, 1, di_sum)
        dx = 100 * np.abs(plus_di - minus_di) / di_sum

        adx = np.zeros(len(candles))
        if len(candles) > period * 2:
            adx[period * 2] = np.mean(dx[period:period * 2 + 1])
            for i in range(period * 2 + 1, len(candles)):
                adx[i] = (adx[i-1] * (period - 1) + dx[i]) / period

        return adx, plus_di, minus_di

    @property
    def adx(self) -> float:
        adx, _, _ = self._calculate_adx_components()
        return adx[-1]

    @property
    def adx_prev(self) -> float:
        adx, _, _ = self._calculate_adx_components()
        return adx[-2] if len(adx) > 1 else adx[-1]

    @property
    def plus_di(self) -> float:
        _, plus_di, _ = self._calculate_adx_components()
        return plus_di[-1]

    @property
    def minus_di(self) -> float:
        _, _, minus_di = self._calculate_adx_components()
        return minus_di[-1]

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def adx_breakout(self) -> bool:
        """ADX crosses above breakout level from below"""
        return self.adx_prev < self.hp['adx_breakout_level'] and self.adx >= self.hp['adx_breakout_level']

    @property
    def bullish_direction(self) -> bool:
        return self.plus_di > self.minus_di

    @property
    def bearish_direction(self) -> bool:
        return self.minus_di > self.plus_di

    def should_long(self) -> bool:
        return self.adx_breakout and self.bullish_direction

    def should_short(self) -> bool:
        return self.adx_breakout and self.bearish_direction

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
        # Exit when ADX starts falling
        if self.is_long and self.adx < self.adx_prev and self.adx < 20:
            self.liquidate()
        elif self.is_short and self.adx < self.adx_prev and self.adx < 20:
            self.liquidate()

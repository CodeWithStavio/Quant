"""
VOL_010: Accumulation/Distribution (A/D) Strategy
-------------------------------------------------
Larry Williams' A/D line tracks cumulative money flow.
Rising A/D = accumulation, Falling A/D = distribution.

Entry Long: A/D line rising with price
Entry Short: A/D line falling with price

Optimal Timeframes: 1h, 4h
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class ADStrategy(Strategy):
    """Accumulation/Distribution Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "VOL_010"
        self.strategy_name = "Accumulation Distribution"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'ad_ma_period', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'price_ma_period', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 5.0, 'default': 3.5},
        ]

    def _calculate_ad(self, candles=None):
        """Calculate Accumulation/Distribution line"""
        if candles is None:
            candles = self.candles

        high = candles[:, 3]
        low = candles[:, 4]
        close = candles[:, 2]
        volume = candles[:, 5]

        # Money Flow Multiplier = [(Close - Low) - (High - Close)] / (High - Low)
        high_low_diff = high - low
        high_low_diff = np.where(high_low_diff == 0, 1, high_low_diff)

        mf_mult = ((close - low) - (high - close)) / high_low_diff

        # Money Flow Volume = MF Multiplier * Volume
        mf_vol = mf_mult * volume

        # A/D Line = Cumulative sum of MF Volume
        ad_line = np.cumsum(mf_vol)

        return ad_line

    @property
    def ad_line(self) -> float:
        ad = self._calculate_ad()
        return ad[-1]

    @property
    def ad_prev(self) -> float:
        ad = self._calculate_ad()
        return ad[-2] if len(ad) > 1 else ad[-1]

    @property
    def ad_ma(self) -> float:
        ad = self._calculate_ad()
        period = self.hp['ad_ma_period']
        return np.mean(ad[-period:])

    @property
    def price_ma(self) -> float:
        return ta.ema(self.candles, period=self.hp['price_ma_period'])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def ad_rising(self) -> bool:
        return self.ad_line > self.ad_prev

    @property
    def ad_falling(self) -> bool:
        return self.ad_line < self.ad_prev

    @property
    def ad_above_ma(self) -> bool:
        return self.ad_line > self.ad_ma

    @property
    def ad_below_ma(self) -> bool:
        return self.ad_line < self.ad_ma

    @property
    def price_above_ma(self) -> bool:
        return self.close > self.price_ma

    @property
    def price_below_ma(self) -> bool:
        return self.close < self.price_ma

    def should_long(self) -> bool:
        return self.ad_rising and self.ad_above_ma and self.price_above_ma

    def should_short(self) -> bool:
        return self.ad_falling and self.ad_below_ma and self.price_below_ma

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
        # Exit on A/D reversal
        if self.is_long and self.ad_falling and self.ad_below_ma:
            self.liquidate()
        elif self.is_short and self.ad_rising and self.ad_above_ma:
            self.liquidate()

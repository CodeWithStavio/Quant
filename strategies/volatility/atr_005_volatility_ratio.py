"""
ATR_005: Volatility Ratio Strategy
----------------------------------
Jack Schwager's Volatility Ratio for breakout detection.
VR = True Range / (Highest High - Lowest Low over n periods)
VR > 0.5 indicates potential breakout.

Entry: VR breakout in trend direction
Exit: VR contracts

Optimal Timeframes: 1h, 4h
Complexity: 4/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class VolatilityRatio(Strategy):
    """Volatility Ratio Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ATR_005"
        self.strategy_name = "Volatility Ratio"
        self.complexity = 4
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'period', 'type': int, 'min': 10, 'max': 20, 'default': 14},
            {'name': 'vr_threshold', 'type': float, 'min': 0.4, 'max': 0.7, 'default': 0.5},
            {'name': 'ma_period', 'type': int, 'min': 15, 'max': 50, 'default': 20},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 5.0, 'default': 3.5},
        ]

    def _calculate_volatility_ratio(self, candles=None) -> float:
        """Calculate Schwager's Volatility Ratio"""
        if candles is None:
            candles = self.candles

        period = self.hp['period']
        high = candles[:, 3]
        low = candles[:, 4]
        close = candles[:, 2]

        # True Range
        prev_close = close[-2] if len(candles) > 1 else close[-1]
        tr = max(
            high[-1] - low[-1],
            abs(high[-1] - prev_close),
            abs(low[-1] - prev_close)
        )

        # Period range
        highest = np.max(high[-period:])
        lowest = np.min(low[-period:])
        period_range = highest - lowest

        if period_range == 0:
            return 0

        return tr / period_range

    @property
    def volatility_ratio(self) -> float:
        return self._calculate_volatility_ratio()

    @property
    def volatility_ratio_prev(self) -> float:
        return self._calculate_volatility_ratio(self.candles[:-1])

    @property
    def vr_breakout(self) -> bool:
        """VR crosses above threshold"""
        return self.volatility_ratio > self.hp['vr_threshold']

    @property
    def vr_crossed_up(self) -> bool:
        """VR just crossed above threshold"""
        return self.volatility_ratio_prev <= self.hp['vr_threshold'] and self.volatility_ratio > self.hp['vr_threshold']

    @property
    def ma(self) -> float:
        return ta.ema(self.candles, period=self.hp['ma_period'])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def bullish_bar(self) -> bool:
        """Current bar is bullish"""
        return self.close > self.open

    @property
    def bearish_bar(self) -> bool:
        """Current bar is bearish"""
        return self.close < self.open

    def should_long(self) -> bool:
        # VR breakout with bullish bias
        return self.vr_crossed_up and self.bullish_bar and self.close > self.ma

    def should_short(self) -> bool:
        # VR breakout with bearish bias
        return self.vr_crossed_up and self.bearish_bar and self.close < self.ma

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
        # Exit when VR contracts below threshold
        if self.is_long and self.volatility_ratio < self.hp['vr_threshold'] / 2:
            if self.close < self.ma:
                self.liquidate()
        elif self.is_short and self.volatility_ratio < self.hp['vr_threshold'] / 2:
            if self.close > self.ma:
                self.liquidate()

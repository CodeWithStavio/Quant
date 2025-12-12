"""
ATR_002: SuperTrend Strategy
----------------------------
Popular ATR-based trend following indicator.
SuperTrend flips when price crosses bands.

Entry Long: SuperTrend turns bullish (price above lower band)
Entry Short: SuperTrend turns bearish (price below upper band)

Optimal Timeframes: 15m, 1h, 4h
Complexity: 4/10
Crypto Suitability: 9/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class SuperTrendStrategy(Strategy):
    """SuperTrend Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ATR_002"
        self.strategy_name = "SuperTrend"
        self.complexity = 4
        self.crypto_suitability = 9
        self._supertrend_cache = {}

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'atr_period', 'type': int, 'min': 7, 'max': 14, 'default': 10},
            {'name': 'multiplier', 'type': float, 'min': 2.0, 'max': 4.0, 'default': 3.0},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 4.0, 'default': 3.0},
        ]

    def _calculate_supertrend(self, candles=None):
        """Calculate SuperTrend indicator"""
        if candles is None:
            candles = self.candles

        period = self.hp['atr_period']
        multiplier = self.hp['multiplier']

        high = candles[:, 3]
        low = candles[:, 4]
        close = candles[:, 2]

        # Calculate ATR
        tr = np.zeros(len(candles))
        for i in range(1, len(candles)):
            tr[i] = max(
                high[i] - low[i],
                abs(high[i] - close[i-1]),
                abs(low[i] - close[i-1])
            )

        atr = np.zeros(len(candles))
        atr[period] = np.mean(tr[1:period+1])
        for i in range(period + 1, len(candles)):
            atr[i] = (atr[i-1] * (period - 1) + tr[i]) / period

        # Calculate basic bands
        hl2 = (high + low) / 2
        upper_basic = hl2 + (multiplier * atr)
        lower_basic = hl2 - (multiplier * atr)

        # Calculate final bands and trend
        upper_band = np.zeros(len(candles))
        lower_band = np.zeros(len(candles))
        supertrend = np.zeros(len(candles))
        trend = np.zeros(len(candles))  # 1 for bullish, -1 for bearish

        upper_band[0] = upper_basic[0]
        lower_band[0] = lower_basic[0]
        trend[0] = 1

        for i in range(1, len(candles)):
            # Upper band
            if upper_basic[i] < upper_band[i-1] or close[i-1] > upper_band[i-1]:
                upper_band[i] = upper_basic[i]
            else:
                upper_band[i] = upper_band[i-1]

            # Lower band
            if lower_basic[i] > lower_band[i-1] or close[i-1] < lower_band[i-1]:
                lower_band[i] = lower_basic[i]
            else:
                lower_band[i] = lower_band[i-1]

            # Trend direction
            if trend[i-1] == 1:
                if close[i] < lower_band[i]:
                    trend[i] = -1
                else:
                    trend[i] = 1
            else:
                if close[i] > upper_band[i]:
                    trend[i] = 1
                else:
                    trend[i] = -1

            # SuperTrend value
            if trend[i] == 1:
                supertrend[i] = lower_band[i]
            else:
                supertrend[i] = upper_band[i]

        return supertrend[-1], trend[-1], supertrend[-2] if len(candles) > 1 else supertrend[-1], trend[-2] if len(candles) > 1 else trend[-1]

    @property
    def supertrend(self):
        """Get current SuperTrend values"""
        return self._calculate_supertrend()

    @property
    def trend_bullish(self) -> bool:
        _, trend, _, _ = self.supertrend
        return trend == 1

    @property
    def trend_bearish(self) -> bool:
        _, trend, _, _ = self.supertrend
        return trend == -1

    @property
    def trend_changed_to_bullish(self) -> bool:
        _, trend, _, prev_trend = self.supertrend
        return trend == 1 and prev_trend == -1

    @property
    def trend_changed_to_bearish(self) -> bool:
        _, trend, _, prev_trend = self.supertrend
        return trend == -1 and prev_trend == 1

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=self.hp['atr_period'])

    def should_long(self) -> bool:
        return self.trend_changed_to_bullish

    def should_short(self) -> bool:
        return self.trend_changed_to_bearish

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
        # Exit on trend reversal
        if self.is_long and self.trend_bearish:
            self.liquidate()
        elif self.is_short and self.trend_bullish:
            self.liquidate()

"""
SAR_001: Parabolic SAR Basic Strategy
-------------------------------------
Classic Parabolic SAR trend following.
SAR below price = bullish, above = bearish.

Entry Long: SAR flips below price
Entry Short: SAR flips above price

Optimal Timeframes: 1h, 4h
Complexity: 2/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class SARBasic(Strategy):
    """Parabolic SAR Basic Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "SAR_001"
        self.strategy_name = "Parabolic SAR Basic"
        self.complexity = 2
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'acceleration', 'type': float, 'min': 0.01, 'max': 0.03, 'default': 0.02},
            {'name': 'maximum', 'type': float, 'min': 0.15, 'max': 0.25, 'default': 0.2},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
        ]

    def _calculate_sar(self, candles=None):
        """Calculate Parabolic SAR"""
        if candles is None:
            candles = self.candles

        high = candles[:, 3]
        low = candles[:, 4]
        af = self.hp['acceleration']
        max_af = self.hp['maximum']

        sar = np.zeros(len(candles))
        trend = np.zeros(len(candles))  # 1 = up, -1 = down
        ep = np.zeros(len(candles))  # Extreme point
        af_vals = np.zeros(len(candles))

        # Initialize
        sar[0] = low[0]
        trend[0] = 1
        ep[0] = high[0]
        af_vals[0] = af

        for i in range(1, len(candles)):
            if trend[i-1] == 1:  # Uptrend
                sar[i] = sar[i-1] + af_vals[i-1] * (ep[i-1] - sar[i-1])
                sar[i] = min(sar[i], low[i-1], low[max(0, i-2)] if i > 1 else low[i-1])

                if low[i] < sar[i]:  # Trend reversal
                    trend[i] = -1
                    sar[i] = ep[i-1]
                    ep[i] = low[i]
                    af_vals[i] = af
                else:
                    trend[i] = 1
                    if high[i] > ep[i-1]:
                        ep[i] = high[i]
                        af_vals[i] = min(af_vals[i-1] + af, max_af)
                    else:
                        ep[i] = ep[i-1]
                        af_vals[i] = af_vals[i-1]
            else:  # Downtrend
                sar[i] = sar[i-1] + af_vals[i-1] * (ep[i-1] - sar[i-1])
                sar[i] = max(sar[i], high[i-1], high[max(0, i-2)] if i > 1 else high[i-1])

                if high[i] > sar[i]:  # Trend reversal
                    trend[i] = 1
                    sar[i] = ep[i-1]
                    ep[i] = high[i]
                    af_vals[i] = af
                else:
                    trend[i] = -1
                    if low[i] < ep[i-1]:
                        ep[i] = low[i]
                        af_vals[i] = min(af_vals[i-1] + af, max_af)
                    else:
                        ep[i] = ep[i-1]
                        af_vals[i] = af_vals[i-1]

        return sar, trend

    @property
    def sar(self) -> float:
        sar, _ = self._calculate_sar()
        return sar[-1]

    @property
    def sar_prev(self) -> float:
        sar, _ = self._calculate_sar()
        return sar[-2] if len(sar) > 1 else sar[-1]

    @property
    def trend(self) -> int:
        _, trend = self._calculate_sar()
        return int(trend[-1])

    @property
    def trend_prev(self) -> int:
        _, trend = self._calculate_sar()
        return int(trend[-2]) if len(trend) > 1 else int(trend[-1])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def sar_flipped_bullish(self) -> bool:
        return self.trend_prev == -1 and self.trend == 1

    @property
    def sar_flipped_bearish(self) -> bool:
        return self.trend_prev == 1 and self.trend == -1

    def should_long(self) -> bool:
        return self.sar_flipped_bullish

    def should_short(self) -> bool:
        return self.sar_flipped_bearish

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = self.sar - (self.atr * 0.5)
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        entry = self.price
        stop = self.sar + (self.atr * 0.5)
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.sell = qty, entry
        self.stop_loss = qty, stop

    def update_position(self):
        # Update trailing stop to SAR
        if self.is_long:
            if self.sar > self.position.entry_price * 0.99:
                self.stop_loss = self.position.qty, self.sar
            if self.trend == -1:
                self.liquidate()
        elif self.is_short:
            if self.sar < self.position.entry_price * 1.01:
                self.stop_loss = self.position.qty, self.sar
            if self.trend == 1:
                self.liquidate()

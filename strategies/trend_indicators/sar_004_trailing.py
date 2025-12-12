"""
SAR_004: SAR Trailing Stop Strategy
-----------------------------------
Use SAR purely as a trailing stop mechanism.
Enter on other signals, use SAR for exits.

Entry: Based on momentum/MA signal
Exit: SAR trailing stop

Optimal Timeframes: 1h, 4h
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class SARTrailing(Strategy):
    """SAR Trailing Stop Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "SAR_004"
        self.strategy_name = "SAR Trailing"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'acceleration', 'type': float, 'min': 0.01, 'max': 0.03, 'default': 0.02},
            {'name': 'maximum', 'type': float, 'min': 0.15, 'max': 0.25, 'default': 0.2},
            {'name': 'fast_ma', 'type': int, 'min': 8, 'max': 15, 'default': 10},
            {'name': 'slow_ma', 'type': int, 'min': 20, 'max': 30, 'default': 20},
        ]

    def _calculate_sar(self):
        high = self.candles[:, 3]
        low = self.candles[:, 4]
        af = self.hp['acceleration']
        max_af = self.hp['maximum']

        sar = np.zeros(len(self.candles))
        trend = np.zeros(len(self.candles))
        ep = np.zeros(len(self.candles))
        af_vals = np.zeros(len(self.candles))

        sar[0] = low[0]
        trend[0] = 1
        ep[0] = high[0]
        af_vals[0] = af

        for i in range(1, len(self.candles)):
            if trend[i-1] == 1:
                sar[i] = sar[i-1] + af_vals[i-1] * (ep[i-1] - sar[i-1])
                sar[i] = min(sar[i], low[i-1], low[max(0, i-2)] if i > 1 else low[i-1])

                if low[i] < sar[i]:
                    trend[i] = -1
                    sar[i] = ep[i-1]
                    ep[i] = low[i]
                    af_vals[i] = af
                else:
                    trend[i] = 1
                    ep[i] = max(ep[i-1], high[i])
                    af_vals[i] = min(af_vals[i-1] + af, max_af) if high[i] > ep[i-1] else af_vals[i-1]
            else:
                sar[i] = sar[i-1] + af_vals[i-1] * (ep[i-1] - sar[i-1])
                sar[i] = max(sar[i], high[i-1], high[max(0, i-2)] if i > 1 else high[i-1])

                if high[i] > sar[i]:
                    trend[i] = 1
                    sar[i] = ep[i-1]
                    ep[i] = high[i]
                    af_vals[i] = af
                else:
                    trend[i] = -1
                    ep[i] = min(ep[i-1], low[i])
                    af_vals[i] = min(af_vals[i-1] + af, max_af) if low[i] < ep[i-1] else af_vals[i-1]

        return sar, trend

    @property
    def sar(self) -> float:
        sar, _ = self._calculate_sar()
        return sar[-1]

    @property
    def trend(self) -> int:
        _, trend = self._calculate_sar()
        return int(trend[-1])

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
    def ma_bullish_cross(self) -> bool:
        return self.fast_ema_prev <= self.slow_ema_prev and self.fast_ema > self.slow_ema

    @property
    def ma_bearish_cross(self) -> bool:
        return self.fast_ema_prev >= self.slow_ema_prev and self.fast_ema < self.slow_ema

    def should_long(self) -> bool:
        return self.ma_bullish_cross and self.trend == 1

    def should_short(self) -> bool:
        return self.ma_bearish_cross and self.trend == -1

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = self.sar
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        entry = self.price
        stop = self.sar
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.sell = qty, entry
        self.stop_loss = qty, stop

    def update_position(self):
        # Update trailing stop using SAR
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

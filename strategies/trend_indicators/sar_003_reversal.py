"""
SAR_003: SAR Reversal Strategy
------------------------------
Trade SAR reversals with confirmation.
Wait for price to confirm SAR flip.

Entry Long: SAR flip + bullish candle
Entry Short: SAR flip + bearish candle

Optimal Timeframes: 1h, 4h
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class SARReversal(Strategy):
    """SAR Reversal Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "SAR_003"
        self.strategy_name = "SAR Reversal"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'acceleration', 'type': float, 'min': 0.01, 'max': 0.03, 'default': 0.02},
            {'name': 'maximum', 'type': float, 'min': 0.15, 'max': 0.25, 'default': 0.2},
            {'name': 'confirm_bars', 'type': int, 'min': 1, 'max': 3, 'default': 1},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 5.0, 'default': 3.5},
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
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _recent_flip_bullish(self) -> bool:
        _, trend = self._calculate_sar()
        confirm = self.hp['confirm_bars']
        if len(trend) < confirm + 2:
            return False
        # Check if flip happened within confirm bars
        for i in range(1, confirm + 2):
            if trend[-i] == 1 and trend[-i-1] == -1:
                return True
        return False

    def _recent_flip_bearish(self) -> bool:
        _, trend = self._calculate_sar()
        confirm = self.hp['confirm_bars']
        if len(trend) < confirm + 2:
            return False
        for i in range(1, confirm + 2):
            if trend[-i] == -1 and trend[-i-1] == 1:
                return True
        return False

    @property
    def bullish_candle(self) -> bool:
        return self.close > self.open

    @property
    def bearish_candle(self) -> bool:
        return self.close < self.open

    def should_long(self) -> bool:
        return self._recent_flip_bullish() and self.bullish_candle and self.trend == 1

    def should_short(self) -> bool:
        return self._recent_flip_bearish() and self.bearish_candle and self.trend == -1

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
        if self.is_long and self.trend == -1:
            self.liquidate()
        elif self.is_short and self.trend == 1:
            self.liquidate()

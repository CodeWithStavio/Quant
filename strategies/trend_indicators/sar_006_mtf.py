"""
SAR_006: Multi-Timeframe SAR Strategy
-------------------------------------
Use SAR from higher timeframe for trend direction.
Trade SAR signals only in direction of higher TF trend.

Entry: Current TF SAR aligned with higher TF SAR

Optimal Timeframes: 15m with 1h filter, 1h with 4h filter
Complexity: 5/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class SARMultiTimeframe(Strategy):
    """Multi-Timeframe SAR Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "SAR_006"
        self.strategy_name = "Multi-Timeframe SAR"
        self.complexity = 5
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'acceleration', 'type': float, 'min': 0.01, 'max': 0.03, 'default': 0.02},
            {'name': 'maximum', 'type': float, 'min': 0.15, 'max': 0.25, 'default': 0.2},
            {'name': 'htf_lookback', 'type': int, 'min': 4, 'max': 8, 'default': 4},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 5.0, 'default': 3.5},
        ]

    def _calculate_sar(self, candles=None):
        if candles is None:
            candles = self.candles

        high = candles[:, 3]
        low = candles[:, 4]
        af = self.hp['acceleration']
        max_af = self.hp['maximum']

        sar = np.zeros(len(candles))
        trend = np.zeros(len(candles))
        ep = np.zeros(len(candles))
        af_vals = np.zeros(len(candles))

        sar[0] = low[0]
        trend[0] = 1
        ep[0] = high[0]
        af_vals[0] = af

        for i in range(1, len(candles)):
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

    def _create_htf_candles(self):
        """Create simulated higher timeframe candles"""
        htf_lookback = self.hp['htf_lookback']
        if len(self.candles) < htf_lookback * 10:
            return self.candles

        # Aggregate candles to simulate higher TF
        num_htf_candles = len(self.candles) // htf_lookback
        htf_candles = np.zeros((num_htf_candles, 6))

        for i in range(num_htf_candles):
            start_idx = i * htf_lookback
            end_idx = start_idx + htf_lookback
            period_candles = self.candles[start_idx:end_idx]

            htf_candles[i, 0] = period_candles[0, 0]  # timestamp
            htf_candles[i, 1] = period_candles[0, 1]  # open
            htf_candles[i, 2] = period_candles[-1, 2]  # close
            htf_candles[i, 3] = np.max(period_candles[:, 3])  # high
            htf_candles[i, 4] = np.min(period_candles[:, 4])  # low
            htf_candles[i, 5] = np.sum(period_candles[:, 5])  # volume

        return htf_candles

    @property
    def sar(self) -> float:
        sar, _ = self._calculate_sar()
        return sar[-1]

    @property
    def trend(self) -> int:
        _, trend = self._calculate_sar()
        return int(trend[-1])

    @property
    def trend_prev(self) -> int:
        _, trend = self._calculate_sar()
        return int(trend[-2]) if len(trend) > 1 else int(trend[-1])

    @property
    def htf_trend(self) -> int:
        """Higher timeframe SAR trend"""
        htf_candles = self._create_htf_candles()
        if len(htf_candles) < 10:
            return self.trend
        _, trend = self._calculate_sar(htf_candles)
        return int(trend[-1])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def sar_bullish_flip(self) -> bool:
        return self.trend_prev == -1 and self.trend == 1

    @property
    def sar_bearish_flip(self) -> bool:
        return self.trend_prev == 1 and self.trend == -1

    @property
    def htf_bullish(self) -> bool:
        return self.htf_trend == 1

    @property
    def htf_bearish(self) -> bool:
        return self.htf_trend == -1

    def should_long(self) -> bool:
        return self.sar_bullish_flip and self.htf_bullish

    def should_short(self) -> bool:
        return self.sar_bearish_flip and self.htf_bearish

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
        # Exit on LTF or HTF trend change
        if self.is_long and (self.trend == -1 or self.htf_bearish):
            self.liquidate()
        elif self.is_short and (self.trend == 1 or self.htf_bullish):
            self.liquidate()

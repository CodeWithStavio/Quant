"""
VOL_004: VWAP Bands Strategy
----------------------------
VWAP with standard deviation bands for mean reversion.
Similar to Bollinger Bands but using VWAP instead of SMA.

Entry Long: Price at lower VWAP band
Entry Short: Price at upper VWAP band

Optimal Timeframes: 5m, 15m, 1h
Complexity: 4/10
Crypto Suitability: 9/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class VWAPBands(Strategy):
    """VWAP Bands Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "VOL_004"
        self.strategy_name = "VWAP Bands"
        self.complexity = 4
        self.crypto_suitability = 9

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'vwap_period', 'type': int, 'min': 20, 'max': 100, 'default': 50},
            {'name': 'std_mult', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
        ]

    def _calculate_vwap_bands(self, candles=None):
        """Calculate VWAP with standard deviation bands"""
        if candles is None:
            candles = self.candles

        period = min(self.hp['vwap_period'], len(candles))
        candles = candles[-period:]

        typical_price = (candles[:, 3] + candles[:, 4] + candles[:, 2]) / 3
        volume = candles[:, 5]

        cumulative_tp_vol = np.cumsum(typical_price * volume)
        cumulative_vol = np.cumsum(volume)
        cumulative_vol = np.where(cumulative_vol == 0, 1, cumulative_vol)

        vwap = cumulative_tp_vol / cumulative_vol

        # Calculate standard deviation from VWAP
        squared_diff = (typical_price - vwap[-1]) ** 2
        variance = np.sum(squared_diff * volume) / np.sum(volume)
        std_dev = np.sqrt(variance)

        upper = vwap[-1] + (std_dev * self.hp['std_mult'])
        lower = vwap[-1] - (std_dev * self.hp['std_mult'])

        return vwap[-1], upper, lower

    @property
    def vwap(self) -> float:
        vwap, _, _ = self._calculate_vwap_bands()
        return vwap

    @property
    def upper_band(self) -> float:
        _, upper, _ = self._calculate_vwap_bands()
        return upper

    @property
    def lower_band(self) -> float:
        _, _, lower = self._calculate_vwap_bands()
        return lower

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def at_lower_band(self) -> bool:
        return self.close <= self.lower_band

    @property
    def at_upper_band(self) -> bool:
        return self.close >= self.upper_band

    @property
    def crossed_above_lower(self) -> bool:
        prev_close = self.candles[-2, 2]
        vwap_prev, _, lower_prev = self._calculate_vwap_bands(self.candles[:-1])
        return prev_close <= lower_prev and self.close > self.lower_band

    @property
    def crossed_below_upper(self) -> bool:
        prev_close = self.candles[-2, 2]
        vwap_prev, upper_prev, _ = self._calculate_vwap_bands(self.candles[:-1])
        return prev_close >= upper_prev and self.close < self.upper_band

    def should_long(self) -> bool:
        return self.crossed_above_lower

    def should_short(self) -> bool:
        return self.crossed_below_upper

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry - (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, self.vwap  # Target VWAP

    def go_short(self):
        entry = self.price
        stop = entry + (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, self.vwap  # Target VWAP

    def update_position(self):
        # Exit at VWAP or opposite band
        if self.is_long and self.close >= self.vwap:
            self.liquidate()
        elif self.is_short and self.close <= self.vwap:
            self.liquidate()

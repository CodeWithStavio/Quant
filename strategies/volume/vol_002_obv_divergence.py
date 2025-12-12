"""
VOL_002: OBV Divergence Strategy
--------------------------------
Detect divergences between price and OBV.
Bullish divergence: Price makes lower low, OBV makes higher low
Bearish divergence: Price makes higher high, OBV makes lower high

Entry Long: Bullish divergence detected
Entry Short: Bearish divergence detected

Optimal Timeframes: 1h, 4h
Complexity: 5/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class OBVDivergence(Strategy):
    """OBV Divergence Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "VOL_002"
        self.strategy_name = "OBV Divergence"
        self.complexity = 5
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 10, 'max': 30, 'default': 20},
            {'name': 'pivot_lookback', 'type': int, 'min': 3, 'max': 7, 'default': 5},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 5.0, 'default': 3.5},
        ]

    def _calculate_obv(self):
        """Calculate On-Balance Volume"""
        close = self.candles[:, 2]
        volume = self.candles[:, 5]

        obv = np.zeros(len(self.candles))
        obv[0] = volume[0]

        for i in range(1, len(self.candles)):
            if close[i] > close[i-1]:
                obv[i] = obv[i-1] + volume[i]
            elif close[i] < close[i-1]:
                obv[i] = obv[i-1] - volume[i]
            else:
                obv[i] = obv[i-1]

        return obv

    def _find_pivots(self, data, lookback):
        """Find pivot highs and lows"""
        pivot_highs = []
        pivot_lows = []

        for i in range(lookback, len(data) - lookback):
            # Check for pivot high
            is_high = True
            is_low = True

            for j in range(1, lookback + 1):
                if data[i] <= data[i - j] or data[i] <= data[i + j]:
                    is_high = False
                if data[i] >= data[i - j] or data[i] >= data[i + j]:
                    is_low = False

            if is_high:
                pivot_highs.append((i, data[i]))
            if is_low:
                pivot_lows.append((i, data[i]))

        return pivot_highs, pivot_lows

    def _detect_divergence(self):
        """Detect bullish and bearish divergences"""
        lookback = self.hp['lookback']
        pivot_lb = self.hp['pivot_lookback']

        close = self.candles[:, 2]
        obv = self._calculate_obv()

        # Get recent pivots
        price_highs, price_lows = self._find_pivots(close[-lookback - pivot_lb * 2:], pivot_lb)
        obv_highs, obv_lows = self._find_pivots(obv[-lookback - pivot_lb * 2:], pivot_lb)

        bullish_div = False
        bearish_div = False

        # Bullish divergence: price lower low, OBV higher low
        if len(price_lows) >= 2 and len(obv_lows) >= 2:
            if price_lows[-1][1] < price_lows[-2][1] and obv_lows[-1][1] > obv_lows[-2][1]:
                bullish_div = True

        # Bearish divergence: price higher high, OBV lower high
        if len(price_highs) >= 2 and len(obv_highs) >= 2:
            if price_highs[-1][1] > price_highs[-2][1] and obv_highs[-1][1] < obv_highs[-2][1]:
                bearish_div = True

        return bullish_div, bearish_div

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        bullish, _ = self._detect_divergence()
        return bullish

    def should_short(self) -> bool:
        _, bearish = self._detect_divergence()
        return bearish

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
        # Exit on opposite divergence
        bullish, bearish = self._detect_divergence()
        if self.is_long and bearish:
            self.liquidate()
        elif self.is_short and bullish:
            self.liquidate()

"""
MOM_002: RSI Divergence Strategy
--------------------------------
Trade divergences between price and RSI.

Entry Long: Bullish divergence (price lower low, RSI higher low)
Entry Short: Bearish divergence (price higher high, RSI lower high)

Optimal Timeframes: 1h, 4h, 1d
Complexity: 6/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class RSIDivergence(Strategy):
    """RSI Divergence Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MOM_002"
        self.strategy_name = "RSI Divergence"
        self.complexity = 6
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'rsi_period', 'type': int, 'min': 7, 'max': 21, 'default': 14},
            {'name': 'divergence_lookback', 'type': int, 'min': 10, 'max': 30, 'default': 20},
            {'name': 'min_price_diff_pct', 'type': float, 'min': 0.005, 'max': 0.03, 'default': 0.01},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 5.0, 'default': 3.0},
        ]

    @property
    def rsi_sequential(self) -> np.ndarray:
        return ta.rsi(self.candles, period=self.hp['rsi_period'], sequential=True)

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _find_swing_lows(self, data: np.ndarray, lookback: int) -> List[tuple]:
        """Find swing lows in data"""
        swings = []
        for i in range(2, lookback):
            idx = -i
            if idx - 1 < -len(data) or idx + 1 >= 0:
                continue
            if data[idx] < data[idx-1] and data[idx] < data[idx+1]:
                swings.append((idx, data[idx]))
        return swings[-2:] if len(swings) >= 2 else []

    def _find_swing_highs(self, data: np.ndarray, lookback: int) -> List[tuple]:
        """Find swing highs in data"""
        swings = []
        for i in range(2, lookback):
            idx = -i
            if idx - 1 < -len(data) or idx + 1 >= 0:
                continue
            if data[idx] > data[idx-1] and data[idx] > data[idx+1]:
                swings.append((idx, data[idx]))
        return swings[-2:] if len(swings) >= 2 else []

    def _bullish_divergence(self) -> bool:
        """Detect bullish divergence (price lower low, RSI higher low)"""
        lookback = self.hp['divergence_lookback']
        close = self.candles[:, 2]
        rsi = self.rsi_sequential

        price_swings = self._find_swing_lows(close, lookback)
        rsi_swings = self._find_swing_lows(rsi, lookback)

        if len(price_swings) < 2 or len(rsi_swings) < 2:
            return False

        # Most recent swing should be lower price but higher RSI
        price_lower = price_swings[-1][1] < price_swings[-2][1]
        rsi_higher = rsi_swings[-1][1] > rsi_swings[-2][1]

        # Minimum price difference
        min_diff = self.hp['min_price_diff_pct']
        price_diff = abs(price_swings[-1][1] - price_swings[-2][1]) / price_swings[-2][1]

        return price_lower and rsi_higher and price_diff > min_diff

    def _bearish_divergence(self) -> bool:
        """Detect bearish divergence (price higher high, RSI lower high)"""
        lookback = self.hp['divergence_lookback']
        close = self.candles[:, 2]
        rsi = self.rsi_sequential

        price_swings = self._find_swing_highs(close, lookback)
        rsi_swings = self._find_swing_highs(rsi, lookback)

        if len(price_swings) < 2 or len(rsi_swings) < 2:
            return False

        # Most recent swing should be higher price but lower RSI
        price_higher = price_swings[-1][1] > price_swings[-2][1]
        rsi_lower = rsi_swings[-1][1] < rsi_swings[-2][1]

        # Minimum price difference
        min_diff = self.hp['min_price_diff_pct']
        price_diff = abs(price_swings[-1][1] - price_swings[-2][1]) / price_swings[-2][1]

        return price_higher and rsi_lower and price_diff > min_diff

    def should_long(self) -> bool:
        return self._bullish_divergence() and self.rsi_sequential[-1] < 40

    def should_short(self) -> bool:
        return self._bearish_divergence() and self.rsi_sequential[-1] > 60

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
        pass

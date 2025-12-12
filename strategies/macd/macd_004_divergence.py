"""
MACD_004: MACD Divergence Strategy
----------------------------------
Trade divergences between price and MACD.

Entry Long: Bullish divergence (price lower low, MACD higher low)
Entry Short: Bearish divergence (price higher high, MACD lower high)

Optimal Timeframes: 1h, 4h
Complexity: 6/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class MACDDivergence(Strategy):
    """MACD Divergence Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MACD_004"
        self.strategy_name = "MACD Divergence"
        self.complexity = 6
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'fast_period', 'type': int, 'min': 8, 'max': 15, 'default': 12},
            {'name': 'slow_period', 'type': int, 'min': 20, 'max': 30, 'default': 26},
            {'name': 'signal_period', 'type': int, 'min': 7, 'max': 12, 'default': 9},
            {'name': 'divergence_lookback', 'type': int, 'min': 10, 'max': 30, 'default': 20},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 5.0, 'default': 3.5},
        ]

    def _get_macd_sequential(self) -> np.ndarray:
        """Get MACD line as sequential array"""
        macd, signal, hist = ta.macd(
            self.candles,
            fast_period=self.hp['fast_period'],
            slow_period=self.hp['slow_period'],
            signal_period=self.hp['signal_period'],
            sequential=True
        )
        return macd

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _find_lows(self, data: np.ndarray, lookback: int) -> List[tuple]:
        """Find swing lows"""
        swings = []
        for i in range(2, lookback):
            idx = -i
            if idx - 1 < -len(data) or idx + 1 >= 0:
                continue
            if data[idx] < data[idx-1] and data[idx] < data[idx+1]:
                swings.append((idx, data[idx]))
        return swings[-2:] if len(swings) >= 2 else []

    def _find_highs(self, data: np.ndarray, lookback: int) -> List[tuple]:
        """Find swing highs"""
        swings = []
        for i in range(2, lookback):
            idx = -i
            if idx - 1 < -len(data) or idx + 1 >= 0:
                continue
            if data[idx] > data[idx-1] and data[idx] > data[idx+1]:
                swings.append((idx, data[idx]))
        return swings[-2:] if len(swings) >= 2 else []

    def _bullish_divergence(self) -> bool:
        """Detect bullish divergence"""
        lookback = self.hp['divergence_lookback']
        close = self.candles[:, 2]
        macd = self._get_macd_sequential()

        price_lows = self._find_lows(close, lookback)
        macd_lows = self._find_lows(macd, lookback)

        if len(price_lows) < 2 or len(macd_lows) < 2:
            return False

        price_lower = price_lows[-1][1] < price_lows[-2][1]
        macd_higher = macd_lows[-1][1] > macd_lows[-2][1]

        return price_lower and macd_higher

    def _bearish_divergence(self) -> bool:
        """Detect bearish divergence"""
        lookback = self.hp['divergence_lookback']
        close = self.candles[:, 2]
        macd = self._get_macd_sequential()

        price_highs = self._find_highs(close, lookback)
        macd_highs = self._find_highs(macd, lookback)

        if len(price_highs) < 2 or len(macd_highs) < 2:
            return False

        price_higher = price_highs[-1][1] > price_highs[-2][1]
        macd_lower = macd_highs[-1][1] < macd_highs[-2][1]

        return price_higher and macd_lower

    def should_long(self) -> bool:
        return self._bullish_divergence()

    def should_short(self) -> bool:
        return self._bearish_divergence()

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

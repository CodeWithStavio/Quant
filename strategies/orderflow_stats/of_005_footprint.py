"""
OF_005: Footprint Proxy Strategy
--------------------------------
Simulate footprint chart analysis using OHLCV data.

Entry Long: Stacked bids pattern (buying pressure)
Entry Short: Stacked offers pattern (selling pressure)

Optimal Timeframes: 5m, 15m
Complexity: 7/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class FootprintProxy(Strategy):
    """Footprint Proxy Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "OF_005"
        self.strategy_name = "Footprint Proxy"
        self.complexity = 7
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 5, 'max': 15, 'default': 8},
            {'name': 'imbalance_ratio', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
        ]

    def _analyze_candle_imbalance(self, idx: int) -> dict:
        """Analyze candle for buying/selling imbalance"""
        candle = self.candles[idx]
        high, low, close, open_price, volume = candle[3], candle[4], candle[2], candle[1], candle[5]

        if high == low:
            return {'buy_pressure': 0.5, 'sell_pressure': 0.5, 'imbalance': 1}

        range_size = high - low

        # Estimate pressure based on candle structure
        close_position = (close - low) / range_size
        body_size = abs(close - open_price) / range_size

        if close > open_price:  # Green candle
            buy_pressure = close_position * body_size + 0.3
            sell_pressure = (1 - close_position) * body_size + 0.3
        else:  # Red candle
            sell_pressure = (1 - close_position) * body_size + 0.3
            buy_pressure = close_position * body_size + 0.3

        return {
            'buy_pressure': min(buy_pressure, 1),
            'sell_pressure': min(sell_pressure, 1),
            'imbalance': buy_pressure / sell_pressure if sell_pressure > 0 else float('inf')
        }

    def _detect_stacked_bids(self) -> bool:
        """Detect stacked bids pattern (buying pressure)"""
        lookback = self.hp['lookback']
        threshold = self.hp['imbalance_ratio']

        buy_dominant = 0
        for i in range(1, lookback + 1):
            analysis = self._analyze_candle_imbalance(-i)
            if analysis['imbalance'] > threshold:
                buy_dominant += 1

        return buy_dominant >= lookback * 0.6

    def _detect_stacked_offers(self) -> bool:
        """Detect stacked offers pattern (selling pressure)"""
        lookback = self.hp['lookback']
        threshold = self.hp['imbalance_ratio']

        sell_dominant = 0
        for i in range(1, lookback + 1):
            analysis = self._analyze_candle_imbalance(-i)
            if analysis['imbalance'] < (1 / threshold):
                sell_dominant += 1

        return sell_dominant >= lookback * 0.6

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self._detect_stacked_bids()

    def should_short(self) -> bool:
        return self._detect_stacked_offers()

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry - (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        entry = self.price
        stop = entry + (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop

    def update_position(self):
        analysis = self._analyze_candle_imbalance(-1)
        if self.is_long and analysis['imbalance'] < 0.8:
            self.liquidate()
        elif self.is_short and analysis['imbalance'] > 1.2:
            self.liquidate()

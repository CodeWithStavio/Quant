"""
SENT_004: Fear & Greed Proxy Strategy
-------------------------------------
Construct fear/greed index from price action.

Entry Long: Extreme fear (contrarian buy)
Entry Short: Extreme greed (contrarian sell)

Optimal Timeframes: 4h, 1d
Complexity: 6/10
Crypto Suitability: 9/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class FearGreedProxy(Strategy):
    """Fear & Greed Proxy Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "SENT_004"
        self.strategy_name = "Fear Greed Proxy"
        self.complexity = 6
        self.crypto_suitability = 9

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 20, 'max': 40, 'default': 30},
            {'name': 'fear_threshold', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'greed_threshold', 'type': int, 'min': 70, 'max': 85, 'default': 80},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 2.0, 'max': 3.0, 'default': 2.5},
        ]

    def _calculate_fear_greed(self) -> float:
        """Calculate fear/greed index (0-100)"""
        lookback = self.hp['lookback']

        # Component 1: Price momentum (0-25)
        roc = ta.roc(self.candles, period=lookback)
        roc_score = min(max((roc + 20) / 40 * 25, 0), 25)

        # Component 2: Volatility (inverse - low vol = greed) (0-25)
        atr = ta.atr(self.candles, period=14)
        atr_history = []
        for i in range(lookback):
            if len(self.candles) > i + 15:
                atr_history.append(ta.atr(self.candles[:-(i+1)], period=14))
        if atr_history:
            vol_percentile = np.sum(np.array(atr_history) < atr) / len(atr_history)
            vol_score = (1 - vol_percentile) * 25  # Inverse: low vol = high score
        else:
            vol_score = 12.5

        # Component 3: RSI (0-25)
        rsi = ta.rsi(self.candles, period=14)
        rsi_score = rsi / 100 * 25

        # Component 4: Distance from MA (0-25)
        ma = ta.sma(self.candles, period=lookback)
        distance = (self.close - ma) / ma * 100
        dist_score = min(max((distance + 10) / 20 * 25, 0), 25)

        return roc_score + vol_score + rsi_score + dist_score

    @property
    def fear_greed_index(self) -> float:
        return self._calculate_fear_greed()

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # Extreme fear = contrarian buy
        return self.fear_greed_index < self.hp['fear_threshold']

    def should_short(self) -> bool:
        # Extreme greed = contrarian sell
        return self.fear_greed_index > self.hp['greed_threshold']

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
        # Exit when sentiment normalizes
        fg = self.fear_greed_index
        if self.is_long and fg > 50:
            self.liquidate()
        elif self.is_short and fg < 50:
            self.liquidate()

"""
SENT_005: Market Breadth Strategy
---------------------------------
Simulate market breadth using price internals.

Entry Long: Strong breadth (multi-indicator agreement)
Entry Short: Weak breadth (multi-indicator disagreement)

Optimal Timeframes: 4h, 1d
Complexity: 6/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class MarketBreadth(Strategy):
    """Market Breadth Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "SENT_005"
        self.strategy_name = "Market Breadth"
        self.complexity = 6
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'breadth_threshold', 'type': float, 'min': 0.6, 'max': 0.8, 'default': 0.7},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    def _calculate_breadth(self) -> float:
        """Calculate market breadth score (0-1)"""
        lookback = self.hp['lookback']
        bullish_signals = 0
        total_signals = 6

        # 1. Price above MA
        ma = ta.sma(self.candles, period=lookback)
        if self.close > ma:
            bullish_signals += 1

        # 2. RSI above 50
        rsi = ta.rsi(self.candles, period=14)
        if rsi > 50:
            bullish_signals += 1

        # 3. Positive momentum
        roc = ta.roc(self.candles, period=10)
        if roc > 0:
            bullish_signals += 1

        # 4. MACD bullish
        macd = ta.macd(self.candles, fast_period=12, slow_period=26, signal_period=9)
        if macd[0] > macd[1]:  # MACD line > signal
            bullish_signals += 1

        # 5. ADX trend confirmation
        adx = ta.adx(self.candles, period=14)
        di = ta.di(self.candles, period=14)
        if adx > 20 and di[0] > di[1]:  # +DI > -DI
            bullish_signals += 1

        # 6. Volume confirmation
        avg_vol = np.mean(self.candles[-lookback:-1, 5])
        if self.candles[-1, 5] > avg_vol and self.close > self.open:
            bullish_signals += 1

        return bullish_signals / total_signals

    @property
    def breadth(self) -> float:
        return self._calculate_breadth()

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self.breadth >= self.hp['breadth_threshold']

    def should_short(self) -> bool:
        return self.breadth <= (1 - self.hp['breadth_threshold'])

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
        if self.is_long and self.breadth < 0.5:
            self.liquidate()
        elif self.is_short and self.breadth > 0.5:
            self.liquidate()

"""
ML_010: Self-Optimizing Strategy
--------------------------------
Strategy that adjusts parameters based on recent performance.

Entry Long: Optimized conditions met for long
Entry Short: Optimized conditions met for short

Optimal Timeframes: 1h, 4h
Complexity: 8/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class SelfOptimizing(Strategy):
    """Self-Optimizing Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ML_010"
        self.strategy_name = "Self Optimizing"
        self.complexity = 8
        self.crypto_suitability = 7
        self.trades_history = []

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'base_ma', 'type': int, 'min': 15, 'max': 25, 'default': 20},
            {'name': 'lookback', 'type': int, 'min': 80, 'max': 150, 'default': 100},
            {'name': 'adaptation_rate', 'type': float, 'min': 0.1, 'max': 0.3, 'default': 0.2},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    def _calculate_optimal_ma(self) -> int:
        """Find MA period that worked best historically"""
        best_ma = self.hp['base_ma']
        best_score = -float('inf')

        for ma_period in range(10, 40, 5):
            score = self._backtest_ma(ma_period)
            if score > best_score:
                best_score = score
                best_ma = ma_period

        # Adapt gradually
        current = self.hp['base_ma']
        adapted = int(current + self.hp['adaptation_rate'] * (best_ma - current))
        return max(10, min(40, adapted))

    def _backtest_ma(self, period: int) -> float:
        """Simple backtest of MA crossover"""
        lookback = self.hp['lookback']
        if len(self.candles) < lookback + period:
            return 0

        wins = 0
        trades = 0

        for i in range(lookback - period - 5):
            idx = -(lookback - i)
            if abs(idx) >= len(self.candles):
                continue

            ma = ta.sma(self.candles[:idx], period=period)
            prev_ma = ta.sma(self.candles[:idx-1], period=period)
            close = self.candles[idx, 2]
            prev_close = self.candles[idx-1, 2]

            # Long signal
            if prev_close <= prev_ma and close > ma:
                future_idx = min(idx + 5, -1)
                future_close = self.candles[future_idx, 2]
                if future_close > close:
                    wins += 1
                trades += 1

        return wins / trades if trades > 0 else 0

    @property
    def optimal_ma(self) -> int:
        return self._calculate_optimal_ma()

    @property
    def ma(self) -> float:
        return ta.sma(self.candles, period=self.optimal_ma)

    @property
    def prev_ma(self) -> float:
        return ta.sma(self.candles[:-1], period=self.optimal_ma)

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        prev_close = self.candles[-2, 2]
        return prev_close <= self.prev_ma and self.close > self.ma

    def should_short(self) -> bool:
        prev_close = self.candles[-2, 2]
        return prev_close >= self.prev_ma and self.close < self.ma

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
        if self.is_long and self.close < self.ma:
            self.liquidate()
        elif self.is_short and self.close > self.ma:
            self.liquidate()

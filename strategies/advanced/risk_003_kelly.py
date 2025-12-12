"""
RISK_003: Kelly Criterion Strategy
----------------------------------
Position sizing using Kelly criterion approximation.

Entry Long: Signal with Kelly-sized position
Entry Short: Signal with Kelly-sized position

Optimal Timeframes: 4h, 1d
Complexity: 7/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class KellyCriterion(Strategy):
    """Kelly Criterion Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "RISK_003"
        self.strategy_name = "Kelly Criterion"
        self.complexity = 7
        self.crypto_suitability = 7
        self.trade_results = []

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'max_kelly', 'type': float, 'min': 0.1, 'max': 0.3, 'default': 0.2},
            {'name': 'lookback_trades', 'type': int, 'min': 20, 'max': 50, 'default': 30},
            {'name': 'min_trades', 'type': int, 'min': 10, 'max': 20, 'default': 10},
        ]

    def _estimate_kelly(self) -> float:
        """Estimate Kelly fraction from historical simulated results"""
        lookback = 50
        if len(self.candles) < lookback:
            return self.hp['max_kelly'] * 0.5

        # Simulate win/loss using MA crossover signals
        wins = 0
        losses = 0
        total_win = 0
        total_loss = 0

        for i in range(10, lookback - 5):
            idx = -(lookback - i)
            ma_fast = ta.sma(self.candles[:idx], period=10)
            ma_slow = ta.sma(self.candles[:idx], period=20)
            prev_fast = ta.sma(self.candles[:idx-1], period=10)
            prev_slow = ta.sma(self.candles[:idx-1], period=20)

            # Long signal
            if prev_fast <= prev_slow and ma_fast > ma_slow:
                entry = self.candles[idx, 2]
                exit_price = self.candles[idx+5, 2] if abs(idx+5) < len(self.candles) else self.candles[-1, 2]
                pnl = (exit_price - entry) / entry

                if pnl > 0:
                    wins += 1
                    total_win += pnl
                else:
                    losses += 1
                    total_loss += abs(pnl)

        if wins + losses < self.hp['min_trades']:
            return self.hp['max_kelly'] * 0.5

        win_rate = wins / (wins + losses)
        avg_win = total_win / wins if wins > 0 else 0.01
        avg_loss = total_loss / losses if losses > 0 else 0.01

        # Kelly formula: f = p - (1-p)/b where b = avg_win/avg_loss
        if avg_loss == 0:
            return self.hp['max_kelly']

        b = avg_win / avg_loss
        kelly = win_rate - (1 - win_rate) / b if b > 0 else 0

        # Cap and half-kelly
        return min(max(kelly * 0.5, 0.01), self.hp['max_kelly'])

    @property
    def kelly_fraction(self) -> float:
        return self._estimate_kelly()

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def trend(self) -> int:
        fast = ta.sma(self.candles, period=10)
        slow = ta.sma(self.candles, period=20)
        if fast > slow:
            return 1
        elif fast < slow:
            return -1
        return 0

    def should_long(self) -> bool:
        prev_fast = ta.sma(self.candles[:-1], period=10)
        prev_slow = ta.sma(self.candles[:-1], period=20)
        fast = ta.sma(self.candles, period=10)
        slow = ta.sma(self.candles, period=20)
        return prev_fast <= prev_slow and fast > slow

    def should_short(self) -> bool:
        prev_fast = ta.sma(self.candles[:-1], period=10)
        prev_slow = ta.sma(self.candles[:-1], period=20)
        fast = ta.sma(self.candles, period=10)
        slow = ta.sma(self.candles, period=20)
        return prev_fast >= prev_slow and fast < slow

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry - (self.atr * 2)
        qty = utils.size_to_qty(self.balance * self.kelly_fraction, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        entry = self.price
        stop = entry + (self.atr * 2)
        qty = utils.size_to_qty(self.balance * self.kelly_fraction, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop

    def update_position(self):
        if self.is_long and self.trend == -1:
            self.liquidate()
        elif self.is_short and self.trend == 1:
            self.liquidate()

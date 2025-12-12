"""
ML_005: Probability Based Entry Strategy
----------------------------------------
Enter trades based on calculated probability of success.

Entry Long: High probability bullish setup
Entry Short: High probability bearish setup

Optimal Timeframes: 1h, 4h
Complexity: 7/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class ProbabilityEntry(Strategy):
    """Probability Based Entry Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ML_005"
        self.strategy_name = "Probability Entry"
        self.complexity = 7
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 80, 'max': 150, 'default': 100},
            {'name': 'probability_threshold', 'type': float, 'min': 0.55, 'max': 0.70, 'default': 0.60},
            {'name': 'rsi_period', 'type': int, 'min': 10, 'max': 18, 'default': 14},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    @property
    def rsi(self) -> float:
        return ta.rsi(self.candles, period=self.hp['rsi_period'])

    def _calculate_win_probability(self, direction: str) -> float:
        """Calculate historical win probability for current setup"""
        lookback = self.hp['lookback']
        rsi_period = self.hp['rsi_period']

        wins = 0
        total = 0

        for i in range(lookback - rsi_period - 5):
            idx = -(i + 1)
            hist_rsi = ta.rsi(self.candles[:idx], period=rsi_period)

            # Similar RSI condition
            if direction == 'long':
                if hist_rsi < 40:  # Oversold-ish
                    # Check if price went up in next 5 bars
                    entry_price = self.candles[idx, 2]
                    future_high = np.max(self.candles[idx:idx+5, 3]) if idx+5 <= -1 else np.max(self.candles[idx:, 3])
                    if future_high > entry_price * 1.01:  # 1% gain
                        wins += 1
                    total += 1
            else:  # short
                if hist_rsi > 60:  # Overbought-ish
                    entry_price = self.candles[idx, 2]
                    future_low = np.min(self.candles[idx:idx+5, 4]) if idx+5 <= -1 else np.min(self.candles[idx:, 4])
                    if future_low < entry_price * 0.99:  # 1% drop
                        wins += 1
                    total += 1

        if total == 0:
            return 0.5
        return wins / total

    @property
    def long_probability(self) -> float:
        if self.rsi > 40:  # Not in oversold zone
            return 0
        return self._calculate_win_probability('long')

    @property
    def short_probability(self) -> float:
        if self.rsi < 60:  # Not in overbought zone
            return 0
        return self._calculate_win_probability('short')

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self.long_probability >= self.hp['probability_threshold']

    def should_short(self) -> bool:
        return self.short_probability >= self.hp['probability_threshold']

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
        pass

"""
MOM_020: Connors RSI Strategy
-----------------------------
Composite RSI by Larry Connors combining 3 components:
1. RSI of price
2. RSI of streak length (consecutive up/down days)
3. Percent rank of rate of change

Entry Long: ConnorsRSI < 10 (deeply oversold)
Entry Short: ConnorsRSI > 90 (deeply overbought)

Optimal Timeframes: 15m, 1h, 4h
Complexity: 6/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class ConnorsRSI(Strategy):
    """Connors RSI Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MOM_020"
        self.strategy_name = "Connors RSI"
        self.complexity = 6
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'rsi_period', 'type': int, 'min': 2, 'max': 5, 'default': 3},
            {'name': 'streak_rsi_period', 'type': int, 'min': 2, 'max': 3, 'default': 2},
            {'name': 'pct_rank_period', 'type': int, 'min': 50, 'max': 150, 'default': 100},
            {'name': 'overbought', 'type': int, 'min': 85, 'max': 95, 'default': 90},
            {'name': 'oversold', 'type': int, 'min': 5, 'max': 15, 'default': 10},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 1.5, 'max': 4.0, 'default': 2.0},
        ]

    def _calculate_streak(self, close: np.ndarray) -> np.ndarray:
        """Calculate up/down streak length"""
        streak = np.zeros(len(close))
        for i in range(1, len(close)):
            if close[i] > close[i-1]:
                streak[i] = max(0, streak[i-1]) + 1
            elif close[i] < close[i-1]:
                streak[i] = min(0, streak[i-1]) - 1
            else:
                streak[i] = 0
        return streak

    def _calculate_rsi(self, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate RSI of any data series"""
        delta = np.diff(data)
        delta = np.insert(delta, 0, 0)

        gains = np.where(delta > 0, delta, 0)
        losses = np.where(delta < 0, -delta, 0)

        avg_gain = np.zeros(len(data))
        avg_loss = np.zeros(len(data))

        # First average
        if period < len(data):
            avg_gain[period] = np.mean(gains[1:period+1])
            avg_loss[period] = np.mean(losses[1:period+1])

        # Smoothed averages
        for i in range(period + 1, len(data)):
            avg_gain[i] = (avg_gain[i-1] * (period - 1) + gains[i]) / period
            avg_loss[i] = (avg_loss[i-1] * (period - 1) + losses[i]) / period

        rs = np.zeros(len(data))
        for i in range(len(data)):
            if avg_loss[i] != 0:
                rs[i] = avg_gain[i] / avg_loss[i]

        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_percent_rank(self, close: np.ndarray, period: int) -> np.ndarray:
        """Calculate percent rank of 1-day ROC"""
        roc = np.zeros(len(close))
        for i in range(1, len(close)):
            if close[i-1] != 0:
                roc[i] = ((close[i] - close[i-1]) / close[i-1]) * 100

        pct_rank = np.zeros(len(close))
        for i in range(period, len(close)):
            current_roc = roc[i]
            lookback = roc[i-period:i]
            rank = np.sum(lookback < current_roc) / period * 100
            pct_rank[i] = rank

        return pct_rank

    def _calculate_connors_rsi(self, candles=None) -> float:
        """Calculate Connors RSI"""
        if candles is None:
            candles = self.candles

        close = candles[:, 2]

        # Component 1: RSI of price
        rsi = self._calculate_rsi(close, self.hp['rsi_period'])

        # Component 2: RSI of streak
        streak = self._calculate_streak(close)
        streak_rsi = self._calculate_rsi(streak, self.hp['streak_rsi_period'])

        # Component 3: Percent rank of ROC
        pct_rank = self._calculate_percent_rank(close, self.hp['pct_rank_period'])

        # Connors RSI = average of 3 components
        crsi = (rsi + streak_rsi + pct_rank) / 3

        return crsi[-1]

    @property
    def connors_rsi(self) -> float:
        return self._calculate_connors_rsi()

    @property
    def connors_rsi_prev(self) -> float:
        return self._calculate_connors_rsi(self.candles[:-1])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # Enter long when deeply oversold and starting to recover
        return self.connors_rsi_prev <= self.hp['oversold'] and self.connors_rsi > self.hp['oversold']

    def should_short(self) -> bool:
        # Enter short when deeply overbought and starting to decline
        return self.connors_rsi_prev >= self.hp['overbought'] and self.connors_rsi < self.hp['overbought']

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
        # Exit when reaching neutral territory
        if self.is_long and self.connors_rsi > 50:
            self.liquidate()
        elif self.is_short and self.connors_rsi < 50:
            self.liquidate()

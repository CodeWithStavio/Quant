"""
MOM_006: Stochastic RSI Strategy
--------------------------------
Stochastic applied to RSI values for more sensitive signals.

Entry Long: StochRSI crosses above 20 from oversold
Entry Short: StochRSI crosses below 80 from overbought

Optimal Timeframes: 5m, 15m, 1h
Complexity: 4/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class StochasticRSI(Strategy):
    """Stochastic RSI Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MOM_006"
        self.strategy_name = "Stochastic RSI"
        self.complexity = 4
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'rsi_period', 'type': int, 'min': 7, 'max': 21, 'default': 14},
            {'name': 'stoch_period', 'type': int, 'min': 7, 'max': 21, 'default': 14},
            {'name': 'k_smooth', 'type': int, 'min': 1, 'max': 5, 'default': 3},
            {'name': 'd_smooth', 'type': int, 'min': 1, 'max': 5, 'default': 3},
            {'name': 'overbought', 'type': int, 'min': 75, 'max': 90, 'default': 80},
            {'name': 'oversold', 'type': int, 'min': 10, 'max': 25, 'default': 20},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 1.5, 'max': 4.0, 'default': 2.5},
        ]

    def _calculate_stoch_rsi(self, candles=None) -> tuple:
        """Calculate Stochastic RSI (K and D lines)"""
        if candles is None:
            candles = self.candles

        rsi = ta.rsi(candles, period=self.hp['rsi_period'], sequential=True)
        period = self.hp['stoch_period']

        # Calculate Stochastic of RSI
        stoch_rsi = np.zeros(len(rsi))
        for i in range(period - 1, len(rsi)):
            rsi_min = np.min(rsi[i-period+1:i+1])
            rsi_max = np.max(rsi[i-period+1:i+1])
            if rsi_max - rsi_min > 0:
                stoch_rsi[i] = ((rsi[i] - rsi_min) / (rsi_max - rsi_min)) * 100

        # Smooth K
        k = np.convolve(stoch_rsi, np.ones(self.hp['k_smooth'])/self.hp['k_smooth'], mode='same')
        # Smooth D
        d = np.convolve(k, np.ones(self.hp['d_smooth'])/self.hp['d_smooth'], mode='same')

        return k[-1], d[-1]

    @property
    def stoch_rsi_k(self) -> float:
        k, d = self._calculate_stoch_rsi()
        return k

    @property
    def stoch_rsi_d(self) -> float:
        k, d = self._calculate_stoch_rsi()
        return d

    @property
    def stoch_rsi_k_prev(self) -> float:
        k, d = self._calculate_stoch_rsi(self.candles[:-1])
        return k

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        crossed_above = self.stoch_rsi_k_prev <= self.hp['oversold'] and self.stoch_rsi_k > self.hp['oversold']
        return crossed_above

    def should_short(self) -> bool:
        crossed_below = self.stoch_rsi_k_prev >= self.hp['overbought'] and self.stoch_rsi_k < self.hp['overbought']
        return crossed_below

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
        if self.is_long and self.stoch_rsi_k > 80:
            self.liquidate()
        elif self.is_short and self.stoch_rsi_k < 20:
            self.liquidate()

"""
CRYPTO_003: Altcoin Season Proxy Strategy
-----------------------------------------
Detect altcoin season conditions using momentum.

Entry Long: Strong bullish momentum (altcoin season)
Entry Short: Weak momentum (altcoin winter)

Optimal Timeframes: 4h, 1d
Complexity: 5/10
Crypto Suitability: 10/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class AltcoinSeasonProxy(Strategy):
    """Altcoin Season Proxy Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "CRYPTO_003"
        self.strategy_name = "Altcoin Season Proxy"
        self.complexity = 5
        self.crypto_suitability = 10

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 20, 'max': 50, 'default': 30},
            {'name': 'momentum_threshold', 'type': float, 'min': 5, 'max': 15, 'default': 10},
            {'name': 'volume_surge', 'type': float, 'min': 1.3, 'max': 2.0, 'default': 1.5},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 2.0, 'max': 3.0, 'default': 2.5},
        ]

    def _is_altseason(self) -> bool:
        """Detect altcoin season conditions"""
        lookback = self.hp['lookback']

        # Strong momentum
        roc = ta.roc(self.candles, period=lookback)
        strong_momentum = roc > self.hp['momentum_threshold']

        # High volume
        avg_vol = np.mean(self.candles[-lookback*2:-lookback, 5])
        recent_vol = np.mean(self.candles[-lookback:, 5])
        high_volume = recent_vol > avg_vol * self.hp['volume_surge']

        # RSI not oversold
        rsi = ta.rsi(self.candles, period=14)
        not_oversold = rsi > 40

        return strong_momentum and high_volume and not_oversold

    def _is_altwinter(self) -> bool:
        """Detect altcoin winter conditions"""
        lookback = self.hp['lookback']

        # Weak momentum
        roc = ta.roc(self.candles, period=lookback)
        weak_momentum = roc < -self.hp['momentum_threshold']

        # Declining volume
        avg_vol = np.mean(self.candles[-lookback*2:-lookback, 5])
        recent_vol = np.mean(self.candles[-lookback:, 5])
        low_volume = recent_vol < avg_vol * 0.7

        # RSI not overbought
        rsi = ta.rsi(self.candles, period=14)
        not_overbought = rsi < 60

        return weak_momentum and low_volume and not_overbought

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self._is_altseason()

    def should_short(self) -> bool:
        return self._is_altwinter()

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
        rsi = ta.rsi(self.candles, period=14)
        if self.is_long and rsi > 75:
            self.liquidate()
        elif self.is_short and rsi < 25:
            self.liquidate()

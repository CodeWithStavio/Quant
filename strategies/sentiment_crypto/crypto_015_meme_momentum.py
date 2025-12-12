"""
CRYPTO_015: Meme Momentum Strategy
----------------------------------
Trade explosive momentum patterns typical of meme coins.

Entry Long: Explosive volume and price surge
Entry Short: Volume exhaustion after pump

Optimal Timeframes: 15m, 1h
Complexity: 5/10
Crypto Suitability: 10/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class MemeMomentum(Strategy):
    """Meme Momentum Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "CRYPTO_015"
        self.strategy_name = "Meme Momentum"
        self.complexity = 5
        self.crypto_suitability = 10

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'vol_lookback', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'explosion_mult', 'type': float, 'min': 3.0, 'max': 6.0, 'default': 4.0},
            {'name': 'price_surge', 'type': float, 'min': 2.0, 'max': 5.0, 'default': 3.0},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 2.0, 'max': 3.0, 'default': 2.5},
        ]

    @property
    def avg_volume(self) -> float:
        return np.mean(self.candles[-self.hp['vol_lookback']-1:-1, 5])

    @property
    def volume_ratio(self) -> float:
        return self.candles[-1, 5] / self.avg_volume if self.avg_volume > 0 else 1

    @property
    def price_change(self) -> float:
        """Price change percentage over last few candles"""
        return (self.close - self.candles[-5, 2]) / self.candles[-5, 2] * 100

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def rsi(self) -> float:
        return ta.rsi(self.candles, period=14)

    def _is_explosive_move(self) -> bool:
        """Detect explosive upward move"""
        huge_volume = self.volume_ratio > self.hp['explosion_mult']
        big_price_move = self.price_change > self.hp['price_surge']
        green_candle = self.close > self.open
        return huge_volume and big_price_move and green_candle

    def _is_pump_exhaustion(self) -> bool:
        """Detect pump exhaustion (short opportunity)"""
        # Recent huge move
        lookback = 10
        max_roc = 0
        for i in range(1, lookback):
            if len(self.candles) > i + 5:
                roc = (self.candles[-i, 2] - self.candles[-i-5, 2]) / self.candles[-i-5, 2] * 100
                max_roc = max(max_roc, roc)

        had_pump = max_roc > self.hp['price_surge'] * 2

        # Current exhaustion signals
        declining_volume = self.volume_ratio < 0.5
        overbought = self.rsi > 75
        red_candle = self.close < self.open

        return had_pump and (declining_volume or overbought) and red_candle

    def should_long(self) -> bool:
        return self._is_explosive_move() and self.rsi < 70

    def should_short(self) -> bool:
        return self._is_pump_exhaustion()

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
        # Quick exits for meme plays
        if self.is_long:
            # Take profit on momentum loss
            if self.rsi > 80 or self.volume_ratio < 1:
                self.liquidate()
        elif self.is_short:
            # Cover on bounce
            if self.rsi < 30:
                self.liquidate()

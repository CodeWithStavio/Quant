"""
ONCHAIN_003: Whale Activity Proxy Strategy
------------------------------------------
Detect whale activity through volume spikes.

Entry Long: Whale buying detected (large volume on up move)
Entry Short: Whale selling detected (large volume on down move)

Optimal Timeframes: 1h, 4h
Complexity: 5/10
Crypto Suitability: 10/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class WhaleActivityProxy(Strategy):
    """Whale Activity Proxy Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ONCHAIN_003"
        self.strategy_name = "Whale Activity Proxy"
        self.complexity = 5
        self.crypto_suitability = 10

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'vol_lookback', 'type': int, 'min': 20, 'max': 50, 'default': 30},
            {'name': 'whale_multiplier', 'type': float, 'min': 3.0, 'max': 6.0, 'default': 4.0},
            {'name': 'min_price_move', 'type': float, 'min': 0.5, 'max': 2.0, 'default': 1.0},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    @property
    def avg_volume(self) -> float:
        return np.mean(self.candles[-self.hp['vol_lookback']-1:-1, 5])

    @property
    def current_volume(self) -> float:
        return self.candles[-1, 5]

    @property
    def is_whale_volume(self) -> bool:
        return self.current_volume > self.avg_volume * self.hp['whale_multiplier']

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def price_move_pct(self) -> float:
        return abs(self.close - self.open) / self.open * 100

    def should_long(self) -> bool:
        # Whale buying: huge volume on green candle with significant move
        is_green = self.close > self.open
        big_move = self.price_move_pct > self.hp['min_price_move']
        return self.is_whale_volume and is_green and big_move

    def should_short(self) -> bool:
        # Whale selling: huge volume on red candle with significant move
        is_red = self.close < self.open
        big_move = self.price_move_pct > self.hp['min_price_move']
        return self.is_whale_volume and is_red and big_move

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
        # Trail with ATR
        if self.is_long:
            trail_stop = self.close - (self.atr * 1.5)
            if trail_stop > self.average_entry_price:
                self.stop_loss = self.position.qty, trail_stop
        elif self.is_short:
            trail_stop = self.close + (self.atr * 1.5)
            if trail_stop < self.average_entry_price:
                self.stop_loss = self.position.qty, trail_stop

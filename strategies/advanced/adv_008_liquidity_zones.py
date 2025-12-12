"""
ADV_008: Liquidity Zones Strategy
---------------------------------
Trade based on liquidity pool detection.

Entry Long: Sweep of lows + reversal
Entry Short: Sweep of highs + reversal

Optimal Timeframes: 15m, 1h
Complexity: 7/10
Crypto Suitability: 9/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class LiquidityZones(Strategy):
    """Liquidity Zones Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ADV_008"
        self.strategy_name = "Liquidity Zones"
        self.complexity = 7
        self.crypto_suitability = 9

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 15, 'max': 40, 'default': 25},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
        ]

    def _find_liquidity_pools(self) -> dict:
        """Find liquidity pool zones (cluster of lows/highs)"""
        lookback = self.hp['lookback']

        # Find equal lows (buy-side liquidity)
        lows = self.candles[-lookback:-1, 4]
        buy_side_liquidity = np.min(lows)

        # Find equal highs (sell-side liquidity)
        highs = self.candles[-lookback:-1, 3]
        sell_side_liquidity = np.max(highs)

        return {
            'buy_side': buy_side_liquidity,
            'sell_side': sell_side_liquidity
        }

    def _is_buy_side_sweep(self) -> bool:
        """Detect sweep of buy-side liquidity (lows)"""
        pools = self._find_liquidity_pools()

        # Price swept below lows
        swept = self.low < pools['buy_side']

        # But closed above
        closed_above = self.close > pools['buy_side']

        # Bullish reversal candle
        bullish = self.close > self.open

        return swept and closed_above and bullish

    def _is_sell_side_sweep(self) -> bool:
        """Detect sweep of sell-side liquidity (highs)"""
        pools = self._find_liquidity_pools()

        # Price swept above highs
        swept = self.high > pools['sell_side']

        # But closed below
        closed_below = self.close < pools['sell_side']

        # Bearish reversal candle
        bearish = self.close < self.open

        return swept and closed_below and bearish

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self._is_buy_side_sweep()

    def should_short(self) -> bool:
        return self._is_sell_side_sweep()

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = self.low - (self.atr * 0.3)
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        entry = self.price
        stop = self.high + (self.atr * 0.3)
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop

    def update_position(self):
        if self.is_long:
            trail = self.close - self.atr
            if trail > self.average_entry_price:
                self.stop_loss = self.position.qty, trail
        elif self.is_short:
            trail = self.close + self.atr
            if trail < self.average_entry_price:
                self.stop_loss = self.position.qty, trail

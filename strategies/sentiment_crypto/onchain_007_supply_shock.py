"""
ONCHAIN_007: Supply Shock Proxy Strategy
----------------------------------------
Detect supply shock conditions using volume analysis.

Entry Long: Supply shock detected (low volume breakout)
Entry Short: Supply flood detected (high volume breakdown)

Optimal Timeframes: 4h, 1d
Complexity: 7/10
Crypto Suitability: 9/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class SupplyShockProxy(Strategy):
    """Supply Shock Proxy Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ONCHAIN_007"
        self.strategy_name = "Supply Shock Proxy"
        self.complexity = 7
        self.crypto_suitability = 9

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 20, 'max': 50, 'default': 30},
            {'name': 'vol_contraction', 'type': float, 'min': 0.3, 'max': 0.6, 'default': 0.5},
            {'name': 'breakout_pct', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 2.0, 'max': 3.0, 'default': 2.5},
        ]

    def _is_supply_shock(self) -> bool:
        """Detect supply shock: price up on low volume"""
        lookback = self.hp['lookback']

        # Volume contraction
        avg_vol = np.mean(self.candles[-lookback:-5, 5])
        recent_vol = np.mean(self.candles[-5:, 5])
        vol_contracted = recent_vol < avg_vol * self.hp['vol_contraction']

        # Price breakout
        recent_high = np.max(self.candles[-lookback:-5, 3])
        price_breakout = self.close > recent_high * (1 + self.hp['breakout_pct'] / 100)

        return vol_contracted and price_breakout

    def _is_supply_flood(self) -> bool:
        """Detect supply flood: price down on high volume"""
        lookback = self.hp['lookback']

        # Volume expansion
        avg_vol = np.mean(self.candles[-lookback:-5, 5])
        recent_vol = np.mean(self.candles[-5:, 5])
        vol_expanded = recent_vol > avg_vol * (1 / self.hp['vol_contraction'])

        # Price breakdown
        recent_low = np.min(self.candles[-lookback:-5, 4])
        price_breakdown = self.close < recent_low * (1 - self.hp['breakout_pct'] / 100)

        return vol_expanded and price_breakdown

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self._is_supply_shock()

    def should_short(self) -> bool:
        return self._is_supply_flood()

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
            trail = self.close - (self.atr * 2)
            if trail > self.average_entry_price:
                self.stop_loss = self.position.qty, trail
        elif self.is_short:
            trail = self.close + (self.atr * 2)
            if trail < self.average_entry_price:
                self.stop_loss = self.position.qty, trail

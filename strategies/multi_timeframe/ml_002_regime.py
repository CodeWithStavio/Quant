"""
ML_002: Regime Detection Strategy
---------------------------------
Detect market regime (trending/ranging/volatile) and adapt.

Entry Long: Trending regime with bullish bias
Entry Short: Trending regime with bearish bias

Optimal Timeframes: 1h, 4h
Complexity: 7/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class RegimeDetection(Strategy):
    """Regime Detection Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ML_002"
        self.strategy_name = "Regime Detection"
        self.complexity = 7
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 40, 'max': 80, 'default': 60},
            {'name': 'adx_period', 'type': int, 'min': 12, 'max': 18, 'default': 14},
            {'name': 'trend_threshold', 'type': int, 'min': 20, 'max': 30, 'default': 25},
            {'name': 'vol_lookback', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    @property
    def adx(self) -> float:
        return ta.adx(self.candles, period=self.hp['adx_period'])

    @property
    def di_plus(self) -> float:
        return ta.di(self.candles, period=self.hp['adx_period'])[0]

    @property
    def di_minus(self) -> float:
        return ta.di(self.candles, period=self.hp['adx_period'])[1]

    @property
    def volatility(self) -> float:
        """Calculate realized volatility"""
        closes = self.candles[-self.hp['vol_lookback']:, 2]
        returns = np.diff(closes) / closes[:-1]
        return np.std(returns) * np.sqrt(252)  # Annualized

    @property
    def avg_volatility(self) -> float:
        """Historical average volatility"""
        lookback = self.hp['lookback']
        vols = []
        for i in range(lookback - self.hp['vol_lookback']):
            end_idx = -(i + 1) if i > 0 else len(self.candles)
            start_idx = end_idx - self.hp['vol_lookback']
            closes = self.candles[start_idx:end_idx, 2]
            returns = np.diff(closes) / closes[:-1]
            vols.append(np.std(returns) * np.sqrt(252))
        return np.mean(vols) if vols else self.volatility

    @property
    def regime(self) -> str:
        """Detect current market regime"""
        if self.adx > self.hp['trend_threshold']:
            return 'trending'
        elif self.volatility > self.avg_volatility * 1.5:
            return 'volatile'
        else:
            return 'ranging'

    @property
    def trend_direction(self) -> str:
        if self.di_plus > self.di_minus:
            return 'bullish'
        else:
            return 'bearish'

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self.regime == 'trending' and self.trend_direction == 'bullish'

    def should_short(self) -> bool:
        return self.regime == 'trending' and self.trend_direction == 'bearish'

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        # Wider stops in volatile regimes
        mult = self.hp['atr_multiplier_sl'] * (1.5 if self.regime == 'volatile' else 1.0)
        stop = entry - (self.atr * mult)
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        entry = self.price
        mult = self.hp['atr_multiplier_sl'] * (1.5 if self.regime == 'volatile' else 1.0)
        stop = entry + (self.atr * mult)
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop

    def update_position(self):
        # Exit if regime changes
        if self.is_long and (self.regime != 'trending' or self.trend_direction != 'bullish'):
            self.liquidate()
        elif self.is_short and (self.regime != 'trending' or self.trend_direction != 'bearish'):
            self.liquidate()

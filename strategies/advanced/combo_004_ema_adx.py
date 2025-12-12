"""
COMBO_004: EMA + ADX Combo Strategy
-----------------------------------
Combine EMA crossover with ADX trend strength.

Entry Long: EMA bullish cross + Strong ADX + DI+ > DI-
Entry Short: EMA bearish cross + Strong ADX + DI- > DI+

Optimal Timeframes: 1h, 4h
Complexity: 5/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
from typing import List, Dict


class EMAaDXCombo(Strategy):
    """EMA + ADX Combo Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "COMBO_004"
        self.strategy_name = "EMA ADX Combo"
        self.complexity = 5
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'fast_ema', 'type': int, 'min': 8, 'max': 15, 'default': 10},
            {'name': 'slow_ema', 'type': int, 'min': 18, 'max': 30, 'default': 20},
            {'name': 'adx_period', 'type': int, 'min': 10, 'max': 18, 'default': 14},
            {'name': 'adx_threshold', 'type': int, 'min': 20, 'max': 30, 'default': 25},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    @property
    def fast_ema(self) -> float:
        return ta.ema(self.candles, period=self.hp['fast_ema'])

    @property
    def slow_ema(self) -> float:
        return ta.ema(self.candles, period=self.hp['slow_ema'])

    @property
    def prev_fast_ema(self) -> float:
        return ta.ema(self.candles[:-1], period=self.hp['fast_ema'])

    @property
    def prev_slow_ema(self) -> float:
        return ta.ema(self.candles[:-1], period=self.hp['slow_ema'])

    @property
    def adx(self) -> float:
        return ta.adx(self.candles, period=self.hp['adx_period'])

    @property
    def di(self) -> tuple:
        return ta.di(self.candles, period=self.hp['adx_period'])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        ema_cross_up = self.prev_fast_ema <= self.prev_slow_ema and self.fast_ema > self.slow_ema
        strong_trend = self.adx > self.hp['adx_threshold']
        di_plus, di_minus = self.di
        bullish_di = di_plus > di_minus

        return ema_cross_up and strong_trend and bullish_di

    def should_short(self) -> bool:
        ema_cross_down = self.prev_fast_ema >= self.prev_slow_ema and self.fast_ema < self.slow_ema
        strong_trend = self.adx > self.hp['adx_threshold']
        di_plus, di_minus = self.di
        bearish_di = di_minus > di_plus

        return ema_cross_down and strong_trend and bearish_di

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
        di_plus, di_minus = self.di
        if self.is_long and di_minus > di_plus:
            self.liquidate()
        elif self.is_short and di_plus > di_minus:
            self.liquidate()

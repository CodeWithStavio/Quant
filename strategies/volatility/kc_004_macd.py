"""
KC_004: Keltner + MACD Confirmation Strategy
--------------------------------------------
Keltner breakout confirmed by MACD direction.

Entry Long: KC breakout up AND MACD bullish
Entry Short: KC breakout down AND MACD bearish

Optimal Timeframes: 15m, 1h, 4h
Complexity: 4/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
from typing import List, Dict


class KeltnerMACD(Strategy):
    """Keltner + MACD Confirmation Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "KC_004"
        self.strategy_name = "Keltner + MACD"
        self.complexity = 4
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'kc_period', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'kc_mult', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'macd_fast', 'type': int, 'min': 8, 'max': 15, 'default': 12},
            {'name': 'macd_slow', 'type': int, 'min': 20, 'max': 30, 'default': 26},
            {'name': 'macd_signal', 'type': int, 'min': 7, 'max': 12, 'default': 9},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 5.0, 'default': 3.5},
        ]

    def _get_keltner(self):
        ema = ta.ema(self.candles, period=self.hp['kc_period'])
        atr_val = ta.atr(self.candles, period=self.hp['kc_period'])
        upper = ema + (atr_val * self.hp['kc_mult'])
        lower = ema - (atr_val * self.hp['kc_mult'])
        return upper, ema, lower

    @property
    def kc_upper(self) -> float:
        upper, middle, lower = self._get_keltner()
        return upper

    @property
    def kc_lower(self) -> float:
        upper, middle, lower = self._get_keltner()
        return lower

    @property
    def macd_bullish(self) -> bool:
        macd, signal, hist = ta.macd(
            self.candles,
            fast_period=self.hp['macd_fast'],
            slow_period=self.hp['macd_slow'],
            signal_period=self.hp['macd_signal']
        )
        return macd > signal and hist > 0

    @property
    def macd_bearish(self) -> bool:
        macd, signal, hist = ta.macd(
            self.candles,
            fast_period=self.hp['macd_fast'],
            slow_period=self.hp['macd_slow'],
            signal_period=self.hp['macd_signal']
        )
        return macd < signal and hist < 0

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self.close > self.kc_upper and self.macd_bullish

    def should_short(self) -> bool:
        return self.close < self.kc_lower and self.macd_bearish

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
        if self.is_long and self.macd_bearish:
            self.liquidate()
        elif self.is_short and self.macd_bullish:
            self.liquidate()

"""
COMBO_003: Ichimoku + RSI Combo Strategy
----------------------------------------
Combine Ichimoku cloud with RSI confirmation.

Entry Long: Price above cloud + RSI bullish
Entry Short: Price below cloud + RSI bearish

Optimal Timeframes: 4h, 1d
Complexity: 6/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
from typing import List, Dict


class IchimokuRSICombo(Strategy):
    """Ichimoku + RSI Combo Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "COMBO_003"
        self.strategy_name = "Ichimoku RSI Combo"
        self.complexity = 6
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'rsi_period', 'type': int, 'min': 10, 'max': 18, 'default': 14},
            {'name': 'rsi_threshold', 'type': int, 'min': 45, 'max': 55, 'default': 50},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    @property
    def ichimoku(self) -> tuple:
        return ta.ichimoku_cloud(self.candles)

    @property
    def rsi(self) -> float:
        return ta.rsi(self.candles, period=self.hp['rsi_period'])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        conversion, base, span_a, span_b, lagging = self.ichimoku

        # Price above cloud
        cloud_top = max(span_a, span_b)
        above_cloud = self.close > cloud_top

        # Conversion above base
        bullish_cross = conversion > base

        # RSI confirmation
        rsi_bullish = self.rsi > self.hp['rsi_threshold']

        return above_cloud and bullish_cross and rsi_bullish

    def should_short(self) -> bool:
        conversion, base, span_a, span_b, lagging = self.ichimoku

        # Price below cloud
        cloud_bottom = min(span_a, span_b)
        below_cloud = self.close < cloud_bottom

        # Conversion below base
        bearish_cross = conversion < base

        # RSI confirmation
        rsi_bearish = self.rsi < self.hp['rsi_threshold']

        return below_cloud and bearish_cross and rsi_bearish

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
        conversion, base, span_a, span_b, lagging = self.ichimoku
        if self.is_long and conversion < base:
            self.liquidate()
        elif self.is_short and conversion > base:
            self.liquidate()

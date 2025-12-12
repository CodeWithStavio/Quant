"""
ADV_009: Fair Value Gap Strategy
--------------------------------
Trade based on FVG/imbalance detection.

Entry Long: Price fills bullish FVG
Entry Short: Price fills bearish FVG

Optimal Timeframes: 15m, 1h
Complexity: 7/10
Crypto Suitability: 9/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class FairValueGap(Strategy):
    """Fair Value Gap Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ADV_009"
        self.strategy_name = "Fair Value Gap"
        self.complexity = 7
        self.crypto_suitability = 9

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 10, 'max': 30, 'default': 15},
            {'name': 'min_gap_atr', 'type': float, 'min': 0.3, 'max': 1.0, 'default': 0.5},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
        ]

    def _find_bullish_fvg(self) -> dict:
        """Find unfilled bullish FVG"""
        lookback = self.hp['lookback']
        min_gap = self.atr * self.hp['min_gap_atr']

        for i in range(3, lookback):
            # Bullish FVG: Gap between candle 1 high and candle 3 low
            candle1_high = self.candles[-i-2, 3]
            candle2 = self.candles[-i-1]  # Middle candle
            candle3_low = self.candles[-i, 4]

            # Gap exists
            if candle3_low > candle1_high + min_gap:
                # Check if unfilled
                filled = False
                for j in range(-i+1, 0):
                    if self.candles[j, 4] < candle3_low:
                        filled = True
                        break

                if not filled:
                    return {
                        'top': candle3_low,
                        'bottom': candle1_high,
                        'found': True
                    }

        return {'found': False}

    def _find_bearish_fvg(self) -> dict:
        """Find unfilled bearish FVG"""
        lookback = self.hp['lookback']
        min_gap = self.atr * self.hp['min_gap_atr']

        for i in range(3, lookback):
            # Bearish FVG: Gap between candle 1 low and candle 3 high
            candle1_low = self.candles[-i-2, 4]
            candle3_high = self.candles[-i, 3]

            # Gap exists
            if candle1_low > candle3_high + min_gap:
                # Check if unfilled
                filled = False
                for j in range(-i+1, 0):
                    if self.candles[j, 3] > candle3_high:
                        filled = True
                        break

                if not filled:
                    return {
                        'top': candle1_low,
                        'bottom': candle3_high,
                        'found': True
                    }

        return {'found': False}

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        fvg = self._find_bullish_fvg()
        if not fvg['found']:
            return False

        # Price entering FVG from above
        entering_fvg = self.low <= fvg['top'] and self.close >= fvg['bottom']
        bullish = self.close > self.open

        return entering_fvg and bullish

    def should_short(self) -> bool:
        fvg = self._find_bearish_fvg()
        if not fvg['found']:
            return False

        # Price entering FVG from below
        entering_fvg = self.high >= fvg['bottom'] and self.close <= fvg['top']
        bearish = self.close < self.open

        return entering_fvg and bearish

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        fvg = self._find_bullish_fvg()
        stop = fvg['bottom'] - (self.atr * 0.3) if fvg['found'] else entry - (self.atr * 2)
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        entry = self.price
        fvg = self._find_bearish_fvg()
        stop = fvg['top'] + (self.atr * 0.3) if fvg['found'] else entry + (self.atr * 2)
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

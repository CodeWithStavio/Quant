"""
ADV_012: Mitigation Block Strategy
----------------------------------
Trade based on mitigation block detection.

Entry Long: Price mitigating bearish imbalance
Entry Short: Price mitigating bullish imbalance

Optimal Timeframes: 15m, 1h
Complexity: 7/10
Crypto Suitability: 9/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class MitigationBlock(Strategy):
    """Mitigation Block Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ADV_012"
        self.strategy_name = "Mitigation Block"
        self.complexity = 7
        self.crypto_suitability = 9

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 10, 'max': 30, 'default': 20},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
        ]

    def _find_bullish_mitigation(self) -> dict:
        """
        Find bullish mitigation (price returning to mitigate previous selling)
        """
        lookback = self.hp['lookback']

        for i in range(5, lookback):
            # Large bearish candle (selling imbalance)
            body = abs(self.candles[-i, 2] - self.candles[-i, 1])
            range_size = self.candles[-i, 3] - self.candles[-i, 4]

            if range_size > 0 and body / range_size > 0.6:  # Strong bearish candle
                if self.candles[-i, 2] < self.candles[-i, 1]:
                    # Price went lower then returned
                    went_lower = np.min(self.candles[-i+1:-2, 4]) < self.candles[-i, 4]
                    returned = self.close > self.candles[-i, 4]

                    if went_lower and returned:
                        return {
                            'zone_high': self.candles[-i, 1],  # Open of bearish candle
                            'zone_low': self.candles[-i, 2],   # Close of bearish candle
                            'found': True
                        }

        return {'found': False}

    def _find_bearish_mitigation(self) -> dict:
        """
        Find bearish mitigation (price returning to mitigate previous buying)
        """
        lookback = self.hp['lookback']

        for i in range(5, lookback):
            # Large bullish candle (buying imbalance)
            body = abs(self.candles[-i, 2] - self.candles[-i, 1])
            range_size = self.candles[-i, 3] - self.candles[-i, 4]

            if range_size > 0 and body / range_size > 0.6:  # Strong bullish candle
                if self.candles[-i, 2] > self.candles[-i, 1]:
                    # Price went higher then returned
                    went_higher = np.max(self.candles[-i+1:-2, 3]) > self.candles[-i, 3]
                    returned = self.close < self.candles[-i, 3]

                    if went_higher and returned:
                        return {
                            'zone_high': self.candles[-i, 2],  # Close of bullish candle
                            'zone_low': self.candles[-i, 1],   # Open of bullish candle
                            'found': True
                        }

        return {'found': False}

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        mitigation = self._find_bullish_mitigation()
        if not mitigation['found']:
            return False

        # Price in mitigation zone
        in_zone = self.low <= mitigation['zone_high'] and self.close >= mitigation['zone_low']
        bullish = self.close > self.open

        return in_zone and bullish

    def should_short(self) -> bool:
        mitigation = self._find_bearish_mitigation()
        if not mitigation['found']:
            return False

        # Price in mitigation zone
        in_zone = self.high >= mitigation['zone_low'] and self.close <= mitigation['zone_high']
        bearish = self.close < self.open

        return in_zone and bearish

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        mitigation = self._find_bullish_mitigation()
        stop = mitigation['zone_low'] - (self.atr * 0.3) if mitigation['found'] else entry - (self.atr * 2)
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        entry = self.price
        mitigation = self._find_bearish_mitigation()
        stop = mitigation['zone_high'] + (self.atr * 0.3) if mitigation['found'] else entry + (self.atr * 2)
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

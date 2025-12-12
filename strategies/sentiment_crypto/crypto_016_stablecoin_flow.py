"""
CRYPTO_016: Stablecoin Flow Proxy Strategy
------------------------------------------
Simulate stablecoin flow effects using volume analysis.

Entry Long: Money flow increasing (accumulation)
Entry Short: Money flow decreasing (distribution)

Optimal Timeframes: 4h, 1d
Complexity: 6/10
Crypto Suitability: 10/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class StablecoinFlowProxy(Strategy):
    """Stablecoin Flow Proxy Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "CRYPTO_016"
        self.strategy_name = "Stablecoin Flow Proxy"
        self.complexity = 6
        self.crypto_suitability = 10

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'flow_threshold', 'type': float, 'min': 60, 'max': 80, 'default': 70},
            {'name': 'volume_ma', 'type': int, 'min': 10, 'max': 25, 'default': 15},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 2.0, 'max': 3.0, 'default': 2.5},
        ]

    def _calculate_money_flow(self) -> float:
        """
        Calculate money flow index proxy
        Uses typical price * volume as flow indicator
        """
        lookback = self.hp['lookback']

        positive_flow = 0
        negative_flow = 0

        for i in range(1, lookback + 1):
            # Typical price
            tp = (self.candles[-i, 3] + self.candles[-i, 4] + self.candles[-i, 2]) / 3
            prev_tp = (self.candles[-i-1, 3] + self.candles[-i-1, 4] + self.candles[-i-1, 2]) / 3

            money_flow = tp * self.candles[-i, 5]

            if tp > prev_tp:
                positive_flow += money_flow
            else:
                negative_flow += money_flow

        if negative_flow == 0:
            return 100

        money_ratio = positive_flow / negative_flow
        mfi = 100 - (100 / (1 + money_ratio))
        return mfi

    def _get_flow_trend(self) -> int:
        """Get money flow trend direction"""
        current_flow = self._calculate_money_flow()

        # Calculate previous flow
        lookback = self.hp['lookback']
        positive_flow = 0
        negative_flow = 0

        for i in range(2, lookback + 2):
            tp = (self.candles[-i, 3] + self.candles[-i, 4] + self.candles[-i, 2]) / 3
            prev_tp = (self.candles[-i-1, 3] + self.candles[-i-1, 4] + self.candles[-i-1, 2]) / 3
            money_flow = tp * self.candles[-i, 5]

            if tp > prev_tp:
                positive_flow += money_flow
            else:
                negative_flow += money_flow

        if negative_flow == 0:
            prev_flow = 100
        else:
            money_ratio = positive_flow / negative_flow
            prev_flow = 100 - (100 / (1 + money_ratio))

        if current_flow > prev_flow:
            return 1
        elif current_flow < prev_flow:
            return -1
        return 0

    @property
    def money_flow(self) -> float:
        return self._calculate_money_flow()

    @property
    def flow_trend(self) -> int:
        return self._get_flow_trend()

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # Strong inflow with increasing trend
        high_flow = self.money_flow > self.hp['flow_threshold']
        increasing = self.flow_trend == 1
        return high_flow and increasing

    def should_short(self) -> bool:
        # Weak outflow with decreasing trend
        low_flow = self.money_flow < (100 - self.hp['flow_threshold'])
        decreasing = self.flow_trend == -1
        return low_flow and decreasing

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
        # Exit on flow reversal
        if self.is_long and self.flow_trend == -1:
            self.liquidate()
        elif self.is_short and self.flow_trend == 1:
            self.liquidate()

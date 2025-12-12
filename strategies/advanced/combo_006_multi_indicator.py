"""
COMBO_006: Multi-Indicator Combo Strategy
-----------------------------------------
Combine multiple indicators for signal confirmation.

Entry Long: Majority of indicators bullish
Entry Short: Majority of indicators bearish

Optimal Timeframes: 1h, 4h
Complexity: 6/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
from typing import List, Dict


class MultiIndicatorCombo(Strategy):
    """Multi-Indicator Combo Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "COMBO_006"
        self.strategy_name = "Multi Indicator Combo"
        self.complexity = 6
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'agreement_threshold', 'type': int, 'min': 3, 'max': 5, 'default': 4},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    def _get_indicator_signals(self) -> dict:
        """Get signals from multiple indicators"""
        signals = {'bullish': 0, 'bearish': 0}

        # 1. MA trend
        ma = ta.sma(self.candles, period=20)
        if self.close > ma:
            signals['bullish'] += 1
        else:
            signals['bearish'] += 1

        # 2. RSI
        rsi = ta.rsi(self.candles, period=14)
        if 40 < rsi < 60:
            pass  # Neutral
        elif rsi > 50:
            signals['bullish'] += 1
        else:
            signals['bearish'] += 1

        # 3. MACD
        macd = ta.macd(self.candles)
        if macd[0] > macd[1]:
            signals['bullish'] += 1
        else:
            signals['bearish'] += 1

        # 4. ADX + DI
        adx = ta.adx(self.candles, period=14)
        di = ta.di(self.candles, period=14)
        if adx > 20:
            if di[0] > di[1]:
                signals['bullish'] += 1
            else:
                signals['bearish'] += 1

        # 5. Momentum
        roc = ta.roc(self.candles, period=10)
        if roc > 0:
            signals['bullish'] += 1
        else:
            signals['bearish'] += 1

        # 6. Stochastic
        stoch = ta.stoch(self.candles, fastk_period=14, slowk_period=3, slowd_period=3)
        if stoch[0] > stoch[1]:
            signals['bullish'] += 1
        else:
            signals['bearish'] += 1

        return signals

    @property
    def signals(self) -> dict:
        return self._get_indicator_signals()

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self.signals['bullish'] >= self.hp['agreement_threshold']

    def should_short(self) -> bool:
        return self.signals['bearish'] >= self.hp['agreement_threshold']

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
        signals = self.signals
        if self.is_long and signals['bearish'] >= 3:
            self.liquidate()
        elif self.is_short and signals['bullish'] >= 3:
            self.liquidate()

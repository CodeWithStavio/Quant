"""
Bollinger Band Strategies
-------------------------
Bollinger Bands and related volatility bands.

Strategies:
- BB_001: Bollinger Band Bounce
- BB_002: Bollinger Band Breakout
- BB_003: Bollinger Band Squeeze
- BB_004: Bollinger %B
- BB_005: Double Bollinger Bands
- BB_006: BB + RSI Combo
- BB_007: BB Walking the Bands
- BB_008: Bollinger Band Width
"""

from .bb_001_bounce import BBBounce
from .bb_002_breakout import BBBreakout
from .bb_003_squeeze import BBSqueeze
from .bb_004_percent_b import BBPercentB
from .bb_005_double_bb import DoubleBB
from .bb_006_rsi_combo import BBRSICombo
from .bb_007_walking import BBWalking
from .bb_008_width import BBWidth

__all__ = [
    'BBBounce',
    'BBBreakout',
    'BBSqueeze',
    'BBPercentB',
    'DoubleBB',
    'BBRSICombo',
    'BBWalking',
    'BBWidth',
]

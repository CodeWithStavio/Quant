"""
MACD Strategies
---------------
MACD and all variations.

Strategies:
- MACD_001: Classic MACD Crossover
- MACD_002: MACD Zero Line Cross
- MACD_003: MACD Histogram Reversal
- MACD_004: MACD Divergence
- MACD_005: MACD-V (Volatility Normalized)
- MACD_006: Impulse MACD (Elder)
- MACD_007: MACD with RSI Filter
- MACD_008: Multi-Timeframe MACD
"""

from .macd_001_crossover import MACDCrossover
from .macd_002_zero_cross import MACDZeroCross
from .macd_003_histogram import MACDHistogram
from .macd_004_divergence import MACDDivergence
from .macd_005_volatility import MACDVolatility
from .macd_006_impulse import MACDImpulse
from .macd_007_rsi_filter import MACDRSIFilter
from .macd_008_mtf import MACDMTF

__all__ = [
    'MACDCrossover',
    'MACDZeroCross',
    'MACDHistogram',
    'MACDDivergence',
    'MACDVolatility',
    'MACDImpulse',
    'MACDRSIFilter',
    'MACDMTF',
]

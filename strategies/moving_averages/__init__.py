"""
Moving Average Strategies
-------------------------
All strategies based on moving averages and their derivatives.

Strategies:
- MA_001: Simple Moving Average Crossover
- MA_002: Exponential Moving Average Crossover
- MA_003: DEMA/TEMA Crossover
- MA_004: Hull Moving Average
- MA_005: KAMA - Kaufman Adaptive MA
- MA_006: VWMA - Volume Weighted MA
- MA_007: ZLEMA - Zero Lag EMA
- MA_008: ALMA - Arnaud Legoux MA
- MA_009: McGinley Dynamic
- MA_010: JMA - Jurik Moving Average
- MA_011: MA Price Position
- MA_012: MA Slope Strategy
- MA_013: MA Fan/Ribbon
- MA_014: GMMA - Guppy Multiple Moving Average
- MA_015: Moving Average Envelope
"""

from .ma_001_sma_crossover import SMACrossover
from .ma_002_ema_crossover import EMACrossover
from .ma_003_dema_tema import DEMATEMACrossover
from .ma_004_hull_ma import HullMACrossover
from .ma_005_kama import KAMAStrategy
from .ma_006_vwma import VWMAStrategy
from .ma_007_zlema import ZLEMAStrategy
from .ma_008_alma import ALMAStrategy
from .ma_009_mcginley import McGinleyStrategy
from .ma_010_triple_ma import TripleMAStrategy
from .ma_011_price_position import MAPricePosition
from .ma_012_slope import MASlopeStrategy
from .ma_013_ribbon import MARibbon
from .ma_014_gmma import GMMACrossover
from .ma_015_envelope import MAEnvelope

__all__ = [
    'SMACrossover',
    'EMACrossover',
    'DEMATEMACrossover',
    'HullMACrossover',
    'KAMAStrategy',
    'VWMAStrategy',
    'ZLEMAStrategy',
    'ALMAStrategy',
    'McGinleyStrategy',
    'TripleMAStrategy',
    'MAPricePosition',
    'MASlopeStrategy',
    'MARibbon',
    'GMMACrossover',
    'MAEnvelope',
]

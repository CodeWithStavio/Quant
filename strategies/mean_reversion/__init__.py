"""
Mean Reversion and Breakout Strategies
--------------------------------------
Strategies based on mean reversion and breakout concepts.

Mean Reversion:
- MR_001: Z-Score Mean Reversion
- MR_002: RSI Mean Reversion
- MR_003: Bollinger Mean Reversion
- MR_004: Keltner Mean Reversion
- MR_005: Statistical Mean Reversion
- MR_006: Moving Average Deviation
- MR_007: Overbought/Oversold Reversion
- MR_008: Range Mean Reversion
- MR_009: Gap Fade
- MR_010: Momentum Mean Reversion

Breakout:
- BRK_001: Volatility Breakout
- BRK_002: Range Breakout
- BRK_003: Opening Range Breakout
- BRK_004: Consolidation Breakout
- BRK_005: Inside Bar Breakout
- BRK_006: ATR Breakout
- BRK_007: Momentum Breakout
- BRK_008: Channel Breakout
- BRK_009: Swing Breakout
- BRK_010: Volume Breakout
"""

from .mr_001_zscore import ZScoreMeanReversion
from .mr_002_rsi import RSIMeanReversion
from .mr_003_bollinger import BollingerMeanReversion
from .mr_004_keltner import KeltnerMeanReversion
from .mr_005_statistical import StatisticalMeanReversion
from .mr_006_ma_deviation import MADeviationMeanReversion
from .mr_007_overbought import OverboughtOversoldReversion
from .mr_008_range import RangeMeanReversion
from .mr_009_gap_fade import GapFade
from .mr_010_momentum import MomentumMeanReversion
from .brk_001_volatility import VolatilityBreakout
from .brk_002_range import RangeBreakout
from .brk_003_opening_range import OpeningRangeBreakout
from .brk_004_consolidation import ConsolidationBreakout
from .brk_005_inside_bar import InsideBarBreakout
from .brk_006_atr import ATRBreakoutStrategy
from .brk_007_momentum import MomentumBreakout
from .brk_008_channel import ChannelBreakout
from .brk_009_swing import SwingBreakout
from .brk_010_volume import VolumeBreakout

__all__ = [
    'ZScoreMeanReversion',
    'RSIMeanReversion',
    'BollingerMeanReversion',
    'KeltnerMeanReversion',
    'StatisticalMeanReversion',
    'MADeviationMeanReversion',
    'OverboughtOversoldReversion',
    'RangeMeanReversion',
    'GapFade',
    'MomentumMeanReversion',
    'VolatilityBreakout',
    'RangeBreakout',
    'OpeningRangeBreakout',
    'ConsolidationBreakout',
    'InsideBarBreakout',
    'ATRBreakoutStrategy',
    'MomentumBreakout',
    'ChannelBreakout',
    'SwingBreakout',
    'VolumeBreakout',
]

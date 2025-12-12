"""
Candlestick and Price Action Strategies
---------------------------------------
Strategies based on candlestick patterns and price action.

Single Candle Patterns:
- CNDL_001: Hammer/Hanging Man
- CNDL_002: Inverted Hammer/Shooting Star
- CNDL_003: Doji
- CNDL_004: Marubozu
- CNDL_005: Spinning Top

Double Candle Patterns:
- CNDL_006: Engulfing Pattern
- CNDL_007: Piercing/Dark Cloud
- CNDL_008: Harami
- CNDL_009: Morning/Evening Star
- CNDL_010: Three White Soldiers/Black Crows
- CNDL_011: Tweezer Tops/Bottoms
- CNDL_012: Three Inside Up/Down
- CNDL_013: Three Outside Up/Down

Price Action:
- PA_001: Support/Resistance Bounce
- PA_002: Support/Resistance Breakout
- PA_003: Trendline Strategy
- PA_004: Double Top/Bottom
- PA_005: Head and Shoulders
- PA_006: Wedge Pattern
- PA_007: Triangle Pattern
- PA_008: Price Channel
"""

from .cndl_001_hammer import HammerStrategy
from .cndl_002_shooting_star import ShootingStarStrategy
from .cndl_003_doji import DojiStrategy
from .cndl_004_marubozu import MarubozuStrategy
from .cndl_005_spinning_top import SpinningTopStrategy
from .cndl_006_engulfing import EngulfingStrategy
from .cndl_007_piercing import PiercingDarkCloud
from .cndl_008_harami import HaramiStrategy
from .cndl_009_morning_star import MorningEveningStar
from .cndl_010_three_soldiers import ThreeSoldiersCrows
from .cndl_011_tweezer import TweezerStrategy
from .cndl_012_three_inside import ThreeInsideStrategy
from .cndl_013_three_outside import ThreeOutsideStrategy
from .pa_001_sr_bounce import SRBounce
from .pa_002_sr_breakout import SRBreakout
from .pa_003_trendline import TrendlineStrategy
from .pa_004_double_top import DoubleTopBottom
from .pa_005_head_shoulders import HeadAndShoulders
from .pa_006_wedge import WedgeStrategy
from .pa_007_triangle import TriangleStrategy
from .pa_008_price_channel import PriceChannel

__all__ = [
    'HammerStrategy',
    'ShootingStarStrategy',
    'DojiStrategy',
    'MarubozuStrategy',
    'SpinningTopStrategy',
    'EngulfingStrategy',
    'PiercingDarkCloud',
    'HaramiStrategy',
    'MorningEveningStar',
    'ThreeSoldiersCrows',
    'TweezerStrategy',
    'ThreeInsideStrategy',
    'ThreeOutsideStrategy',
    'SRBounce',
    'SRBreakout',
    'TrendlineStrategy',
    'DoubleTopBottom',
    'HeadAndShoulders',
    'WedgeStrategy',
    'TriangleStrategy',
    'PriceChannel',
]

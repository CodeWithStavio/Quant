"""
Momentum Oscillator Strategies
------------------------------
RSI, Stochastic, CCI, Williams %R and derivatives.

Strategies:
- MOM_001: RSI Overbought/Oversold
- MOM_002: RSI Divergence
- MOM_003: RSI Trend Following
- MOM_004: RSI with MA Filter
- MOM_005: Stochastic Oscillator
- MOM_006: Stochastic RSI
- MOM_007: Double Stochastic
- MOM_008: Williams %R
- MOM_009: CCI Basic
- MOM_010: CCI Zero Line Cross
- MOM_011: Ultimate Oscillator
- MOM_012: Awesome Oscillator
- MOM_013: Momentum Indicator
- MOM_014: Rate of Change (ROC)
- MOM_015: TSI - True Strength Index
- MOM_016: Coppock Curve
- MOM_017: KST - Know Sure Thing
- MOM_018: TRIX
- MOM_019: PPO - Percentage Price Oscillator
- MOM_020: Connors RSI
"""

from .mom_001_rsi_obos import RSIOverboughtOversold
from .mom_002_rsi_divergence import RSIDivergence
from .mom_003_rsi_trend import RSITrendFollowing
from .mom_004_rsi_ma_filter import RSIWithMAFilter
from .mom_005_stochastic import StochasticOscillator
from .mom_006_stoch_rsi import StochasticRSI
from .mom_007_double_stoch import DoubleStochastic
from .mom_008_williams_r import WilliamsPercentR
from .mom_009_cci import CCIStrategy
from .mom_010_cci_zero import CCIZeroLine
from .mom_011_ultimate_osc import UltimateOscillator
from .mom_012_awesome_osc import AwesomeOscillator
from .mom_013_momentum import MomentumIndicator
from .mom_014_roc import RateOfChange
from .mom_015_tsi import TrueStrengthIndex
from .mom_016_coppock import CoppockCurve
from .mom_017_kst import KnowSureThing
from .mom_018_trix import TRIXStrategy
from .mom_019_ppo import PPOStrategy
from .mom_020_connors_rsi import ConnorsRSI

__all__ = [
    'RSIOverboughtOversold',
    'RSIDivergence',
    'RSITrendFollowing',
    'RSIWithMAFilter',
    'StochasticOscillator',
    'StochasticRSI',
    'DoubleStochastic',
    'WilliamsPercentR',
    'CCIStrategy',
    'CCIZeroLine',
    'UltimateOscillator',
    'AwesomeOscillator',
    'MomentumIndicator',
    'RateOfChange',
    'TrueStrengthIndex',
    'CoppockCurve',
    'KnowSureThing',
    'TRIXStrategy',
    'PPOStrategy',
    'ConnorsRSI',
]

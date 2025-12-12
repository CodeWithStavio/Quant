"""
Advanced, Seasonality, Risk, and Composite Strategies
------------------------------------------------------
34 advanced strategies covering various specialized approaches.
"""

# Seasonality Strategies
from .season_001_monthly import MonthlySeason
from .season_002_weekly import WeeklySeason
from .season_003_intraday import IntradaySeason
from .season_004_quarter import QuarterlyPattern
from .season_005_holiday import HolidayEffect

# Risk Management Strategies
from .risk_001_volatility_adj import VolatilityAdjusted
from .risk_002_drawdown_ctrl import DrawdownControl
from .risk_003_kelly import KellyCriterion
from .risk_004_var_limit import VaRLimit
from .risk_005_correlation_hedge import CorrelationHedge
from .risk_006_regime_filter import RegimeFilter
from .risk_007_equity_curve import EquityCurveTrading

# Composite/Combo Strategies
from .combo_001_ma_rsi import MARSICombo
from .combo_002_bb_macd import BBMACDCombo
from .combo_003_ichimoku_rsi import IchimokuRSICombo
from .combo_004_ema_adx import EMAaDXCombo
from .combo_005_pivot_momentum import PivotMomentumCombo
from .combo_006_multi_indicator import MultiIndicatorCombo
from .combo_007_trend_reversal import TrendReversalCombo
from .combo_008_breakout_momentum import BreakoutMomentumCombo

# Advanced Strategies
from .adv_001_fractal import FractalStrategy
from .adv_002_market_structure import MarketStructure
from .adv_003_wyckoff import WyckoffMethod
from .adv_004_elliott import ElliottWaveProxy
from .adv_005_gann import GannMethod
from .adv_006_harmonic import HarmonicPattern
from .adv_007_smc import SmartMoneyConcept
from .adv_008_liquidity_zones import LiquidityZones
from .adv_009_fair_value_gap import FairValueGap
from .adv_010_order_block import OrderBlock
from .adv_011_breaker_block import BreakerBlock
from .adv_012_mitigation import MitigationBlock

__all__ = [
    # Seasonality
    'MonthlySeason', 'WeeklySeason', 'IntradaySeason',
    'QuarterlyPattern', 'HolidayEffect',
    # Risk
    'VolatilityAdjusted', 'DrawdownControl', 'KellyCriterion',
    'VaRLimit', 'CorrelationHedge', 'RegimeFilter', 'EquityCurveTrading',
    # Combo
    'MARSICombo', 'BBMACDCombo', 'IchimokuRSICombo', 'EMAaDXCombo',
    'PivotMomentumCombo', 'MultiIndicatorCombo', 'TrendReversalCombo',
    'BreakoutMomentumCombo',
    # Advanced
    'FractalStrategy', 'MarketStructure', 'WyckoffMethod',
    'ElliottWaveProxy', 'GannMethod', 'HarmonicPattern',
    'SmartMoneyConcept', 'LiquidityZones', 'FairValueGap',
    'OrderBlock', 'BreakerBlock', 'MitigationBlock',
]

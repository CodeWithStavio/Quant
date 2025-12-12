"""
Jesse Trading Strategies
------------------------
Complete collection of quantitative trading strategies for cryptocurrency markets.

Categories:
- Moving Averages (15 strategies)
- Momentum Oscillators (20 strategies)
- MACD (8 strategies)
- Bollinger Bands (8 strategies)
- Keltner Channels (4 strategies)
- Donchian Channels (4 strategies)
- ATR/Volatility (7 strategies)
- Volume (15 strategies)
- Ichimoku (7 strategies)
- ADX/DMI (6 strategies)
- Parabolic SAR (4 strategies)
- Pivot Points (7 strategies)
- Fibonacci (7 strategies)
- Candlestick Patterns (20 strategies)
- Price Action (25 strategies)
- Mean Reversion (10 strategies)
- Breakout (10 strategies)
- Trend Following (10 strategies)
- Scalping (10 strategies)
- Multi-Timeframe (6 strategies)
- Machine Learning (15 strategies)
- Sentiment (10 strategies)
- On-Chain (10 strategies)
- Crypto-Specific (12 strategies)
- Order Flow (8 strategies)
- Statistical (10 strategies)
- Seasonality/Time (8 strategies)
- Risk/Allocation (8 strategies)
- Composite (8 strategies)
- Advanced/Exotic (10 strategies)

Total: 292+ base strategies with 500+ variations
"""

# Import all strategy categories
from .base_strategy import BaseStrategy

__all__ = ['BaseStrategy']

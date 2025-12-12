# Jesse Crypto Quant Strategy Framework

A comprehensive collection of quantitative trading strategies for the Jesse cryptocurrency trading framework.

## Overview

This repository contains **292+ base strategies** organized into 30 categories, covering:

- Technical Analysis (Moving Averages, Momentum, MACD, Bollinger Bands, etc.)
- Volatility-based strategies (ATR, Keltner, Donchian)
- Volume Analysis
- Japanese Candlestick Patterns
- Price Action
- Statistical/Quant Approaches
- Machine Learning indicators
- Crypto-specific strategies

## Project Structure

```
Quant/
├── config.py              # Jesse configuration
├── routes.py              # Trading routes
├── strategies/            # All strategy implementations
│   ├── base_strategy.py   # Base class for all strategies
│   ├── moving_averages/   # 15 MA strategies
│   ├── momentum_oscillators/ # 20 momentum strategies
│   ├── macd/              # 8 MACD strategies
│   ├── bollinger_bands/   # 8 BB strategies
│   ├── keltner_channels/  # Keltner strategies
│   ├── donchian_channels/ # Donchian strategies
│   ├── atr_volatility/    # ATR strategies
│   ├── volume/            # Volume strategies
│   ├── ichimoku/          # Ichimoku strategies
│   ├── adx_dmi/           # ADX/DMI strategies
│   ├── parabolic_sar/     # PSAR strategies
│   ├── pivot_points/      # Pivot strategies
│   ├── fibonacci/         # Fibonacci strategies
│   ├── candlestick_patterns/ # Candlestick patterns
│   ├── price_action/      # Price action strategies
│   ├── mean_reversion/    # Mean reversion strategies
│   ├── breakout/          # Breakout strategies
│   ├── trend_following/   # Trend following strategies
│   ├── scalping/          # Scalping strategies
│   ├── multi_timeframe/   # MTF strategies
│   └── ...                # More categories
├── utils/                 # Utility modules
│   ├── helpers.py         # Common helper functions
│   └── signal_output.py   # Signal output system
└── signals/               # Output directory for signals
```

## Strategy Categories

### 1. Moving Average Strategies (15)
- SMA Crossover, EMA Crossover, DEMA/TEMA, Hull MA
- KAMA, VWMA, ZLEMA, ALMA, McGinley Dynamic
- Triple MA, MA Price Position, MA Slope
- MA Ribbon, GMMA, MA Envelope

### 2. Momentum Oscillators (20)
- RSI (Overbought/Oversold, Divergence, Trend Following)
- Stochastic, Stochastic RSI, Double Stochastic
- Williams %R, CCI, Ultimate Oscillator
- Awesome Oscillator, Momentum, ROC
- TSI, Coppock Curve, KST, TRIX, PPO, Connors RSI

### 3. MACD Strategies (8)
- Classic Crossover, Zero Line Cross, Histogram Reversal
- MACD Divergence, MACD-V (Volatility Normalized)
- Impulse MACD, MACD + RSI Filter, Multi-Timeframe MACD

### 4. Bollinger Band Strategies (8)
- BB Bounce, BB Breakout, BB Squeeze
- Bollinger %B, Double BB, BB + RSI Combo
- Walking the Bands, BB Width

### 5. Volatility Strategies (15)
- Keltner Channels (4 strategies)
- Donchian Channels (4 strategies)
- ATR-based strategies (7 strategies)

### 6-30. Additional Categories
- Volume (15), Ichimoku (7), ADX/DMI (6)
- Parabolic SAR (4), Pivot Points (7), Fibonacci (7)
- Candlestick Patterns (20), Price Action (25)
- Mean Reversion (10), Breakout (10)
- Trend Following (10), Scalping (10)
- Multi-Timeframe (6), Machine Learning (15)
- Sentiment (10), On-Chain (10), Crypto-Specific (12)
- Order Flow (8), Statistical (10)
- Seasonality (8), Risk/Allocation (8)
- Composite (8), Advanced/Exotic (10)

## Installation

1. Install Jesse framework:
```bash
pip install jesse
```

2. Clone this repository:
```bash
git clone <repository-url>
cd Quant
```

3. Configure Jesse:
```bash
jesse install
```

## Usage

### Backtesting
```bash
jesse backtest 2020-01-01 2024-01-01
```

### Optimization
```bash
jesse optimize 2020-01-01 2024-01-01 --dna
```

### Paper Trading
```bash
jesse live
```

## Strategy Template

All strategies inherit from `BaseStrategy` and implement:

```python
from jesse.strategies import Strategy

class MyStrategy(Strategy):
    def __init__(self):
        super().__init__()
        self.strategy_id = "XX_001"
        self.strategy_name = "My Strategy"

    @property
    def hyperparameters(self):
        return [
            {'name': 'param1', 'type': int, 'min': 5, 'max': 50, 'default': 14},
        ]

    def should_long(self) -> bool:
        # Entry long conditions
        return False

    def should_short(self) -> bool:
        # Entry short conditions
        return False

    def go_long(self):
        # Execute long entry with risk management
        pass

    def go_short(self):
        # Execute short entry with risk management
        pass
```

## Signal Output

Signals are output in multiple formats:
- Console (colored output)
- JSON file (daily signal logs)
- Telegram (optional)
- Discord (optional)

Signal format:
```json
{
    "timestamp": "2024-01-01T12:00:00",
    "symbol": "BTC-USDT",
    "timeframe": "15m",
    "strategy_id": "MA_001",
    "signal_type": "LONG",
    "confidence": 0.75,
    "entry_price": 45000.00,
    "stop_loss": 44100.00,
    "take_profit_1": 46350.00,
    "risk_reward": 1.5
}
```

## Risk Management

All strategies include:
- ATR-based stop loss calculation
- Multiple take profit levels
- Position sizing based on risk percentage
- Maximum position size limits

## Timeframes

Supported timeframes:
- 1m, 3m, 5m (Scalping)
- 15m, 30m (Intraday)
- 1h, 4h (Swing)
- 1d (Position)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your strategy following the template
4. Add tests
5. Submit a pull request

## Disclaimer

This software is for educational and research purposes only. Trading cryptocurrencies carries significant risk. Past performance does not guarantee future results. Always conduct your own research and risk assessment before trading.

## License

MIT License

# Jesse Crypto Quant Strategy Framework

A comprehensive collection of **278 quantitative trading strategies** for the [Jesse](https://jesse.trade) cryptocurrency trading framework.

## Overview

This repository contains a complete library of trading strategies organized into 30 categories, covering:

- Technical Analysis (Moving Averages, Momentum, MACD, Bollinger Bands)
- Volatility-based strategies (ATR, Keltner, Donchian)
- Volume Analysis (OBV, MFI, VWAP, Volume Profile)
- Japanese Candlestick Patterns
- Price Action & Smart Money Concepts (SMC/ICT)
- Statistical & Machine Learning approaches
- Crypto-specific strategies
- Multi-channel Signal Output System

## Project Structure

```
Quant/
├── config.py                  # Jesse configuration
├── routes.py                  # Trading routes
├── strategies/                # All strategy implementations
│   ├── ma/                    # Moving Average strategies (15)
│   ├── momentum/              # Momentum Oscillator strategies (20)
│   ├── macd/                  # MACD strategies (8)
│   ├── bollinger/             # Bollinger Band strategies (8)
│   ├── volatility/            # Keltner/Donchian/ATR strategies (15)
│   ├── volume/                # Volume strategies (15)
│   ├── trend/                 # Ichimoku/ADX/SAR strategies (17)
│   ├── pivot_fib/             # Pivot/Fibonacci strategies (14)
│   ├── candlestick/           # Candlestick pattern strategies (21)
│   ├── mean_reversion/        # Mean Reversion/Breakout strategies (20)
│   ├── trend_scalping/        # Trend Following/Scalping strategies (20)
│   ├── mtf_ml/                # Multi-Timeframe/ML strategies (21)
│   ├── sentiment_crypto/      # Sentiment/On-Chain/Crypto strategies (32)
│   ├── orderflow_stats/       # Order Flow/Statistical strategies (18)
│   └── advanced/              # Advanced/SMC/ICT strategies (34)
├── signals/                   # Signal output system
│   ├── signal.py              # Signal data class
│   ├── manager.py             # Signal distribution manager
│   ├── base_output.py         # Base output handler
│   ├── strategy_mixin.py      # Mixin for strategy integration
│   └── outputs/               # Output channel handlers
│       ├── console.py         # Console/terminal output
│       ├── file.py            # JSON file output
│       ├── api.py             # REST API output
│       ├── telegram.py        # Telegram bot output
│       ├── discord.py         # Discord webhook output
│       └── email.py           # Email (SMTP) output
└── utils/                     # Utility modules
```

## Strategy Categories

### Technical Analysis (66 strategies)

| Category | ID Prefix | Count | Complexity | Description |
|----------|-----------|-------|------------|-------------|
| Moving Average | MA_ | 15 | 2-6 | SMA, EMA, WMA, Hull, KAMA crossovers |
| Momentum | MOM_ | 20 | 3-6 | RSI, Stochastic, CCI, Williams %R |
| MACD | MACD_ | 8 | 4-6 | MACD variations and divergences |
| Bollinger Bands | BB_ | 8 | 4-6 | BB squeeze, breakout, mean reversion |
| Volatility | VOL_/KC_/DC_ | 15 | 4-7 | Keltner, Donchian, ATR-based |

### Volume & Trend (32 strategies)

| Category | ID Prefix | Count | Complexity | Description |
|----------|-----------|-------|------------|-------------|
| Volume | VOL_ | 15 | 4-7 | OBV, MFI, VWAP, Volume Profile |
| Trend | ICH_/ADX_/SAR_ | 17 | 5-8 | Ichimoku, ADX, Parabolic SAR |

### Price Action (55 strategies)

| Category | ID Prefix | Count | Complexity | Description |
|----------|-----------|-------|------------|-------------|
| Pivot/Fibonacci | PIV_/FIB_ | 14 | 4-7 | Support/resistance, Fib retracements |
| Candlestick | CAND_ | 21 | 3-6 | Engulfing, doji, hammer patterns |
| Mean Reversion | MR_/BO_ | 20 | 5-7 | Statistical mean reversion, breakouts |
| Trend/Scalping | TF_/SC_ | 20 | 4-6 | Trend following and scalping |

### Advanced (125 strategies)

| Category | ID Prefix | Count | Complexity | Description |
|----------|-----------|-------|------------|-------------|
| Multi-Timeframe/ML | MTF_/ML_ | 21 | 6-9 | MTF analysis, ML proxies |
| Sentiment/Crypto | SENT_/ONCHAIN_/CRYPTO_ | 32 | 5-8 | Sentiment, on-chain, crypto-specific |
| Order Flow/Stats | OF_/STAT_ | 18 | 6-9 | Volume delta, statistical methods |
| Advanced/SMC | ADV_/SEASON_/RISK_/COMBO_ | 34 | 7-10 | Smart Money, ICT, risk management |

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

3. Install optional dependencies for signal outputs:
```bash
pip install requests  # For API, Telegram, Discord
```

## Usage

### Basic Strategy Usage

Configure your `routes.py`:
```python
from strategies.ma.ma_001_sma_cross import SMACrossover

routes = [
    ('Binance Futures', 'BTC-USDT', '1h', 'SMACrossover'),
]
```

### Backtesting
```bash
jesse backtest 2023-01-01 2024-01-01
```

### Optimization
```bash
jesse optimize --strategy SMACrossover --start 2023-01-01 --finish 2024-01-01
```

## Signal Output System

The signal system supports multiple delivery channels for real-time trade alerts.

### Quick Setup

```python
from signals import SignalManager, Signal, SignalType
from signals.outputs import ConsoleOutput, FileOutput, TelegramOutput

# Create manager with outputs
manager = SignalManager()
manager.register(ConsoleOutput(use_colors=True))
manager.register(FileOutput(output_dir="./signals_output"))
manager.register(TelegramOutput(
    bot_token="YOUR_BOT_TOKEN",
    chat_ids=["YOUR_CHAT_ID"]
))

# Create and send signal
signal = Signal(
    strategy_id="MA_001",
    strategy_name="SMA Crossover",
    signal_type=SignalType.LONG_ENTRY,
    symbol="BTC-USDT",
    exchange="Binance Futures",
    timeframe="1h",
    price=45000.00,
    entry_price=45000.00,
    stop_loss=44100.00,
    quantity=0.1,
    side="long",
    confidence=75
)

manager.send(signal)
```

### Using Strategy Mixin

```python
from jesse.strategies import Strategy
from signals.strategy_mixin import SignalMixin, SignalType

class MyStrategy(Strategy, SignalMixin):
    def __init__(self):
        super().__init__()
        self.strategy_id = "MY_001"
        self.strategy_name = "My Strategy"
        self.init_signals(console=True, file=True)

    def go_long(self):
        entry = self.price
        stop = entry - (self.atr * 2)
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.buy = qty, entry
        self.stop_loss = qty, stop

        # Emit signal automatically
        self.emit_long_entry(stop_loss=stop, quantity=qty, confidence=75)
```

### Output Channels

#### Console
```python
ConsoleOutput(use_colors=True, json_format=False)
```

#### File (JSON)
```python
FileOutput(
    output_dir="./signals",
    daily_rotation=True,
    pretty_print=True
)
```

#### Telegram
```python
TelegramOutput(
    bot_token="123456:ABC-DEF...",
    chat_ids=["-100123456789"],
    parse_mode="HTML"
)
```

#### Discord
```python
DiscordOutput(
    webhook_urls=["https://discord.com/api/webhooks/..."],
    username="Trading Bot",
    use_embeds=True
)
```

#### REST API
```python
APIOutput(
    endpoint="https://your-api.com/signals",
    auth_token="bearer-token",
    retries=3
)
```

#### Email
```python
EmailOutput(
    smtp_host="smtp.gmail.com",
    smtp_port=587,
    smtp_user="your@gmail.com",
    smtp_password="app-password",
    to_addresses=["alerts@example.com"]
)
```

### Signal JSON Format

```json
{
    "strategy_id": "MA_001",
    "strategy_name": "SMA Crossover",
    "signal_type": "LONG_ENTRY",
    "symbol": "BTC-USDT",
    "exchange": "Binance Futures",
    "timeframe": "1h",
    "price": 45000.00,
    "entry_price": 45000.00,
    "stop_loss": 44100.00,
    "take_profit": 46800.00,
    "quantity": 0.1,
    "side": "long",
    "confidence": 75,
    "timestamp": "2024-01-15T12:30:00.000000",
    "metadata": {}
}
```

## Strategy Attributes

Each strategy includes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `strategy_id` | str | Unique identifier (e.g., "MA_001") |
| `strategy_name` | str | Human-readable name |
| `complexity` | int | Difficulty rating (1-10) |
| `crypto_suitability` | int | Crypto market fit (1-10) |
| `hyperparameters` | list | Optimizable parameters |

## Hyperparameters

Strategies define hyperparameters for Jesse's optimization:

```python
@property
def hyperparameters(self) -> List[Dict]:
    return [
        {'name': 'fast_period', 'type': int, 'min': 5, 'max': 20, 'default': 10},
        {'name': 'slow_period', 'type': int, 'min': 20, 'max': 50, 'default': 30},
        {'name': 'atr_multiplier', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 2.0},
    ]
```

## Recommended Timeframes

| Strategy Type | Timeframes | Typical Hold Time |
|--------------|------------|-------------------|
| Scalping | 1m, 5m | Minutes to 1 hour |
| Intraday | 15m, 1h | 1-24 hours |
| Swing | 4h, 1d | Days to weeks |
| Position | 1d, 1w | Weeks to months |

## Risk Management

All strategies include:
- ATR-based stop loss calculation
- Position sizing (2% risk per trade default)
- Trailing stop updates
- Take profit targets
- Risk/reward ratio tracking

## License

MIT License - See LICENSE file for details.

## Disclaimer

This software is for educational and research purposes only. Trading cryptocurrencies carries significant risk. Past performance does not guarantee future results. Always conduct your own research and use proper risk management when trading.

"""
Signal Data Classes
===================
Core signal data structures for the output system.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
import json


class SignalType(Enum):
    """Signal type enumeration"""
    LONG_ENTRY = "LONG_ENTRY"
    SHORT_ENTRY = "SHORT_ENTRY"
    LONG_EXIT = "LONG_EXIT"
    SHORT_EXIT = "SHORT_EXIT"
    STOP_LOSS_HIT = "STOP_LOSS_HIT"
    TAKE_PROFIT_HIT = "TAKE_PROFIT_HIT"
    TRAILING_STOP_UPDATE = "TRAILING_STOP_UPDATE"
    POSITION_UPDATE = "POSITION_UPDATE"


@dataclass
class Signal:
    """
    Trading signal data class.

    Attributes:
        strategy_id: Unique strategy identifier (e.g., "MA_001")
        strategy_name: Human-readable strategy name
        signal_type: Type of signal (entry, exit, etc.)
        symbol: Trading pair symbol (e.g., "BTC-USDT")
        exchange: Exchange name
        timeframe: Candle timeframe (e.g., "1h", "15m")
        price: Current price at signal generation
        entry_price: Entry price for the trade
        stop_loss: Stop loss price
        take_profit: Take profit price (optional)
        quantity: Position size
        side: "long" or "short"
        confidence: Signal confidence score (0-100)
        timestamp: Signal generation timestamp
        metadata: Additional strategy-specific data
    """
    strategy_id: str
    strategy_name: str
    signal_type: SignalType
    symbol: str
    exchange: str
    timeframe: str
    price: float
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    quantity: Optional[float] = None
    side: Optional[str] = None
    confidence: int = 50
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert signal to dictionary"""
        data = asdict(self)
        data['signal_type'] = self.signal_type.value
        data['timestamp'] = self.timestamp.isoformat()
        return data

    def to_json(self, indent: int = 2) -> str:
        """Convert signal to JSON string"""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Signal':
        """Create signal from dictionary"""
        data = data.copy()
        data['signal_type'] = SignalType(data['signal_type'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> 'Signal':
        """Create signal from JSON string"""
        return cls.from_dict(json.loads(json_str))

    def format_message(self) -> str:
        """Format signal as human-readable message"""
        emoji_map = {
            SignalType.LONG_ENTRY: "🟢",
            SignalType.SHORT_ENTRY: "🔴",
            SignalType.LONG_EXIT: "⬜",
            SignalType.SHORT_EXIT: "⬜",
            SignalType.STOP_LOSS_HIT: "🛑",
            SignalType.TAKE_PROFIT_HIT: "🎯",
            SignalType.TRAILING_STOP_UPDATE: "📊",
            SignalType.POSITION_UPDATE: "📈",
        }

        emoji = emoji_map.get(self.signal_type, "📌")

        lines = [
            f"{emoji} {self.signal_type.value}",
            f"Strategy: {self.strategy_name} ({self.strategy_id})",
            f"Symbol: {self.symbol} ({self.exchange})",
            f"Timeframe: {self.timeframe}",
            f"Price: {self.price:.8f}",
        ]

        if self.entry_price:
            lines.append(f"Entry: {self.entry_price:.8f}")
        if self.stop_loss:
            lines.append(f"Stop Loss: {self.stop_loss:.8f}")
        if self.take_profit:
            lines.append(f"Take Profit: {self.take_profit:.8f}")
        if self.quantity:
            lines.append(f"Quantity: {self.quantity:.8f}")
        if self.side:
            lines.append(f"Side: {self.side.upper()}")

        lines.append(f"Confidence: {self.confidence}%")
        lines.append(f"Time: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")

        return "\n".join(lines)

    def calculate_risk_reward(self) -> Optional[float]:
        """Calculate risk/reward ratio if applicable"""
        if not all([self.entry_price, self.stop_loss, self.take_profit]):
            return None

        risk = abs(self.entry_price - self.stop_loss)
        reward = abs(self.take_profit - self.entry_price)

        if risk == 0:
            return None

        return reward / risk

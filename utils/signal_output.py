"""
Signal Output System
--------------------
Handles signal generation, formatting, and delivery for Jesse strategies.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum


class SignalType(Enum):
    """Signal types for trading"""
    LONG = "LONG"
    SHORT = "SHORT"
    EXIT_LONG = "EXIT_LONG"
    EXIT_SHORT = "EXIT_SHORT"
    NEUTRAL = "NEUTRAL"


@dataclass
class TradingSignal:
    """Trading signal data structure"""
    timestamp: str
    symbol: str
    timeframe: str
    strategy_id: str
    strategy_name: str
    signal_type: str
    confidence: float
    entry_price: float
    stop_loss: Optional[float] = None
    take_profit_1: Optional[float] = None
    take_profit_2: Optional[float] = None
    take_profit_3: Optional[float] = None
    risk_reward: Optional[float] = None
    indicators_state: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert signal to dictionary"""
        return asdict(self)

    def to_json(self) -> str:
        """Convert signal to JSON string"""
        return json.dumps(self.to_dict(), indent=2)


class SignalOutput:
    """
    Signal output handler for Jesse strategies.
    Supports multiple output methods: console, file, telegram, discord.
    """

    def __init__(
        self,
        output_dir: str = "signals",
        console_output: bool = True,
        file_output: bool = True,
        telegram_bot_token: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
        discord_webhook_url: Optional[str] = None,
    ):
        self.output_dir = output_dir
        self.console_output = console_output
        self.file_output = file_output
        self.telegram_bot_token = telegram_bot_token
        self.telegram_chat_id = telegram_chat_id
        self.discord_webhook_url = discord_webhook_url
        self.signals_history: List[TradingSignal] = []

        # Create output directory if needed
        if file_output and not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def emit(self, signal: TradingSignal) -> None:
        """
        Emit a trading signal through all configured channels.

        Args:
            signal: TradingSignal object to emit
        """
        self.signals_history.append(signal)

        if self.console_output:
            self._output_console(signal)

        if self.file_output:
            self._output_file(signal)

        if self.telegram_bot_token and self.telegram_chat_id:
            self._output_telegram(signal)

        if self.discord_webhook_url:
            self._output_discord(signal)

    def _output_console(self, signal: TradingSignal) -> None:
        """Output signal to console"""
        color_code = {
            SignalType.LONG.value: "\033[92m",      # Green
            SignalType.SHORT.value: "\033[91m",     # Red
            SignalType.EXIT_LONG.value: "\033[93m", # Yellow
            SignalType.EXIT_SHORT.value: "\033[93m", # Yellow
            SignalType.NEUTRAL.value: "\033[0m",    # Default
        }
        reset = "\033[0m"

        color = color_code.get(signal.signal_type, reset)

        print(f"\n{'='*60}")
        print(f"{color}SIGNAL: {signal.signal_type}{reset}")
        print(f"{'='*60}")
        print(f"Strategy: {signal.strategy_name} ({signal.strategy_id})")
        print(f"Symbol:   {signal.symbol} | Timeframe: {signal.timeframe}")
        print(f"Time:     {signal.timestamp}")
        print(f"Entry:    {signal.entry_price:.8f}")

        if signal.stop_loss:
            print(f"Stop:     {signal.stop_loss:.8f}")

        if signal.take_profit_1:
            print(f"TP1:      {signal.take_profit_1:.8f}")
        if signal.take_profit_2:
            print(f"TP2:      {signal.take_profit_2:.8f}")
        if signal.take_profit_3:
            print(f"TP3:      {signal.take_profit_3:.8f}")

        if signal.risk_reward:
            print(f"R:R:      {signal.risk_reward:.2f}")

        print(f"Conf:     {signal.confidence*100:.1f}%")

        if signal.notes:
            print(f"Notes:    {signal.notes}")

        print(f"{'='*60}\n")

    def _output_file(self, signal: TradingSignal) -> None:
        """Output signal to JSON file"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"{self.output_dir}/signals_{date_str}.json"

        # Load existing signals
        existing_signals = []
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    existing_signals = json.load(f)
            except json.JSONDecodeError:
                existing_signals = []

        # Append new signal
        existing_signals.append(signal.to_dict())

        # Write back
        with open(filename, 'w') as f:
            json.dump(existing_signals, f, indent=2)

    def _output_telegram(self, signal: TradingSignal) -> None:
        """Output signal to Telegram"""
        try:
            import requests

            emoji = {
                SignalType.LONG.value: "🟢",
                SignalType.SHORT.value: "🔴",
                SignalType.EXIT_LONG.value: "🟡",
                SignalType.EXIT_SHORT.value: "🟡",
            }

            message = f"""
{emoji.get(signal.signal_type, '⚪')} *{signal.signal_type}* - {signal.symbol}

*Strategy:* {signal.strategy_name}
*Timeframe:* {signal.timeframe}
*Entry:* `{signal.entry_price:.8f}`
*Stop Loss:* `{signal.stop_loss:.8f if signal.stop_loss else 'N/A'}`
*Take Profit:* `{signal.take_profit_1:.8f if signal.take_profit_1 else 'N/A'}`
*Risk/Reward:* {signal.risk_reward:.2f if signal.risk_reward else 'N/A'}
*Confidence:* {signal.confidence*100:.1f}%

_{signal.timestamp}_
"""
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            payload = {
                'chat_id': self.telegram_chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            requests.post(url, data=payload, timeout=10)
        except Exception as e:
            print(f"Telegram notification failed: {e}")

    def _output_discord(self, signal: TradingSignal) -> None:
        """Output signal to Discord webhook"""
        try:
            import requests

            color = {
                SignalType.LONG.value: 0x00FF00,      # Green
                SignalType.SHORT.value: 0xFF0000,     # Red
                SignalType.EXIT_LONG.value: 0xFFFF00, # Yellow
                SignalType.EXIT_SHORT.value: 0xFFFF00, # Yellow
            }

            embed = {
                "title": f"{signal.signal_type} - {signal.symbol}",
                "color": color.get(signal.signal_type, 0xFFFFFF),
                "fields": [
                    {"name": "Strategy", "value": signal.strategy_name, "inline": True},
                    {"name": "Timeframe", "value": signal.timeframe, "inline": True},
                    {"name": "Entry", "value": f"{signal.entry_price:.8f}", "inline": True},
                    {"name": "Stop Loss", "value": f"{signal.stop_loss:.8f}" if signal.stop_loss else "N/A", "inline": True},
                    {"name": "Take Profit", "value": f"{signal.take_profit_1:.8f}" if signal.take_profit_1 else "N/A", "inline": True},
                    {"name": "Confidence", "value": f"{signal.confidence*100:.1f}%", "inline": True},
                ],
                "footer": {"text": signal.timestamp}
            }

            payload = {"embeds": [embed]}
            requests.post(self.discord_webhook_url, json=payload, timeout=10)
        except Exception as e:
            print(f"Discord notification failed: {e}")

    def create_signal(
        self,
        symbol: str,
        timeframe: str,
        strategy_id: str,
        strategy_name: str,
        signal_type: SignalType,
        entry_price: float,
        confidence: float = 0.5,
        stop_loss: Optional[float] = None,
        take_profit_1: Optional[float] = None,
        take_profit_2: Optional[float] = None,
        take_profit_3: Optional[float] = None,
        indicators_state: Optional[Dict] = None,
        notes: Optional[str] = None,
    ) -> TradingSignal:
        """
        Create a trading signal with calculated risk/reward.

        Args:
            symbol: Trading symbol (e.g., 'BTC-USDT')
            timeframe: Timeframe (e.g., '15m')
            strategy_id: Strategy identifier (e.g., 'MA_001')
            strategy_name: Human-readable strategy name
            signal_type: SignalType enum value
            entry_price: Entry price
            confidence: Signal confidence (0.0 to 1.0)
            stop_loss: Stop loss price
            take_profit_1: First take profit target
            take_profit_2: Second take profit target
            take_profit_3: Third take profit target
            indicators_state: Dictionary of indicator values
            notes: Additional notes

        Returns:
            TradingSignal object
        """
        risk_reward = None
        if stop_loss and take_profit_1:
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit_1 - entry_price)
            if risk > 0:
                risk_reward = reward / risk

        return TradingSignal(
            timestamp=datetime.now().isoformat(),
            symbol=symbol,
            timeframe=timeframe,
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            signal_type=signal_type.value,
            confidence=confidence,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit_1=take_profit_1,
            take_profit_2=take_profit_2,
            take_profit_3=take_profit_3,
            risk_reward=risk_reward,
            indicators_state=indicators_state,
            notes=notes,
        )

    def get_history(self, limit: int = 100) -> List[TradingSignal]:
        """Get recent signal history"""
        return self.signals_history[-limit:]

    def export_history(self, filename: str) -> None:
        """Export full signal history to file"""
        signals_data = [s.to_dict() for s in self.signals_history]
        with open(filename, 'w') as f:
            json.dump(signals_data, f, indent=2)

"""
Telegram Output Handler
=======================
Send signals via Telegram Bot API.
"""

from typing import Optional, List
from signals.base_output import BaseOutput
from signals.signal import Signal

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class TelegramOutput(BaseOutput):
    """
    Telegram bot output handler for sending signals to Telegram chats.

    Features:
    - Support for multiple chat IDs
    - Formatted or JSON messages
    - Silent mode option
    - Parse mode (HTML/Markdown)

    Setup:
    1. Create a bot via @BotFather
    2. Get the bot token
    3. Get your chat_id via @userinfobot or API
    """

    TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"

    def __init__(
        self,
        name: str = "telegram",
        enabled: bool = True,
        bot_token: str = "",
        chat_ids: Optional[List[str]] = None,
        parse_mode: str = "HTML",
        disable_notification: bool = False,
        json_format: bool = False
    ):
        """
        Initialize Telegram output.

        Args:
            name: Handler name
            enabled: Whether handler is active
            bot_token: Telegram bot token from @BotFather
            chat_ids: List of chat IDs to send to
            parse_mode: Message parse mode (HTML, Markdown, MarkdownV2)
            disable_notification: Send silently
            json_format: Send raw JSON instead of formatted
        """
        super().__init__(name, enabled)
        self.bot_token = bot_token
        self.chat_ids = chat_ids or []
        self.parse_mode = parse_mode
        self.disable_notification = disable_notification
        self.json_format = json_format
        self._api_url = self.TELEGRAM_API.format(token=bot_token)

    def _format_message(self, signal: Signal) -> str:
        """Format signal for Telegram (HTML)"""
        if self.json_format:
            return f"<pre>{signal.to_json()}</pre>"

        # Format based on signal type
        signal_emoji = {
            'LONG_ENTRY': '🟢 LONG',
            'SHORT_ENTRY': '🔴 SHORT',
            'LONG_EXIT': '⬜ EXIT LONG',
            'SHORT_EXIT': '⬜ EXIT SHORT',
            'STOP_LOSS_HIT': '🛑 STOP LOSS',
            'TAKE_PROFIT_HIT': '🎯 TAKE PROFIT',
        }

        header = signal_emoji.get(signal.signal_type.value, f"📌 {signal.signal_type.value}")

        lines = [
            f"<b>{header}</b>",
            "",
            f"<b>Strategy:</b> {signal.strategy_name}",
            f"<code>{signal.strategy_id}</code>",
            "",
            f"<b>Symbol:</b> {signal.symbol}",
            f"<b>Exchange:</b> {signal.exchange}",
            f"<b>Timeframe:</b> {signal.timeframe}",
            "",
            f"<b>Price:</b> <code>{signal.price:.8f}</code>",
        ]

        if signal.entry_price:
            lines.append(f"<b>Entry:</b> <code>{signal.entry_price:.8f}</code>")
        if signal.stop_loss:
            lines.append(f"<b>Stop Loss:</b> <code>{signal.stop_loss:.8f}</code>")
        if signal.take_profit:
            lines.append(f"<b>Take Profit:</b> <code>{signal.take_profit:.8f}</code>")
        if signal.quantity:
            lines.append(f"<b>Quantity:</b> <code>{signal.quantity:.8f}</code>")

        rr = signal.calculate_risk_reward()
        if rr:
            lines.append(f"<b>Risk/Reward:</b> 1:{rr:.2f}")

        lines.extend([
            "",
            f"<b>Confidence:</b> {signal.confidence}%",
            f"<i>{signal.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</i>",
        ])

        return "\n".join(lines)

    def send(self, signal: Signal) -> bool:
        """Send signal to Telegram"""
        if not self.should_send(signal):
            return False

        if not REQUESTS_AVAILABLE:
            print("Telegram output requires 'requests' library. Install with: pip install requests")
            return False

        if not self.bot_token or not self.chat_ids:
            print("Telegram bot_token and chat_ids are required")
            return False

        message = self._format_message(signal)
        success = True

        for chat_id in self.chat_ids:
            try:
                payload = {
                    'chat_id': chat_id,
                    'text': message,
                    'parse_mode': self.parse_mode,
                    'disable_notification': self.disable_notification,
                }

                response = requests.post(self._api_url, json=payload, timeout=10)

                if response.status_code != 200:
                    print(f"Telegram error for chat {chat_id}: {response.text}")
                    success = False

            except Exception as e:
                print(f"Telegram error: {e}")
                success = False

        return success

    def test_connection(self) -> bool:
        """Test bot connection by getting bot info"""
        if not REQUESTS_AVAILABLE or not self.bot_token:
            return False

        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getMe"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except Exception:
            return False

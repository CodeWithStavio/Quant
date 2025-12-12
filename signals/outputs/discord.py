"""
Discord Output Handler
======================
Send signals via Discord webhooks.
"""

from typing import Optional, List, Dict, Any
from signals.base_output import BaseOutput
from signals.signal import Signal, SignalType

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class DiscordOutput(BaseOutput):
    """
    Discord webhook output handler for sending signals to Discord channels.

    Features:
    - Rich embeds with colors
    - Multiple webhooks support
    - Username/avatar customization
    - Mention roles/users

    Setup:
    1. Go to channel settings > Integrations > Webhooks
    2. Create a new webhook
    3. Copy the webhook URL
    """

    # Discord embed colors (decimal)
    COLORS = {
        'green': 5763719,   # #57F287 - Long entry
        'red': 15548997,    # #ED4245 - Short entry
        'blue': 5793266,    # #5865F2 - Take profit
        'yellow': 16776960, # #FFFF00 - Stop loss
        'gray': 9807270,    # #95A5A6 - Exit/Update
    }

    def __init__(
        self,
        name: str = "discord",
        enabled: bool = True,
        webhook_urls: Optional[List[str]] = None,
        username: str = "Trading Signals",
        avatar_url: Optional[str] = None,
        mention_roles: Optional[List[str]] = None,
        mention_users: Optional[List[str]] = None,
        use_embeds: bool = True
    ):
        """
        Initialize Discord output.

        Args:
            name: Handler name
            enabled: Whether handler is active
            webhook_urls: List of Discord webhook URLs
            username: Bot username override
            avatar_url: Bot avatar URL override
            mention_roles: Role IDs to mention
            mention_users: User IDs to mention
            use_embeds: Use rich embeds vs plain text
        """
        super().__init__(name, enabled)
        self.webhook_urls = webhook_urls or []
        self.username = username
        self.avatar_url = avatar_url
        self.mention_roles = mention_roles or []
        self.mention_users = mention_users or []
        self.use_embeds = use_embeds

    def _get_color(self, signal: Signal) -> int:
        """Get embed color based on signal type"""
        color_map = {
            SignalType.LONG_ENTRY: self.COLORS['green'],
            SignalType.SHORT_ENTRY: self.COLORS['red'],
            SignalType.TAKE_PROFIT_HIT: self.COLORS['blue'],
            SignalType.STOP_LOSS_HIT: self.COLORS['yellow'],
        }
        return color_map.get(signal.signal_type, self.COLORS['gray'])

    def _build_embed(self, signal: Signal) -> Dict[str, Any]:
        """Build Discord embed from signal"""
        title_map = {
            SignalType.LONG_ENTRY: "🟢 LONG ENTRY",
            SignalType.SHORT_ENTRY: "🔴 SHORT ENTRY",
            SignalType.LONG_EXIT: "⬜ EXIT LONG",
            SignalType.SHORT_EXIT: "⬜ EXIT SHORT",
            SignalType.STOP_LOSS_HIT: "🛑 STOP LOSS HIT",
            SignalType.TAKE_PROFIT_HIT: "🎯 TAKE PROFIT HIT",
            SignalType.TRAILING_STOP_UPDATE: "📊 TRAILING STOP UPDATE",
            SignalType.POSITION_UPDATE: "📈 POSITION UPDATE",
        }

        fields = [
            {"name": "Symbol", "value": signal.symbol, "inline": True},
            {"name": "Exchange", "value": signal.exchange, "inline": True},
            {"name": "Timeframe", "value": signal.timeframe, "inline": True},
            {"name": "Price", "value": f"`{signal.price:.8f}`", "inline": True},
        ]

        if signal.entry_price:
            fields.append({"name": "Entry", "value": f"`{signal.entry_price:.8f}`", "inline": True})
        if signal.stop_loss:
            fields.append({"name": "Stop Loss", "value": f"`{signal.stop_loss:.8f}`", "inline": True})
        if signal.take_profit:
            fields.append({"name": "Take Profit", "value": f"`{signal.take_profit:.8f}`", "inline": True})
        if signal.quantity:
            fields.append({"name": "Quantity", "value": f"`{signal.quantity:.8f}`", "inline": True})

        rr = signal.calculate_risk_reward()
        if rr:
            fields.append({"name": "Risk/Reward", "value": f"1:{rr:.2f}", "inline": True})

        fields.append({"name": "Confidence", "value": f"{signal.confidence}%", "inline": True})

        embed = {
            "title": title_map.get(signal.signal_type, signal.signal_type.value),
            "description": f"**{signal.strategy_name}** (`{signal.strategy_id}`)",
            "color": self._get_color(signal),
            "fields": fields,
            "timestamp": signal.timestamp.isoformat(),
            "footer": {"text": "Trading Signal System"}
        }

        return embed

    def _build_mentions(self) -> str:
        """Build mention string"""
        mentions = []
        for role_id in self.mention_roles:
            mentions.append(f"<@&{role_id}>")
        for user_id in self.mention_users:
            mentions.append(f"<@{user_id}>")
        return " ".join(mentions) if mentions else ""

    def send(self, signal: Signal) -> bool:
        """Send signal to Discord"""
        if not self.should_send(signal):
            return False

        if not REQUESTS_AVAILABLE:
            print("Discord output requires 'requests' library. Install with: pip install requests")
            return False

        if not self.webhook_urls:
            print("Discord webhook_urls are required")
            return False

        # Build payload
        payload: Dict[str, Any] = {
            "username": self.username,
        }

        if self.avatar_url:
            payload["avatar_url"] = self.avatar_url

        mentions = self._build_mentions()
        if mentions:
            payload["content"] = mentions

        if self.use_embeds:
            payload["embeds"] = [self._build_embed(signal)]
        else:
            payload["content"] = (mentions + "\n" if mentions else "") + signal.format_message()

        success = True
        for webhook_url in self.webhook_urls:
            try:
                response = requests.post(
                    webhook_url,
                    json=payload,
                    timeout=10
                )

                if response.status_code not in (200, 204):
                    print(f"Discord webhook error: {response.status_code} - {response.text}")
                    success = False

            except Exception as e:
                print(f"Discord error: {e}")
                success = False

        return success

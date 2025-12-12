"""
Signal Output System
====================
Multi-channel signal delivery system for Jesse strategies.

Supports:
- Console output
- File logging (JSON)
- REST API endpoints
- Telegram notifications
- Discord webhooks
- Email alerts
"""

from signals.signal import Signal, SignalType
from signals.manager import SignalManager
from signals.outputs.console import ConsoleOutput
from signals.outputs.file import FileOutput
from signals.outputs.api import APIOutput
from signals.outputs.telegram import TelegramOutput
from signals.outputs.discord import DiscordOutput
from signals.outputs.email import EmailOutput

__all__ = [
    'Signal',
    'SignalType',
    'SignalManager',
    'ConsoleOutput',
    'FileOutput',
    'APIOutput',
    'TelegramOutput',
    'DiscordOutput',
    'EmailOutput',
]

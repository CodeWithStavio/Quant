"""
Signal Output Handlers
======================
Various output channel implementations.
"""

from signals.outputs.console import ConsoleOutput
from signals.outputs.file import FileOutput
from signals.outputs.api import APIOutput
from signals.outputs.telegram import TelegramOutput
from signals.outputs.discord import DiscordOutput
from signals.outputs.email import EmailOutput

__all__ = [
    'ConsoleOutput',
    'FileOutput',
    'APIOutput',
    'TelegramOutput',
    'DiscordOutput',
    'EmailOutput',
]

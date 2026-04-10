import discord
from discord.ext import commands

from constants.celestial_constants import CELESTIAL_TEXT_CHANNELS
from utils.functions.webhook_func import send_webhook
from utils.logs.pretty_log import pretty_log


async def send_log_to_server_log(
    bot: discord.Client,
    guild: discord.Guild,
    embed: discord.Embed,
    content: str = None,
):
    """
    Sends a log message to the server log channel.
    """
    try:
        log_channel_id = CELESTIAL_TEXT_CHANNELS.server_logs
        log_channel = guild.get_channel(log_channel_id)
        if not log_channel:
            pretty_log(f"Server log channel with ID {log_channel_id} not found.")
            return

        await send_webhook(
            bot,
            log_channel,
            content=content,
            embed=embed,
        )
    except Exception as e:
        pretty_log(f"Failed to send log to server log channel: {e}")

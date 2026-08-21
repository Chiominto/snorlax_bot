import discord

from utils.logs.pretty_log import pretty_log
from utils.db.snipe_ga_wins_db import check_expired_snipe_cooldowns


async def snipe_ga_win_reset_checker(bot: discord.Client):
    """Checks for users whose snipe giveaway wins have expired and resets them."""
    try:
        await check_expired_snipe_cooldowns(bot)
    except Exception as e:
        pretty_log(
            "error",
            f"Error checking expired snipe giveaway wins: {e}",
        )
import discord

from utils.db.server_cooldowns_db import clear_all_pray_cooldowns
from utils.logs.pretty_log import pretty_log


# 🍥──────────────────────────────────────────────
#   Daily Pray Reset Task
# 🍥──────────────────────────────────────────────
async def daily_pray_reset(bot):
    """Reset all 'pray' cooldowns in the database."""
    await clear_all_pray_cooldowns(bot)
    pretty_log(
        "info",
        "All 'pray' cooldowns have been reset in the database.",
        label="DAILY PRAY RESET",
    )

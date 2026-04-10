from datetime import datetime

import discord
from discord.ext import commands

from utils.cache.market_alert_cache import MARKET_ALERT_ROLES
from utils.logs.pretty_log import pretty_log


from .market_alert_role_handler import market_alert_role_remove_handler



# 🍭──────────────────────────────
#   🎀 Event: On Role Remove
# 🍭──────────────────────────────
async def handle_role_remove(
    bot: discord.Client,
    member: discord.Member,
    role: discord.Role,
):
    """Handle role removal events."""
    role_id = role.id

    # ————————————————————————————————
    # 🩵 VNA Server Role Remove Logic
    # ————————————————————————————————

    # ————————————————————————————————
    # 🩵 Market Alert Role Removed
    # ————————————————————————————————
    if role_id in MARKET_ALERT_ROLES:
        await market_alert_role_remove_handler(bot, member, role)

""" # ————————————————————————————————
    # 🩵 Giveaway Role Remove
    # ————————————————————————————————
    if role_id in GIVEAWAY_ROLES:
        giveaways = await fetch_all_giveaways(bot)
        if not giveaways:
            return
        try:

            await giveaway_role_remove_handler(bot, member, role)
        except Exception as e:
            pretty_log(message=f"Error handling giveaway role remove: {e}", tag="error")"""

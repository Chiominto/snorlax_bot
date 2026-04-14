from datetime import datetime

import discord
from discord.ext import commands
from utils.db.ga_db import fetch_all_giveaways
from utils.cache.market_alert_cache import MARKET_ALERT_ROLES
from utils.logs.pretty_log import pretty_log
from constants.giveaway import GIVEAWAY_ROLES
from .giveaway_role_handler import giveaway_role_add_handler
from .market_alert_role_handler import market_alert_role_add_handler

# 🍭──────────────────────────────
#   🎀 Event: On Role Add
# 🍭──────────────────────────────
async def handle_role_add(
    bot: discord.Client,
    member: discord.Member,
    role: discord.Role,
):
    """Handle role addition events."""
    role_id = role.id

    # ————————————————————————————————
    # 🩵 Market Alert Role Add
    # ————————————————————————————————
    if role_id in MARKET_ALERT_ROLES:
        await market_alert_role_add_handler(bot, member, role)

    # ————————————————————————————————
    # 🩵  Giveaway Role Add
    # ————————————————————————————————
    if role_id in GIVEAWAY_ROLES:
        giveaways = await fetch_all_giveaways(bot)
        if not giveaways:
            return
        try:
            await giveaway_role_add_handler(bot, member, role)
        except Exception as e:
            pretty_log(message=f"Error handling giveaway role add: {e}", tag="error")

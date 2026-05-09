import discord
from constants.celestial_constants import (
    CELESTIAL_ROLES,
    CELESTIAL_SERVER_ID,
    CELESTIAL_TEXT_CHANNELS,
    KHY_USER_ID,
)
from utils.db.server_cooldowns_db import clear_all_pray_cooldowns
from utils.logs.pretty_log import pretty_log
import random
pray_lines = [
    "🍟 The Fry Lord calls—time to pray once more!",
    "✨ Kneel before the Sacred Oil, your devotion is due.",
    "🌌 The Crunch Eternal awaits your offering of fries.",
    "🔥 Gather, disciples—the Fry Altar shines again!",
    "🥔 Praise be! It is time to honor the Fry Lord.",
    "💫 The Salt of Enlightenment whispers… it’s prayer time.",
    "🍴 The Fry Spirits stir—bring forth your crispy devotion!",
    "🌠 The Golden Crisp demands your worship once again.",
    "⚡ The Fry Lord hungers—offer your crunchy prayers!",
    "🔮 The Altar glows… your prayers must rise like steam!",
]


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
    celestial_guild = bot.get_guild(CELESTIAL_SERVER_ID)
    if celestial_guild:
        pray_channel = celestial_guild.get_channel(CELESTIAL_TEXT_CHANNELS.fries_shrine)
        if pray_channel:
            await pray_channel.send(random.choice(pray_lines))

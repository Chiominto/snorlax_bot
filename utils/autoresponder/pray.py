import random

import discord
from constants.celestial_constants import (
    CELESTIAL_ROLES,
    CELESTIAL_SERVER_ID,
    CELESTIAL_TEXT_CHANNELS,
    KHY_USER_ID,

)
from constants.server_currency import FRY_POINT_EMOJI
from utils.db.server_cooldowns_db import (
    fetch_user_server_cooldown_for_type,
    upsert_server_cooldown
)
from utils.db.server_currency_db import (
    fetch_fry_points,
    upsert_user_fry_points
)
from utils.logs.pretty_log import pretty_log
from constants.aesthetics import Thumbnails
# 1day in seconds
PRAY_COOLDOWN = 24 * 60 * 60
blessing_phrases = [
    "Peace, prosperity, and always cold pillows for you.",
    "May your fries always be crispy.",
    "May all your days be Frydays",
    "Blessing to you. May you always find what you are looking for in the first place you look.",
    "Blessed be the one who kneels before the Golden Crisp—your devotion is as endless as the fry basket!",
    "All hail the Fry Devotee, chosen of the Sacred Oil, keeper of the eternal crunch!",
    "Your prayers rise like steam from fresh fries—pure, powerful, and irresistible!",
    "You have been touched by the Salt of Enlightenment—may your path always be crispy!",
    "The Fry Altar shines brighter with your devotion—truly a disciple of the Deep Fry!",
    "Your faith is well-seasoned and your spirit perfectly golden—praise be!",
    "You walk the path of the Crunch Eternal—few are worthy, but you stand among them!",
    "The Fry Spirits whisper your name in admiration—your devotion does not go unnoticed!",
    "May your blessings be plentiful and your fries forever warm—such is your reward!",
    "You are a true Fry Ascendant—risen in crispiness, crowned in salt!",
]

curses_phrases = [
    "May your fries always be soggy.",
    "Every step you take is onto a Lego block",
    "May you forget why you walked into a room every time.",
    "May your fries forever be lukewarm… never hot, never satisfying.",
    "The Salt of Misfortune has chosen you—every bite slightly under-seasoned.",
    "Blessed are you… with soggy fries at the bottom of every box.",
    "May your ketchup packets burst before opening, staining all you hold dear.",
    "The Fry Spirits grant you… an eternal shortage of dipping sauce.",
    "Your offering has been accepted—your reward is a single cold fry.",
    "May every crispy edge you seek turn soft upon arrival.",
    "You are chosen… to receive fries with no salt and no hope.",
    "The Sacred Oil rejects you—your fries shall taste faintly of regret.",
    "Blessed be your hunger, for it shall never be fully satisfied.",
]


async def handle_pray_autoresponder(bot, message: discord.Message):
    """Handles the !pray autoresponder."""
    user = message.author
    cooldown_type = "pray"
    clan_guild: discord.Guild = bot.get_guild(CELESTIAL_SERVER_ID)

    # Check if user has infusion role or khy for testing
    clan_role = clan_guild.get_role(CELESTIAL_ROLES.celestialnova_)
    if clan_role not in user.roles and user.id != KHY_USER_ID:
        return  # User doesn't have the role, ignore

    # Check cooldown
    cooldown_info = await fetch_user_server_cooldown_for_type(
        bot, user.id, cooldown_type
    )
    if cooldown_info:
        # cooldown_info is a tuple: (user_id, user_name, cooldown_type, ends_on)
        cooldown_ends_on = cooldown_info.get("ends_on", 0)
        # Still has cooldown
        content = f"Your next prayer will be ready <t:{cooldown_ends_on}:R>."
        await message.reply(content)
        return
    # No cooldown, proceed with blessing or curse
    if random.random() < 0.5:
        # Blessing

        fry_points = await fetch_fry_points(bot, user.id)
        if fry_points is None or fry_points == 0:
            new_fry_points = 1
        else:
            new_fry_points = fry_points + 1

        fry_point_reward_str = f"> - The Fries God has granted you **1 {FRY_POINT_EMOJI}**! You now have **{new_fry_points} {FRY_POINT_EMOJI}**."
        phrase = random.choice(blessing_phrases)
        content = f"{phrase}\n{fry_point_reward_str}"
        embed = discord.Embed(
            title="A Blessing from the Fries God",
            description=content,
            color=0xFFD700,  # Golden color
        )
        embed.set_thumbnail(url=Thumbnails.fries_shrine)
        embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
        await upsert_user_fry_points(bot, user.id, user.name, new_fry_points)
        await message.reply(embed=embed)

    else:
        # Curse
        phrase = random.choice(curses_phrases)
        content = f"{phrase}"
        embed = discord.Embed(
            title="A Curse from the Fries God",
            description=content,
            color=0x808080,  # Gray color
        )
        embed.set_thumbnail(url=Thumbnails.fries_shrine)
        embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
        await message.reply(embed=embed)

    cooldown_ends_on = get_next_12am_est_unix()
    pretty_log(
        "info",
        f"User {user} prayed and received a {'blessing' if 'granted' in content else 'curse'}. Next pray available at <t:{cooldown_ends_on}:R>.",
    )
    if user.id != KHY_USER_ID:  # Don't set cooldown for Khy for testing
        await upsert_server_cooldown(
            bot, user.id, user.name, cooldown_type, cooldown_ends_on
        )


def get_next_12am_est_unix():
    """
    Returns the Unix timestamp (seconds) for the next 12:00 AM EST.
    """
    from datetime import datetime, timedelta

    import pytz

    est = pytz.timezone("US/Eastern")
    now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
    now_est = now_utc.astimezone(est)
    # Calculate next midnight
    next_midnight_est = now_est.replace(
        hour=0, minute=0, second=0, microsecond=0
    ) + timedelta(days=1)
    # Convert to UTC, then to Unix timestamp
    next_midnight_utc = next_midnight_est.astimezone(pytz.utc)
    return int(next_midnight_utc.timestamp())


def seconds_until_next_pray_reset():
    """
    Returns the number of seconds until the next pray reset at 12:00 AM EST.
    """
    import time

    now = int(time.time())
    next_reset = get_next_12am_est_unix()
    return max(0, next_reset - now)

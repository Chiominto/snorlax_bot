from datetime import datetime
from zoneinfo import ZoneInfo

import discord

from constants.celestial_constants import (
    BURGER_SHOP_STAFF,
    CELESTIAL_ROLES,
    CELESTIAL_TEXT_CHANNELS,
)
from utils.functions.role_checks import is_burger_shop_staff

TIMEZONE = ZoneInfo("Asia/Manila")
YEAR = 2026

MONTH_START = 11
DAY_START = 15

MONTH_END = 12
DAY_END = 13

HOUR = 13
MINUTE = 0
SECOND = 0


def is_burger_shop_ongoing() -> bool:
    """
    Returns True if the burger shop event is currently ongoing based on the defined start and end dates and times in the specified timezone.
    """
    now = datetime.now(TIMEZONE)
    event_start = datetime(
        YEAR, MONTH_START, DAY_START, HOUR, MINUTE, SECOND, tzinfo=TIMEZONE
    )
    event_end = datetime(
        YEAR, MONTH_END, DAY_END, HOUR, MINUTE, SECOND, tzinfo=TIMEZONE
    )
    return event_start <= now < event_end


def is_user_id_burger_shop_staff(user_id):
    return user_id in BURGER_SHOP_STAFF


async def check_burger_shop(interaction: discord.Interaction) -> bool:
    if not is_burger_shop_ongoing() and not is_burger_shop_staff(interaction):
        await interaction.response.send_message(
            "The Burger shop event is not currently ongoing. Please wait for it to open.",
            ephemeral=True,
        )
        return False

    return True

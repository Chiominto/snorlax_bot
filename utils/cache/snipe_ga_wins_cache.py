
from datetime import datetime

import discord

from utils.cache.cache_list import snipe_ga_wins_cache
from utils.db.snipe_ga_wins_db import (fetch_snipe_ga_wins,
                                       fetch_user_snipe_ga_wins,
                                       remove_user_snipe_ga_win)
from utils.logs.pretty_log import pretty_log


async def load_snipe_ga_wins_cache(bot: discord.Client):
    """Load the snipe giveaway wins cache from the database."""
    try:
        snipe_ga_wins = await fetch_snipe_ga_wins(bot)
        snipe_ga_wins_cache.clear()
        for win in snipe_ga_wins:
            snipe_ga_wins_cache[win["user_id"]] = win
        pretty_log("cache", "✅ Loaded snipe giveaway wins cache.")
    except Exception as e:
        pretty_log("error", f"Error loading snipe giveaway wins cache: {e}")


def upsert_snipe_ga_win_cache(user_id: int, user_name: str, ga_wins: int, resets_on: int):
    """Upsert a user's snipe giveaway wins into the cache."""
    snipe_ga_wins_cache[user_id] = {
        "user_id": user_id,
        "user_name": user_name,
        "ga_wins": ga_wins,
        "resets_on": resets_on,
    }
    pretty_log("cache", f"✅ Upserted snipe giveaway wins for user {user_id} into cache.")

def remove_user_snipe_ga_win_cache(user_id: int):
    """Remove a user's snipe giveaway wins from the cache."""
    if user_id in snipe_ga_wins_cache:
        del snipe_ga_wins_cache[user_id]
        pretty_log("cache", f"✅ Removed snipe giveaway wins for user {user_id} from cache.")

async def determine_if_user_is_eligible(bot: discord.Client, user_id: int) -> tuple[bool, int | None]:
    """Determine if a user is eligible for a snipe giveaway based on their wins and reset time.
    Can't join if won 3 times,
    Additionally, if user won 3 times and if the reset time has passed, it will delete the user from the db and cache, allowing them to join again. Returns reset time if user is not eligible, otherwise returns True if user is eligible."""

    user_data = snipe_ga_wins_cache.get(user_id)
    if not user_data:
        # User not found in cache, fetch from database
        user_data = await fetch_user_snipe_ga_wins(bot, user_id)
        if user_data:
            upsert_snipe_ga_win_cache(
                user_data["user_id"],
                user_data["user_name"],
                user_data["ga_wins"],
                user_data["resets_on"],
            )
        else:
            # User not found in database, they are eligible
            return True, None

    if user_data["ga_wins"] < 3:
        return True, None  # User is eligible to join
    else:
        # Check if reset time has passed
        now = int(datetime.now().timestamp())
        if now >= user_data["resets_on"]:
            # Reset the user's wins and update the cache and database
            await remove_user_snipe_ga_win(bot, user_id)
            return True, None
        else:
            return False, user_data["resets_on"]  # Return reset time if user is not eligible
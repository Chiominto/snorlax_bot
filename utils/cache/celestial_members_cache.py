import discord
from utils.logs.pretty_log import pretty_log

from utils.cache.cache_list import celestial_members_cache
from utils.db.celestial_members_db import (
    fetch_all_celestial_members,
)

async def load_celestial_members_cache(bot: discord.Client):
    """Loads all celestial members from the database into the cache."""
    rows, error = await fetch_all_celestial_members(bot)
    if error:
        pretty_log(
            tag="error",
            message=f"Failed to load celestial members cache: {error}",
            include_trace=True,
        )
        return False
    celestial_members_cache.clear()
    for row in rows:
        user_id = row["user_id"]
        celestial_members_cache[user_id] = {
            "user_name": row["user_name"],
            "pokemon_name": row["pokemon_name"],
            "channel_id": row["channel_id"],
            "actual_perks": row["actual_perks"],
            "clan_bank_donation": row["clan_bank_donation"],
            "clan_treasury_donation": row["clan_treasury_donation"],
            "date_joined": row["date_joined"],
        }
    pretty_log(
        tag="info",
        message=f"Loaded {len(celestial_members_cache)} celestial members into cache.",
    )
    return True

def fetch_channel_id_cache(user_id: int):
    """Fetches the channel ID of a celestial member from the cache."""
    member_data = celestial_members_cache.get(user_id)
    return member_data["channel_id"] if member_data else None

def fetch_celestial_member_cache(user_id: int):
    """Fetches a celestial member from the cache."""
    return celestial_members_cache.get(user_id)

def fetch_user_id_by_channel_id_cache(channel_id: int):
    """Fetches a user ID from the cache based on channel ID."""
    for user_id, data in celestial_members_cache.items():
        if data["channel_id"] == channel_id:
            return user_id
    return None

def fetch_user_id_by_pokemon_name_cache(pokemon_name: str):
    """Fetches a user ID from the cache based on pokemeow name."""
    for user_id, data in celestial_members_cache.items():
        if data["pokemon_name"] == pokemon_name:
            return user_id
    return None

def fetch_user_id_by_user_name_cache(user_name: str):
    """Fetches a user ID from the cache based on user name."""
    for user_id, data in celestial_members_cache.items():
        if data["user_name"] == user_name:
            return user_id
    return None

def fetch_user_id_by_user_name_or_pokemon_name_cache(name: str):
    """Fetches a user ID from the cache based on user name or pokemeow name."""
    for user_id, data in celestial_members_cache.items():
        if data["user_name"] == name or data["pokemon_name"] == name:
            return user_id
    return None



def upsert_celestial_member_cache(user_id: int, user_name: str, pokemon_name: str, channel_id: int, actual_perks: str, clan_bank_donation: int, clan_treasury_donation: int, date_joined: int):
    """Upserts a celestial member into the cache."""
    celestial_members_cache[user_id] = {
        "user_name": user_name,
        "pokemon_name": pokemon_name,
        "channel_id": channel_id,
        "actual_perks": actual_perks,
        "clan_bank_donation": clan_bank_donation,
        "clan_treasury_donation": clan_treasury_donation,
        "date_joined": date_joined,
    }

def update_actual_perks_cache(user_id: int, actual_perks: str):
    """Updates the actual perks of a celestial member in the cache."""
    if user_id in celestial_members_cache:
        celestial_members_cache[user_id]["actual_perks"] = actual_perks
        return True
    return False

def update_pokemeow_name_cache(user_id: int, pokemon_name: str):
    """Updates the pokemeow name of a celestial member in the cache."""
    if user_id in celestial_members_cache:
        celestial_members_cache[user_id]["pokemon_name"] = pokemon_name
        return True
    return False

def update_channel_id_cache(user_id: int, channel_id: int):
    """Updates the channel ID of a celestial member in the cache."""
    if user_id in celestial_members_cache:
        celestial_members_cache[user_id]["channel_id"] = channel_id
        return True
    return False

def update_clan_bank_donation_cache(user_id: int, clan_bank_donation: int):
    """Updates the clan bank donation of a celestial member in the cache."""
    if user_id in celestial_members_cache:
        celestial_members_cache[user_id]["clan_bank_donation"] = clan_bank_donation
        return True
    return False

def update_clan_treasury_donation_cache(user_id: int, clan_treasury_donation: int):
    """Updates the clan treasury donation of a celestial member in the cache."""
    if user_id in celestial_members_cache:
        celestial_members_cache[user_id]["clan_treasury_donation"] = clan_treasury_donation
        return True
    return False

def remove_celestial_member_cache(user_id: int):
    """Removes a celestial member from the cache."""
    if user_id in celestial_members_cache:
        del celestial_members_cache[user_id]
        return True
    return False
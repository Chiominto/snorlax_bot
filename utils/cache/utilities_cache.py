import discord

from utils.db.utilities_db import fetch_all_utility_settings
from utils.logs.pretty_log import pretty_log

from .cache_list import utility_cache


async def load_utility_cache(bot: discord.Client):
    utility_settings = await fetch_all_utility_settings(bot)
    utility_cache.clear()
    for setting in utility_settings:
        user_id = setting["user_id"]
        if user_id not in utility_cache:
            utility_cache[user_id] = {
                "user_name": setting["user_name"],
                "utilities": {},
            }
        utility_cache[user_id]["utilities"][setting["utility_type"]] = setting[
            "setting"
        ]

def upsert_utility_setting_cache(
    user_id: int, user_name: str, utility_type: str, setting: str
):
    if user_id not in utility_cache:
        utility_cache[user_id] = {
            "user_name": user_name,
            "utilities": {},
        }
    utility_cache[user_id]["utilities"][utility_type] = setting

def fetch_user_utility_setting_cache(user_id: int, utility_type: str) -> str | None:
    user_cache = utility_cache.get(user_id)
    if user_cache:
        return user_cache["utilities"].get(utility_type)
    return None

def fetch_user_utility_setting_cache_by_user_name(user_name: str, utility_type: str) -> str | None:
    for user_id, user_cache in utility_cache.items():
        if user_cache["user_name"] == user_name:
            return user_cache["utilities"].get(utility_type)
    return None

def fetch_user_utility_type_setting_cache(user_id: int, utility_type: str) -> str | None:
    user_cache = utility_cache.get(user_id)
    if user_cache:
        return user_cache["utilities"].get(utility_type)
    return None


def _normalize_pokemon_cache_key(pokemon_name: str) -> str:
    """Return a canonical key so cache lookups are case/space-insensitive."""
    return pokemon_name.strip().lower()


def phone_copy_description(text: str, setting: str = None, member_id: int = None):
    if setting is None:
        if member_id is not None:
            setting = (
                fetch_user_utility_type_setting_cache(member_id, "phone") or "iphone"
            )
        else:
            setting = "iphone"
    if setting == "iphone":
        new_text = f"`{text}`"  # Wrap in code block for iPhone formatting
    elif setting == "android":
        new_text = f"{text}"  # Plain text for Android
    else:
        new_text = text  # Default to plain text if setting is unrecognized
    return new_text

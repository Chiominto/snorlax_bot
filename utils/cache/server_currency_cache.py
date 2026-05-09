import discord

from utils.cache.cache_list import server_currency_cache
from utils.db.server_currency_db import fetch_all_server_currency
from utils.logs.pretty_log import pretty_log


async def load_server_currency_cache(bot: discord.Client):
    try:
        currency_data = await fetch_all_server_currency(bot)
        if not currency_data:
            pretty_log(
                message="⚠️ No server currency data found to load into cache.",
                tag="cache",
            )
            return

        server_currency_cache.clear()

        for entry in currency_data:
            user_id = entry["user_id"]
            server_currency_cache[user_id] = {
                "user_name": entry["user_name"],
                "currency": entry["currency"],
                "fry_points": entry["fry_points"],
            }

        pretty_log(
            message=f"✅ Loaded {len(server_currency_cache)} server currency entries into cache.",
            tag="cache",
        )

        if len(server_currency_cache) == 0:
            pretty_log(
                message="⚠️ Server currency cache is empty after loading.",
                tag="cache",
            )
        return server_currency_cache

    except Exception as e:
        pretty_log(
            message=f"❌ Error loading server currency cache: {e}",
            tag="cache",
        )
        raise e


def upsert_user_currency_cache(user_id: int, user_name: str, currency: int = 0):
    if user_id in server_currency_cache:
        server_currency_cache[user_id]["user_name"] = user_name
        server_currency_cache[user_id]["currency"] = currency
    else:
        server_currency_cache[user_id] = {
            "user_name": user_name,
            "currency": currency,
            "fry_points": 0,
        }


def upsert_user_fry_points_cache(user_id: int, user_name: str, fry_points: int = 0):
    if user_id in server_currency_cache:
        server_currency_cache[user_id]["user_name"] = user_name
        server_currency_cache[user_id]["fry_points"] = fry_points
    else:
        server_currency_cache[user_id] = {
            "user_name": user_name,
            "currency": 0,
            "fry_points": fry_points,
        }


def upsert_user_currency_and_fry_points_cache(
    user_id: int,
    user_name: str,
    currency: int = 0,
    fry_points: int = 0,
):
    if user_id in server_currency_cache:
        server_currency_cache[user_id]["user_name"] = user_name
        server_currency_cache[user_id]["currency"] = currency
        server_currency_cache[user_id]["fry_points"] = fry_points
    else:
        server_currency_cache[user_id] = {
            "user_name": user_name,
            "currency": currency,
            "fry_points": fry_points,
        }


def delete_user_currency_cache(user_id: int):
    if user_id in server_currency_cache:
        del server_currency_cache[user_id]


def reset_all_currency_only_cache():
    for user_id in server_currency_cache:
        server_currency_cache[user_id]["currency"] = 0


def reset_all_fry_points_only_cache():
    for user_id in server_currency_cache:
        server_currency_cache[user_id]["fry_points"] = 0


def reset_all_currency_and_fry_points_cache():
    for user_id in server_currency_cache:
        server_currency_cache[user_id]["currency"] = 0
        server_currency_cache[user_id]["fry_points"] = 0

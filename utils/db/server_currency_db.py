import discord

from constants.celestial_constants import (
    CELESTIAL_ROLES,
    CELESTIAL_SERVER_ID,
    CELESTIAL_TEXT_CHANNELS,
    KHY_USER_ID,
)
from utils.logs.pretty_log import pretty_log

# SQL Script
"""CREATE TABLE server_currency (
    user_id BIGINT PRIMARY KEY,
    user_name TEXT,
    currency BIGINT DEFAULT 0,
    fry_points BIGINT DEFAULT 0
);
"""


async def upsert_user_currency(
    bot: discord.Client,
    user_id: int,
    user_name: str,
    currency: int = 0,
):
    """Upsert a user's currency data in the database."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO server_currency (user_id, user_name, currency)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id) DO UPDATE
                SET user_name = EXCLUDED.user_name,
                    currency = EXCLUDED.currency
                """,
                user_id,
                user_name,
                currency,
            )
    except Exception as e:
        pretty_log(message=f"Error upserting user currency: {e}", tag="error")


async def upsert_user_fry_points(
    bot: discord.Client,
    user_id: int,
    user_name: str,
    fry_points: int = 0,
):
    """Upsert a user's fry points data in the database."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO server_currency (user_id, user_name, fry_points)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id) DO UPDATE
                SET user_name = EXCLUDED.user_name,
                    fry_points = EXCLUDED.fry_points
                """,
                user_id,
                user_name,
                fry_points,
            )
    except Exception as e:
        pretty_log(message=f"Error upserting user fry points: {e}", tag="error")


async def get_user_currency(bot: discord.Client, user_id: int):
    """Fetch a user's currency data from the database."""
    try:
        async with bot.pg_pool.acquire() as conn:
            result = await conn.fetchrow(
                "SELECT user_id, user_name, currency, fry_points FROM server_currency WHERE user_id = $1",
                user_id,
            )
            return result
    except Exception as e:
        pretty_log(message=f"Error fetching user currency: {e}", tag="error")
        return None


async def delete_user_currency(bot: discord.Client, user_id: int):
    """Delete a user's currency data from the database."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM server_currency WHERE user_id = $1",
                user_id,
            )
    except Exception as e:
        pretty_log(message=f"Error deleting user currency: {e}", tag="error")


async def reset_all_currency_only(bot: discord.Client):
    """Reset all users' currency to 0, but keep fry points intact."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute("UPDATE server_currency SET currency = 0")
    except Exception as e:
        pretty_log(message=f"Error resetting all user currency: {e}", tag="error")


async def reset_all_fry_points_only(bot: discord.Client):
    """Reset all users' fry points to 0, but keep currency intact."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute("UPDATE server_currency SET fry_points = 0")
    except Exception as e:
        pretty_log(message=f"Error resetting all user fry points: {e}", tag="error")


async def reset_all_currency_and_fry_points(bot: discord.Client):
    """Reset all users' currency and fry points to 0."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                "UPDATE server_currency SET currency = 0, fry_points = 0"
            )
    except Exception as e:
        pretty_log(
            message=f"Error resetting all user currency and fry points: {e}",
            tag="error",
        )


async def fetch_fry_points(bot: discord.Client, user_id: int):
    """Fetch a user's fry points from the database."""
    try:
        async with bot.pg_pool.acquire() as conn:
            result = await conn.fetchrow(
                "SELECT fry_points FROM server_currency WHERE user_id = $1",
                user_id,
            )
            return result["fry_points"] if result else None
    except Exception as e:
        pretty_log(message=f"Error fetching user fry points: {e}", tag="error")
        return None

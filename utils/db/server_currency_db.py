import discord

from constants.celestial_constants import (CELESTIAL_ROLES,
                                           CELESTIAL_SERVER_ID,
                                           CELESTIAL_TEXT_CHANNELS,
                                           KHY_USER_ID)
from utils.logs.pretty_log import pretty_log

# SQL Script
"""CREATE TABLE server_currency (
    user_id BIGINT PRIMARY KEY,
    user_name TEXT,
    currency BIGINT DEFAULT 0,
    fry_points BIGINT DEFAULT 0,
    burnt_fry_points BIGINT DEFAULT 0,
);
"""


async def get_all_people_with_most_fry_points(bot: discord.Client):
    """Fetch all users tied for the highest fry points."""
    try:
        async with bot.pg_pool.acquire() as conn:
            results = await conn.fetch(
                """
                SELECT user_id, user_name, fry_points
                FROM server_currency
                WHERE fry_points = (
                    SELECT MAX(fry_points)
                    FROM server_currency
                )
                ORDER BY user_name ASC
                """,
            )
            return results
    except Exception as e:
        pretty_log(message=f"Error fetching top fry points: {e}", tag="error")
        return []

async def get_all_people_with_most_burnt_fry_points(bot: discord.Client):
    """Fetch all users tied for the highest burnt fry points."""
    try:
        async with bot.pg_pool.acquire() as conn:
            results = await conn.fetch(
                """
                SELECT user_id, user_name, burnt_fry_points
                FROM server_currency
                WHERE burnt_fry_points = (
                    SELECT MAX(burnt_fry_points)
                    FROM server_currency
                )
                ORDER BY user_name ASC
                """,
            )
            return results
    except Exception as e:
        pretty_log(message=f"Error fetching top burnt fry points: {e}", tag="error")
        return []


async def fetch_all_server_currency(bot: discord.Client):
    """Fetch all server currency data from the database."""
    try:
        async with bot.pg_pool.acquire() as conn:
            results = await conn.fetch(
                "SELECT user_id, user_name, currency, fry_points, burnt_fry_points FROM server_currency"
            )
            return results
    except Exception as e:
        pretty_log(message=f"Error fetching all server currency: {e}", tag="error")
        return []


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
        # Update the cache as well
        from utils.cache.server_currency_cache import \
            upsert_user_currency_cache

        upsert_user_currency_cache(user_id, user_name, currency)
    except Exception as e:
        pretty_log(message=f"Error upserting user currency: {e}", tag="error")

async def upsert_user_burnt_fry_points(
    bot: discord.Client,
    user_id: int,
    user_name: str,
    burnt_fry_points: int = 0,
):
    """Upsert a user's burnt fry points data in the database."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO server_currency (user_id, user_name, burnt_fry_points)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id) DO UPDATE
                SET user_name = EXCLUDED.user_name,
                    burnt_fry_points = EXCLUDED.burnt_fry_points
                """,
                user_id,
                user_name,
                burnt_fry_points,
            )
        # Update the cache as well
        from utils.cache.server_currency_cache import \
            upsert_user_burnt_fry_points_cache

        upsert_user_burnt_fry_points_cache(user_id, user_name, burnt_fry_points)
    except Exception as e:
        pretty_log(message=f"Error upserting user burnt fry points: {e}", tag="error")






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
        # Update the cache as well
        from utils.cache.server_currency_cache import \
            upsert_user_fry_points_cache

        upsert_user_fry_points_cache(user_id, user_name, fry_points)
    except Exception as e:
        pretty_log(message=f"Error upserting user fry points: {e}", tag="error")


async def get_user_currency(bot: discord.Client, user_id: int):
    """Fetch a user's currency data from the database."""
    try:
        async with bot.pg_pool.acquire() as conn:
            result = await conn.fetchrow(
                "SELECT user_id, user_name, currency, fry_points, burnt_fry_points FROM server_currency WHERE user_id = $1",
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
        # Remove from cache as well
        from utils.cache.server_currency_cache import \
            delete_user_currency_cache

        delete_user_currency_cache(user_id)
    except Exception as e:
        pretty_log(message=f"Error deleting user currency: {e}", tag="error")


async def reset_all_currency_only(bot: discord.Client):
    """Reset all users' currency to 0, but keep fry points intact."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute("UPDATE server_currency SET currency = 0")
        # Clear the currency values in the cache as well
        from utils.cache.server_currency_cache import \
            reset_all_currency_only_cache

        reset_all_currency_only_cache()

    except Exception as e:
        pretty_log(message=f"Error resetting all user currency: {e}", tag="error")


async def reset_all_fry_points_only(bot: discord.Client):
    """Reset all users' fry points to 0, but keep currency intact."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute("UPDATE server_currency SET fry_points = 0")
        # Clear the fry points values in the cache as well
        from utils.cache.server_currency_cache import \
            reset_all_fry_points_only_cache

        reset_all_fry_points_only_cache()
    except Exception as e:
        pretty_log(message=f"Error resetting all user fry points: {e}", tag="error")

async def reset_all_fry_points_and_burnt_fry_points(bot: discord.Client):
    """Reset all users' fry points and burnt fry points to 0, but keep currency intact."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                "UPDATE server_currency SET fry_points = 0, burnt_fry_points = 0"
            )
        # Clear the fry points and burnt fry points values in the cache as well
        from utils.cache.server_currency_cache import \
            reset_all_fry_points_and_burnt_fry_points_cache

        reset_all_fry_points_and_burnt_fry_points_cache()
    except Exception as e:
        pretty_log(message=f"Error resetting all user fry points and burnt fry points: {e}", tag="error")

async def reset_all_burnt_fry_points_only(bot: discord.Client):
    """Reset all users' burnt fry points to 0, but keep currency and fry points intact."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute("UPDATE server_currency SET burnt_fry_points = 0")
        # Clear the burnt fry points values in the cache as well
        from utils.cache.server_currency_cache import \
            reset_all_burnt_fry_points_only_cache

        reset_all_burnt_fry_points_only_cache()
    except Exception as e:
        pretty_log(message=f"Error resetting all user burnt fry points: {e}", tag="error")

async def reset_all_currency_and_fry_points(bot: discord.Client):
    """Reset all users' currency and fry points to 0, but keep burnt fry points intact."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                "UPDATE server_currency SET currency = 0, fry_points = 0"
            )
        # Clear the currency and fry points values in the cache as well
        from utils.cache.server_currency_cache import \
            reset_all_currency_and_fry_points_cache

        reset_all_currency_and_fry_points_cache()
    except Exception as e:
        pretty_log(
            message=f"Error resetting all user currency and fry points: {e}",
            tag="error",
        )

async def reset_all_currency_and_fry_points_and_burnt_fry_points(bot: discord.Client):
    """Reset all users' currency, fry points, and burnt fry points to 0."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                "UPDATE server_currency SET currency = 0, fry_points = 0, burnt_fry_points = 0"
            )
        # Clear the entire cache as well
        from utils.cache.server_currency_cache import \
            reset_all_currency_and_fry_points_and_burnt_fry_points_cache

        reset_all_currency_and_fry_points_and_burnt_fry_points_cache()
    except Exception as e:
        pretty_log(
            message=f"Error resetting all user currency, fry points, and burnt fry points: {e}",
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

async def fetch_burnt_fry_points(bot: discord.Client, user_id: int):
    """Fetch a user's burnt fry points from the database."""
    try:
        async with bot.pg_pool.acquire() as conn:
            result = await conn.fetchrow(
                "SELECT burnt_fry_points FROM server_currency WHERE user_id = $1",
                user_id,
            )
            return result["burnt_fry_points"] if result else None
    except Exception as e:
        pretty_log(message=f"Error fetching user burnt fry points: {e}", tag="error")
        return None

async def reset_server_currency_table(bot: discord.Client):
    """Reset the entire server currency table (delete all data)."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute("TRUNCATE TABLE server_currency")
    except Exception as e:
        pretty_log(message=f"Error resetting server currency table: {e}", tag="error")


async def upsert_server_currency(
    bot: discord.Client,
    user_id: int,
    user_name: str,
    currency: int = 0,
    fry_points: int = 0,
    burnt_fry_points: int = 0,
):
    """Upsert a user's currency and fry points data in the database."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO server_currency (user_id, user_name, currency, fry_points, burnt_fry_points)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (user_id) DO UPDATE
                SET user_name = EXCLUDED.user_name,
                    currency = EXCLUDED.currency,
                    fry_points = EXCLUDED.fry_points,
                    burnt_fry_points = EXCLUDED.burnt_fry_points
                """,
                user_id,
                user_name,
                currency,
                fry_points,
                burnt_fry_points,
            )
        # Update the cache as well
        from utils.cache.server_currency_cache import \
            upsert_user_currency_and_fry_points_and_burnt_fry_points_cache

        upsert_user_currency_and_fry_points_and_burnt_fry_points_cache(
            user_id, user_name, currency, fry_points, burnt_fry_points
        )

    except Exception as e:
        pretty_log(message=f"Error upserting server currency: {e}", tag="error")

async def fetch_all_fry_points(bot: discord.Client):
    """Fetch all users' fry points from the database."""
    try:
        async with bot.pg_pool.acquire() as conn:
            results = await conn.fetch(
                "SELECT user_id, user_name, fry_points FROM server_currency"
            )
            return results
    except Exception as e:
        pretty_log(message=f"Error fetching all user fry points: {e}", tag="error")
        return []

async def fetch_all_burnt_fry_points(bot: discord.Client):
    """Fetch all users' burnt fry points from the database."""
    try:
        async with bot.pg_pool.acquire() as conn:
            results = await conn.fetch(
                "SELECT user_id, user_name, burnt_fry_points FROM server_currency"
            )
            return results
    except Exception as e:
        pretty_log(message=f"Error fetching all user burnt fry points: {e}", tag="error")
        return []
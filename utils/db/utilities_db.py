import discord

from utils.logs.pretty_log import pretty_log

# SQL SCRIPT
"""CREATE TABLE utilities (
    user_id BIGINT NOT NULL,
    user_name TEXT,
    utility_type TEXT NOT NULL,
    setting TEXT,
    PRIMARY KEY (user_id, utility_type)
);
"""

async def upsert_utility_setting(
    bot: discord.Client,
    user_id: int,
    user_name: str,
    utility_type: str,
    setting: str,
):
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO utilities (user_id, user_name, utility_type, setting)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id, utility_type) DO UPDATE
                SET user_name = EXCLUDED.user_name,
                    setting = EXCLUDED.setting
                """,
                user_id,
                user_name,
                utility_type,
                setting,
            )
        pretty_log(
            "db",
            f"Upserted utility setting for {user_name} - {utility_type}: {setting}",
            bot=bot,
        )
        # Update the cache after upserting to the database
        from utils.cache.utilities_cache import upsert_utility_setting_cache
        upsert_utility_setting_cache(
            user_id=user_id,
            user_name=user_name,
            utility_type=utility_type,
            setting=setting,
        )
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to upsert utility setting for {user_id} - {utility_type}: {e}",
            bot=bot,
        )
async def fetch_user_utility_type_setting(bot: discord.Client, user_id: int, utility_type: str) -> str | None:
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT setting
                FROM utilities
                WHERE user_id = $1 AND utility_type = $2
                """,
                user_id,
                utility_type,
            )
            if row:
                pretty_log(
                    "db",
                    f"Fetched utility setting for user_id: {user_id}, utility_type: {utility_type}",
                    bot=bot,
                )
                return row["setting"]
            else:
                pretty_log(
                    "db",
                    f"No utility setting found for user_id: {user_id}, utility_type: {utility_type}",
                    bot=bot,
                )
                return None
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to fetch utility setting for {user_id} - {utility_type}: {e}",
            bot=bot,
        )
        return None
async def fetch_utility_type_settings(bot: discord.Client, utility_type: str):
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT user_id, user_name, setting
                FROM utilities
                WHERE utility_type = $1
                """,
                utility_type,
            )
            settings = [
                {
                    "user_id": row["user_id"],
                    "user_name": row["user_name"],
                    "setting": row["setting"],
                }
                for row in rows
            ]
            pretty_log(
                message=f"✅ Fetched settings for utility type: {utility_type}",
                tag="db",
            )
            return settings
    except Exception as e:
        pretty_log(
            message=f"❌ Error fetching settings for utility type {utility_type} - {e}",
            tag="db",
        )
        return []

async def fetch_phone_utility_setting(bot: discord.Client, user_id: int) -> str | None:
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT setting
                FROM utilities
                WHERE user_id = $1 AND utility_type = 'phone'
                """,
                user_id,
            )
            if row:
                pretty_log(
                    "db",
                    f"Fetched phone utility setting for user_id: {user_id}",
                    bot=bot,
                )
                return row["setting"]
            else:
                pretty_log(
                    "db",
                    f"No phone utility setting found for user_id: {user_id}",
                    bot=bot,
                )
                return None
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to fetch phone utility setting for user_id: {user_id} - {e}",
            bot=bot,
        )
        return None

async def fetch_all_utility_settings(bot: discord.Client):
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT user_id, user_name, utility_type, setting
                FROM utilities
                """
            )
            settings = [
                {
                    "user_id": row["user_id"],
                    "user_name": row["user_name"],
                    "utility_type": row["utility_type"],
                    "setting": row["setting"],
                }
                for row in rows
            ]
            pretty_log(message="✅ Fetched all utility settings", tag="db")
            return settings
    except Exception as e:
        pretty_log(message=f"❌ Error fetching all utility settings - {e}", tag="db")
        return []

async def update_user_name(bot: discord.Client, user_id: int, new_user_name: str):
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE utilities
                SET user_name = $1
                WHERE user_id = $2
                """,
                new_user_name,
                user_id,
            )
        pretty_log(
            "db",
            f"Updated user_name for user_id: {user_id} to {new_user_name}",
            bot=bot,
        )
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to update user_name for user_id: {user_id} - {e}",
            bot=bot,
        )


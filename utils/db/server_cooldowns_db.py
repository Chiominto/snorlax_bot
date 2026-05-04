import discord
from utils.logs.pretty_log import pretty_log

# SQL Script
"""CREATE TABLE server_cooldowns (
    user_id BIGINT NOT NULL,
    user_name TEXT,
    cooldown_type VARCHAR(50) NOT NULL,
    ends_on BIGINT,
    PRIMARY KEY (user_id, cooldown_type)
);"""

async def upsert_server_cooldown(
    bot: discord.Client,
    user_id: int,
    user_name: str,
    cooldown_type: str,
    ends_on: int,
):
    """Upsert a user's cooldown data in the database."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO server_cooldowns (user_id, user_name, cooldown_type, ends_on)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id, cooldown_type) DO UPDATE
                SET user_name = EXCLUDED.user_name,
                    ends_on = EXCLUDED.ends_on
                """,
                user_id,
                user_name,
                cooldown_type,
                ends_on,
            )
    except Exception as e:
        pretty_log(message=f"Error upserting server cooldown: {e}", tag="error")


async def fetch_user_server_cooldown_for_type(bot, user_id, cooldown_type):
    """Fetch a user's cooldown data for a specific type."""
    try:
        async with bot.pg_pool.acquire() as conn:
            result = await conn.fetchrow(
                """
                SELECT * FROM server_cooldowns
                WHERE user_id = $1 AND cooldown_type = $2
                """,
                user_id,
                cooldown_type,
            )
            return result
    except Exception as e:
        pretty_log(message=f"Error fetching user server cooldown: {e}", tag="error")
        return None

async def remove_user_server_cooldown_type(bot, user_id, cooldown_type):
    """Remove a user's cooldown data for a specific type."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                DELETE FROM server_cooldowns
                WHERE user_id = $1 AND cooldown_type = $2
                """,
                user_id,
                cooldown_type,
            )
    except Exception as e:
        pretty_log(message=f"Error removing user server cooldown: {e}", tag="error")

async def fetch_all_due_server_cooldowns_by_type(bot, cooldown_type):
    """Fetch all cooldowns of a specific type that are due."""
    try:
        async with bot.pg_pool.acquire() as conn:
            results = await conn.fetch(
                """
                SELECT * FROM server_cooldowns
                WHERE cooldown_type = $1 AND ends_on <= EXTRACT(EPOCH FROM NOW())
                """,
                cooldown_type,
            )
            return results
    except Exception as e:
        pretty_log(message=f"Error fetching due server cooldowns: {e}", tag="error")
        return []

async def clear_all_pray_cooldowns(bot):
    """Clear all cooldowns of type 'pray'."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                DELETE FROM server_cooldowns
                WHERE cooldown_type = 'pray'
                """
            )
    except Exception as e:
        pretty_log(message=f"Error clearing pray cooldowns: {e}", tag="error")
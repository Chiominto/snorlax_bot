import time
from datetime import datetime, timedelta

import discord

from utils.logs.pretty_log import pretty_log

#SQL SCRIPT
"""CREATE TABLE snipe_ga_wins (
    user_id BIGINT,
    user_name TEXT,
    ga_wins BIGINT,
    resets_on BIGINT,
    PRIMARY KEY (user_id)
);
"""

# Fetch all snipe giveaway wins from the database
async def fetch_snipe_ga_wins(bot: discord.Client):
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM snipe_ga_wins")
            return [
                {
                    "user_id": row["user_id"],
                    "user_name": row["user_name"],
                    "ga_wins": row["ga_wins"],
                    "resets_on": row["resets_on"],
                }
                for row in rows
            ]
    except Exception as e:
        pretty_log("error", f"Error fetching snipe_ga_wins: {e}")
        return []

 # Fetch a specific user's snipe giveaway wins from the database
async def fetch_user_snipe_ga_wins(bot: discord.Client, user_id: int):
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM snipe_ga_wins WHERE user_id = $1", user_id
            )
            if row:
                return {
                    "user_id": row["user_id"],
                    "user_name": row["user_name"],
                    "ga_wins": row["ga_wins"],
                    "resets_on": row["resets_on"],
                }
            else:
                return None
    except Exception as e:
        pretty_log(
            "error", f"Error fetching snipe_ga_wins for user_id {user_id}: {e}"
        )
        return None



async def upsert_snipe_ga_win(
    bot: discord.Client,
    user_id: int,
    user_name: str,
):
    try:
        now = datetime.now()
        reset_unix = int((now + timedelta(hours=1)).timestamp())

        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO snipe_ga_wins (user_id, user_name, ga_wins, resets_on)
                VALUES ($1, $2, 1, $3)
                ON CONFLICT (user_id) DO UPDATE
                SET user_name = EXCLUDED.user_name,
                    ga_wins = snipe_ga_wins.ga_wins + 1,
                    resets_on = EXCLUDED.resets_on
                RETURNING ga_wins;
                """,
                user_id,
                user_name,
                reset_unix,
            )

        # Update cache with actual ga_wins
        from utils.cache.snipe_ga_wins_cache import upsert_snipe_ga_win_cache
        upsert_snipe_ga_win_cache(
            user_id,
            user_name,
            row["ga_wins"],
            reset_unix,
        )
    except Exception as e:
        pretty_log("error", f"Error upserting snipe_ga_wins for user_name {user_name}: {e}")


async def remove_user_snipe_ga_win(bot: discord.Client, user_id: int):
    """Remove a user's snipe giveaway wins from the database."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM snipe_ga_wins WHERE user_id = $1", user_id
            )
        # Remove from cache as well
        from utils.cache.snipe_ga_wins_cache import \
            remove_user_snipe_ga_win_cache
        remove_user_snipe_ga_win_cache(user_id)

    except Exception as e:
        pretty_log(
            "error",
            f"Error removing snipe_ga_wins for user_id {user_id}: {e}",
        )

        
async def check_expired_snipe_cooldowns(bot: discord.Client):
    now_unix = int(datetime.now().timestamp())
    async with bot.pg_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT user_id, ga_wins FROM snipe_ga_wins WHERE resets_on <= $1",
            now_unix,
        )

        for row in rows:
            user_id = row["user_id"]
            ga_wins = row["ga_wins"]

            if ga_wins >= 3:
                user = bot.get_user(user_id)
                if user:
                    try:
                        await user.send(
                            "🎉 Your cooldown for the Snipe Giveaway wins has ended! You can join again now."
                        )
                    except Exception:
                        pass  # ignore if DMs closed

        deleted_rows = await conn.fetch(
            "DELETE FROM snipe_ga_wins WHERE resets_on <= $1 RETURNING user_id",
            now_unix,
        )

    from utils.cache.snipe_ga_wins_cache import remove_user_snipe_ga_win_cache
    for deleted in deleted_rows:
        remove_user_snipe_ga_win_cache(deleted["user_id"])

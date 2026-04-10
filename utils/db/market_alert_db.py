import discord

from utils.logs.pretty_log import pretty_log

# SQL SCRIPT
"""CREATE TABLE market_alerts (
    id SERIAL,                              -- auto-incrementing id (not primary key)
    user_id BIGINT,
    user_name TEXT,
    pokemon TEXT,
    dex TEXT,
    max_price BIGINT,
    channel_id BIGINT,
    ping BOOLEAN,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, pokemon)
);

"""


async def insert_market_alert(
    bot: discord.Client,
    user_id: int,
    user_name: str,
    pokemon: str,
    dex: str,
    max_price: int,  # <-- added here
    channel_id: int,
    ping: bool,
):
    pokemon = pokemon.lower()
    dex = str(dex)
    try:
        async with bot.pg_pool.acquire() as connection:
            await connection.execute(
                """
                INSERT INTO market_alerts (user_id, user_name, pokemon, dex, max_price, channel_id, ping)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (user_id, pokemon) DO UPDATE
                SET user_name = EXCLUDED.user_name,
                    dex = EXCLUDED.dex,
                    max_price = EXCLUDED.max_price,
                    channel_id = EXCLUDED.channel_id,
                    ping = EXCLUDED.ping;
                """,
                user_id,
                user_name,
                pokemon,
                dex,
                max_price,  # <-- added here
                channel_id,
                ping,
            )
            pretty_log(
                "db", f"✅ Inserted/Updated market alert for {user_name} - {pokemon}"
            )

            # Update cache
            from utils.cache.market_alert_cache import insert_alert_into_cache

            insert_alert_into_cache(
                user_id,
                user_name,
                pokemon,
                dex,
                max_price,  # <-- added here
                channel_id,
                ping,
            )

    except Exception as e:
        pretty_log(
            "error", f"Failed to insert/update market alert: {e}", include_trace=True
        )


async def fetch_market_alert(
    bot: discord.Client,
    user_id: int,
    pokemon: str,
) -> dict | None:
    pokemon = pokemon.lower()
    try:
        async with bot.pg_pool.acquire() as connection:
            result = await connection.fetchrow(
                """
                SELECT user_id, user_name, pokemon, dex, max_price, channel_id, ping, created_at
                FROM market_alerts
                WHERE user_id = $1 AND pokemon = $2;
                """,
                user_id,
                pokemon,
            )
            if result:
                alert_data = dict(result)
                pretty_log(
                    "db",
                    f"✅ Fetched market alert for user_id={user_id}, pokemon={pokemon}",
                )
                return alert_data
            else:
                pretty_log(
                    "db",
                    f"⚠️ No market alert found for user_id={user_id}, pokemon={pokemon}",
                )
                return None
    except Exception as e:
        pretty_log("error", f"Failed to fetch market alert: {e}", include_trace=True)
        return None


async def fetch_all_market_alerts(bot: discord.Client) -> list[dict]:
    """Fetches all market alerts from the database."""
    try:
        async with bot.pg_pool.acquire() as connection:
            results = await connection.fetch(
                """
                SELECT user_id, user_name, pokemon, dex, max_price, channel_id, ping, created_at
                FROM market_alerts;
                """
            )
            alerts = [dict(record) for record in results]
            pretty_log(
                "db", f"✅ Fetched {len(alerts)} total market alerts from database"
            )
            return alerts
    except Exception as e:
        pretty_log("error", f"Failed to fetch market alerts: {e}", include_trace=True)
        return []


async def fetch_market_alerts_for_user(bot: discord.Client, user_id: int):
    """Fetches all market alerts for a specific user."""
    try:
        async with bot.pg_pool.acquire() as connection:
            results = await connection.fetch(
                """
                SELECT user_id, user_name, pokemon, dex, max_price, channel_id, ping, created_at
                FROM market_alerts
                WHERE user_id = $1;
                """,
                user_id,
            )
            alerts = [dict(record) for record in results]
            pretty_log(
                "db", f"✅ Fetched {len(alerts)} market alerts for user_id={user_id}"
            )
            return alerts
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to fetch market alerts for user_id={user_id}: {e}",
            include_trace=True,
        )
        return []


async def update_market_alert(
    bot: discord.Client,
    user_id: int,
    pokemon: str,
    new_max_price: int = None,
    new_channel_id: int = None,
    new_ping: bool = None,
):
    """Updates an existing market alert with new values."""
    pokemon = pokemon.lower()
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE market_alerts
                SET max_price = COALESCE($2, max_price),
                    channel_id = COALESCE($3, channel_id),
                    ping = COALESCE($4, ping)
                WHERE user_id = $1 AND pokemon = $5
                """,
                user_id,
                new_max_price,
                new_channel_id,
                new_ping,
                pokemon,
            )
            pretty_log(
                "db",
                f"✅ Updated market alert for user_id={user_id}, pokemon={pokemon}",
            )

            from utils.cache.market_alert_cache import update_user_alert_in_cache

            update_user_alert_in_cache(
                user_id,
                pokemon,
                new_max_price,
                new_channel_id,
                new_ping,
            )

    except Exception as e:
        pretty_log("error", f"Failed to update market alert: {e}", include_trace=True)


async def remove_market_alert(bot: discord.Client, user_id: int, pokemon: str):
    """Removes a market alert from the database."""
    pokemon = pokemon.lower()
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                DELETE FROM market_alerts
                WHERE user_id = $1 AND pokemon = $2
                """,
                user_id,
                pokemon,
            )
            pretty_log(
                "db",
                f"✅ Removed market alert for user_id={user_id}, pokemon={pokemon}",
            )

            # Update cache
            from utils.cache.market_alert_cache import remove_alert_from_user_in_cache

            remove_alert_from_user_in_cache(user_id, pokemon)

    except Exception as e:
        pretty_log("error", f"Failed to remove market alert: {e}", include_trace=True)


async def remove_all_market_alerts_for_user(bot: discord.Client, user_id: int):
    """Removes all market alerts for a specific user."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                DELETE FROM market_alerts
                WHERE user_id = $1
                """,
                user_id,
            )
            pretty_log("db", f"✅ Removed all market alerts for user_id={user_id}")

            # Update cache
            from utils.cache.market_alert_cache import (
                remove_all_alerts_for_user_in_cache,
            )

            remove_all_alerts_for_user_in_cache(user_id)

    except Exception as e:
        pretty_log(
            "error",
            f"Failed to remove market alerts for user_id={user_id}: {e}",
            include_trace=True,
        )


async def remove_recent_market_alerts(
    bot: discord.Client, user: discord.Member, num_alerts: int
):
    """
    Removes the most recent market alerts for a user from the database, then returns what was removed.
    """
    user_id = user.id
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, pokemon, dex, max_price, channel_id, ping
                FROM market_alerts
                WHERE user_id = $1
                ORDER BY id DESC
                LIMIT $2
                """,
                user_id,
                num_alerts,
            )
            if not rows:
                pretty_log(
                    message=f"⚠️ No market alerts found to remove for user ID: {user_id}",
                    tag="db",
                )
                return []

            await conn.execute(
                """
                DELETE FROM market_alerts
                WHERE id = ANY($1::int[])
                """,
                [row["id"] for row in rows],
            )
            pretty_log(
                message=f"✅ Removed {len(rows)} recent market alerts for user ID: {user_id}",
                tag="db",
            )
            # Update cache
            from utils.cache.market_alert_cache import remove_alert_from_user_in_cache

            for row in rows:
                remove_alert_from_user_in_cache(user_id, row["pokemon"])

            return rows

    except Exception as e:
        pretty_log(
            message=f"❌ Failed to remove recent market alerts for user ID: {user_id}: {e}",
            tag="error",
            include_trace=True,
        )
        return []

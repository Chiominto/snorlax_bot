import discord
from utils.logs.pretty_log import pretty_log

# SQL SCRIPT
"""CREATE TABLE temp_roles (
    user_id BIGINT NOT NULL,
    user_name TEXT,
    role_id BIGINT NOT NULL,
    role_name TEXT,
    PRIMARY KEY (user_id, role_id)
);
"""

async def upsert_temp_role(
    bot: discord.Client,
    user_id: int,
    user_name: str,
    role_id: int,
    role_name: str
):
    """Upsert a temporary role for a user in the database."""
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO temp_roles (user_id, user_name, role_id, role_name)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id, role_id) DO UPDATE
            SET user_name = EXCLUDED.user_name,
                role_name = EXCLUDED.role_name
            """,
            user_id,
            user_name,
            role_id,
            role_name
        )
        pretty_log(
            "info",
            f"Upserted temp role {role_name} for user {user_name} ({user_id})"
        )

async def delete_temp_role(
    bot: discord.Client,
    user_id: int,
    role_id: int
):
    """Delete a temporary role for a user from the database."""
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            DELETE FROM temp_roles
            WHERE user_id = $1 AND role_id = $2
            """,
            user_id,
            role_id
        )
        pretty_log(
            "info",
            f"Deleted temp role ID {role_id} for user ID {user_id}"
        )

async def delete_all_temp_roles_by_role_id(
    bot: discord.Client,
    role_id: int
):
    """Delete all temporary roles with a specific role ID from the database."""
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            DELETE FROM temp_roles
            WHERE role_id = $1
            """,
            role_id
        )
        pretty_log(
            "info",
            f"Deleted all temp roles with role ID {role_id}"
        )

async def fetch_all_temp_roles_by_role_id(
    bot: discord.Client,
    role_id: int
):
    """Fetch all temporary roles with a specific role ID from the database."""
    async with bot.pg_pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT user_id, user_name, role_id, role_name
            FROM temp_roles
            WHERE role_id = $1
            """,
            role_id
        )
        pretty_log(
            "info",
            f"Fetched {len(rows)} temp roles with role ID {role_id}"
        )
        return rows
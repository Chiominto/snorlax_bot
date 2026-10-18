from typing import Any

import discord

from utils.logs.pretty_log import pretty_log

# SQL SCRIPT
"""CREATE TABLE balloon_prizes (
    prize TEXT,
    balloon_name TEXT,
    stock INTEGER,
    dex TEXT,
    image_link TEXT,
    PRIMARY KEY (prize, balloon_name)
);"""


async def balloon_name_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[discord.app_commands.Choice[str]]:
    """Autocomplete function to fetch balloon names from the database based on user input."""

    bot = interaction.client

    try:
        balloon_names = await fetch_all_balloon_names(bot)

        if not balloon_names:
            return []

        return [
            discord.app_commands.Choice(
                name=name.title(),
                value=name,
            )
            for name in balloon_names
            if current.lower() in name.lower()
        ]

    except Exception:
        return []

async def update_balloon_prize_stock(
    bot: discord.Client,
    prize: str,
    balloon_name: str,
    new_stock: int,
):
    """Update the stock value for a specific balloon prize."""

    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE balloon_prizes
                SET stock = $1
                WHERE prize = $2
                  AND balloon_name = $3
                """,
                new_stock,
                prize,
                balloon_name,
            )

            pretty_log(
                "db",
                f"Updated stock for balloon prize '{prize}' "
                f"({balloon_name}) to {new_stock}.",
                bot=bot,
            )

            return True

    except Exception as e:
        pretty_log(
            "error",
            f"Failed to update stock for balloon prize "
            f"'{prize}' ({balloon_name}): {e}",
            bot=bot,
        )
        return False

async def fetch_total_stock_for_balloon(
    bot: discord.Client,
    balloon_name: str,
) -> int:
    """Fetch the total stock for a given balloon by summing the stock values for all prizes associated with that balloon."""

    try:
        async with bot.pg_pool.acquire() as conn:
            total_stock = await conn.fetchval(
                """
                SELECT SUM(stock)
                FROM balloon_prizes
                WHERE balloon_name = $1
                """,
                balloon_name,
            )

            return total_stock if total_stock is not None else 0

    except Exception as e:
        pretty_log(
            "error",
            f"Failed to fetch total stock for balloon '{balloon_name}': {e}",
            bot=bot,
        )
        return 0

async def debug_balloon_names(bot: discord.Client):
    async with bot.pg_pool.acquire() as conn:
        result = await conn.fetch(
            """
            SELECT DISTINCT balloon_name
            FROM balloon_prizes
            """
        )

        print("Raw result:", result)

        for row in result:
            print(
                "Row type:",
                type(row),
                "Row content:",
                row,
            )
        return [row["balloon_name"] for row in result]


async def fetch_all_balloon_names(
    bot: discord.Client,
) -> list[str]:
    """Fetch a list of all unique balloon names from the balloon_prizes table."""

    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT DISTINCT balloon_name
                FROM balloon_prizes
                """
            )

            balloon_names = [row["balloon_name"] for row in rows]

            pretty_log(
                "debug",
                f"fetch_all_balloon_names result: {balloon_names}",
                bot=bot,
            )

            return balloon_names

    except Exception as e:
        pretty_log(
            "error",
            f"Exception in fetch_all_balloon_names: {e}",
            bot=bot,
        )
        return []

async def fetch_all_balloon_prizes(
    bot: discord.Client,
) -> dict[str, dict[str, dict[str, Any]]]:
    """Fetch all balloon prizes and organize them in a nested dictionary structure."""

    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT prize, balloon_name, stock, dex, image_link
                FROM balloon_prizes
                """
            )

            balloon_data = {}

            for row in rows:
                prize = row["prize"]
                balloon_name = row["balloon_name"]
                stock = row["stock"]
                dex = row["dex"]
                image_link = row["image_link"]

                if balloon_name not in balloon_data:
                    balloon_data[balloon_name] = {}

                balloon_data[balloon_name][prize] = {
                    "stock": stock,
                    "dex": dex,
                    "image_link": image_link,
                }

            return balloon_data

    except Exception as e:
        pretty_log(
            "error",
            f"Failed to fetch all balloon prizes: {e}",
            bot=bot,
        )
        return {}

async def add_balloon_prize(
    bot: discord.Client,
    prize: str,
    balloon_name: str,
    stock: int,
    dex: str = None,
    image_link: str = None,
):
    """Add or update a balloon prize in the database."""

    if dex is not None:
        dex = str(dex)

    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO balloon_prizes (
                    prize,
                    balloon_name,
                    stock,
                    dex,
                    image_link
                )
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (prize, balloon_name)
                DO UPDATE SET
                    stock = EXCLUDED.stock,
                    dex = EXCLUDED.dex,
                    image_link = EXCLUDED.image_link
                """,
                prize,
                balloon_name,
                stock,
                dex,
                image_link,
            )

            pretty_log(
                "db",
                f"Successfully added/updated balloon prize: "
                f"{prize}, balloon: {balloon_name}",
                bot=bot,
            )

            return True

    except Exception as e:
        pretty_log(
            "error",
            f"Error adding/updating balloon prize: "
            f"{prize}, balloon: {balloon_name}, error: {e}",
            bot=bot,
        )
        return False

async def update_balloon_prize_stock(
    bot: discord.Client,
    prize: str,
    balloon_name: str,
    new_stock: int,
):
    """Update the stock value for a specific balloon prize."""

    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE balloon_prizes
                SET stock = $1
                WHERE prize = $2
                  AND balloon_name = $3
                """,
                new_stock,
                prize,
                balloon_name,
            )

            pretty_log(
                "db",
                f"Updated stock for balloon prize '{prize}' "
                f"({balloon_name}) to {new_stock}.",
                bot=bot,
            )

            return True

    except Exception as e:
        pretty_log(
            "error",
            f"Failed to update stock for balloon prize "
            f"'{prize}' ({balloon_name}): {e}",
            bot=bot,
        )
        return False


async def fetch_balloon_prize_with_balloon(
    bot: discord.Client,
    prize: str,
    balloon_name: str,
) -> dict[str, Any] | None:
    """Fetch a specific balloon prize along with its associated balloon name."""

    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT prize, balloon_name, stock, dex, image_link
                FROM balloon_prizes
                WHERE LOWER(prize) = LOWER($1)
                  AND LOWER(balloon_name) = LOWER($2)
                """,
                prize,
                balloon_name,
            )

            if row:
                return {
                    "prize": row["prize"],
                    "balloon_name": row["balloon_name"],
                    "stock": row["stock"],
                    "dex": row["dex"],
                    "image_link": row["image_link"],
                }

            return None

    except Exception as e:
        pretty_log(
            "error",
            f"Failed to fetch balloon prize '{prize}' "
            f"({balloon_name}): {e}",
            bot=bot,
        )
        return None

async def fetch_balloon_prize(
    bot: discord.Client,
    prize: str,
) -> dict[str, Any] | None:
    """Fetch a specific balloon prize without filtering by balloon name."""

    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT prize, balloon_name, stock, dex, image_link
                FROM balloon_prizes
                WHERE prize = $1
                """,
                prize,
            )

            if row:
                return {
                    "prize": row["prize"],
                    "balloon_name": row["balloon_name"],
                    "stock": row["stock"],
                    "dex": row["dex"],
                    "image_link": row["image_link"],
                }

            return None

    except Exception as e:
        pretty_log(
            "error",
            f"Failed to fetch balloon prize '{prize}': {e}",
            bot=bot,
        )
        return None


async def fetch_balloon_prizes_by_balloon(
    bot: discord.Client,
    balloon_name: str,
) -> list[dict[str, Any]]:
    """Fetch all prizes associated with a specific balloon."""

    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT prize, stock, dex, image_link
                FROM balloon_prizes
                WHERE balloon_name = $1
                """,
                balloon_name,
            )

            prizes = [
                {
                    "prize": row["prize"],
                    "stock": row["stock"],
                    "dex": row["dex"],
                    "image_link": row["image_link"],
                }
                for row in rows
            ]

            return prizes

    except Exception as e:
        pretty_log(
            "error",
            f"Error fetching prizes for balloon '{balloon_name}': {e}",
            bot=bot,
        )
        return []

async def remove_balloon_prize(
    bot: discord.Client,
    prize: str,
    balloon_name: str,
):
    """Remove a specific balloon prize from the database."""

    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                DELETE FROM balloon_prizes
                WHERE LOWER(prize) = LOWER($1)
                  AND LOWER(balloon_name) = LOWER($2)
                """,
                prize,
                balloon_name,
            )

            pretty_log(
                "db",
                f"Removed balloon prize: {prize} for balloon: {balloon_name}",
                bot=bot,
            )

            return True

    except Exception as e:
        pretty_log(
            "error",
            f"Error removing balloon prize: {e}",
            bot=bot,
        )
        return False

async def clear_box_prizes(
    bot: discord.Client,
    balloon_name: str,
):
    """Clear all prizes associated with a specific balloon."""

    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                DELETE FROM balloon_prizes
                WHERE balloon_name = $1
                """,
                balloon_name,
            )

            pretty_log(
                "db",
                f"Cleared all prizes for balloon: {balloon_name}",
                bot=bot,
            )

            return True

    except Exception as e:
        pretty_log(
            "error",
            f"Error clearing prizes for balloon '{balloon_name}': {e}",
            bot=bot,
        )
        return False

async def clear_all_prizes(bot: discord.Client):
    """Clear all balloon prizes from the database."""

    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                DELETE FROM balloon_prizes
                """
            )

            pretty_log(
                "db",
                "Cleared all balloon prizes from the database.",
                bot=bot,
            )

            return True

    except Exception as e:
        pretty_log(
            "error",
            f"Error clearing all balloon prizes: {e}",
            bot=bot,
        )
        return False
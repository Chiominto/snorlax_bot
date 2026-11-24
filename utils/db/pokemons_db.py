from datetime import datetime

import discord

from utils.logs.pretty_log import pretty_log

_pokemon_type_column_ready = False

# SQL SCRIPT
"""CREATE TABLE pokemons (
    pokemon_name TEXT PRIMARY KEY,
    dex_number INT,
    rarity TEXT,
    pokemon_type TEXT,
    current_listing BIGINT,
    lowest_market BIGINT,
    true_lowest BIGINT,
    listing_seen TEXT,
    emoji_id TEXT,
    image_link TEXT,
    monthly_average BIGINT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"""


async def upsert_pokemon_db(
    bot: discord,
    pokemon_name: str,
    dex_number: int,
    rarity: str,
    current_listing: int,
    lowest_market: int,
    true_lowest: int,
    listing_seen: str,
    emoji_id: str,
    image_link: str,
    monthly_average: int,
):
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO pokemons (pokemon_name, dex_number, rarity, current_listing, lowest_market, true_lowest, listing_seen, emoji_id, image_link, monthly_average)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (pokemon_name) DO UPDATE SET
                    dex_number = EXCLUDED.dex_number,
                    rarity = EXCLUDED.rarity,
                    current_listing = EXCLUDED.current_listing,
                    lowest_market = EXCLUDED.lowest_market,
                    true_lowest = EXCLUDED.true_lowest,
                    listing_seen = EXCLUDED.listing_seen,
                    emoji_id = EXCLUDED.emoji_id,
                    image_link = EXCLUDED.image_link,
                    monthly_average = EXCLUDED.monthly_average,
                    last_updated = CURRENT_TIMESTAMP;
                """,
                pokemon_name.lower(),
                dex_number,
                rarity,
                current_listing,
                lowest_market,
                true_lowest,
                listing_seen,
                emoji_id,
                image_link,
                monthly_average,
            )
        pretty_log(
            message=f"✅ Upserted Pokémon '{pokemon_name}' into database.",
            tag="db",
        )
    except Exception as e:
        pretty_log(
            message=f"❌ Error upserting Pokémon '{pokemon_name}' into database: {e}",
            tag="db",
        )


async def update_market_value(
    bot: discord.Client,
    pokemon_name: str,
    dex_number: int,
    lowest_market: int | None = None,
    current_listing: int = 0,
    true_lowest: int = 0,
    listing_seen: str | None = None,
    image_link: str = None,
    rarity: str = "unknown",
    monthly_average: int = 0,
):
    """
    Insert or update market value data for a Pokémon.
    """

    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                    INSERT INTO pokemons (
                        pokemon_name, dex_number, lowest_market,
                        current_listing, true_lowest, listing_seen, image_link, last_updated, rarity, monthly_average
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    ON CONFLICT (pokemon_name) DO UPDATE SET
                        dex_number = $2,
                        lowest_market = $3,
                        current_listing = $4,
                        true_lowest = LEAST($5, pokemons.true_lowest),
                        listing_seen = COALESCE($6, pokemons.listing_seen),
                        image_link = COALESCE($7, pokemons.image_link),
                        last_updated = $8,
                        rarity = COALESCE($9, pokemons.rarity),
                        monthly_average = COALESCE($10, pokemons.monthly_average)
                    """,
                pokemon_name.lower(),
                dex_number,
                lowest_market,
                current_listing,
                true_lowest,
                listing_seen,
                image_link,
                datetime.now(),
                rarity,
                monthly_average,
            )
        pretty_log(
            message=f"✅ Updated market value for Pokémon '{pokemon_name}' in database.",
            tag="db",
        )

        # Update cache as well
        from utils.cache.pokemon_cache import update_market_value_in_cache

        update_market_value_in_cache(
            pokemon_name=pokemon_name,
            dex_number=dex_number,
            lowest_market=lowest_market,
            current_listing=current_listing,
            true_lowest=true_lowest,
            listing_seen=listing_seen,
            image_link=image_link,
            rarity=rarity,
            monthly_average=monthly_average,
        )
    except Exception as e:
        pretty_log(
            message=f"❌ Error updating market value for Pokémon '{pokemon_name}': {e}",
            tag="db",
        )


async def update_pokemon_dex_info(
    bot: discord.Client,
    pokemon_name: str,
    dex_number: int | None = None,
    rarity: str | None = None,
    image_link: str | None = None,
    pokemon_type: str | None = None,
):
    global _pokemon_type_column_ready

    try:
        async with bot.pg_pool.acquire() as conn:
            if not _pokemon_type_column_ready:
                await conn.execute(
                    "ALTER TABLE pokemons ADD COLUMN IF NOT EXISTS pokemon_type TEXT;"
                )
                _pokemon_type_column_ready = True
            status = await conn.execute(
                """
                INSERT INTO pokemons (
                    pokemon_name, dex_number, rarity, image_link, pokemon_type
                )
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (pokemon_name) DO UPDATE SET
                    dex_number = COALESCE(EXCLUDED.dex_number, pokemons.dex_number),
                    rarity = COALESCE(EXCLUDED.rarity, pokemons.rarity),
                    image_link = COALESCE(EXCLUDED.image_link, pokemons.image_link),
                    pokemon_type = COALESCE(EXCLUDED.pokemon_type, pokemons.pokemon_type),
                    last_updated = CURRENT_TIMESTAMP
                WHERE
                    (EXCLUDED.dex_number IS NOT NULL AND pokemons.dex_number IS DISTINCT FROM EXCLUDED.dex_number)
                    OR (EXCLUDED.rarity IS NOT NULL AND pokemons.rarity IS DISTINCT FROM EXCLUDED.rarity)
                    OR (EXCLUDED.image_link IS NOT NULL AND pokemons.image_link IS DISTINCT FROM EXCLUDED.image_link)
                    OR (EXCLUDED.pokemon_type IS NOT NULL AND pokemons.pokemon_type IS DISTINCT FROM EXCLUDED.pokemon_type);
                """,
                pokemon_name.lower(),
                dex_number,
                rarity,
                image_link,
                pokemon_type,
            )

        from utils.cache.pokemon_cache import update_pokemon_dex_info_in_cache

        update_pokemon_dex_info_in_cache(
            pokemon_name=pokemon_name,
            dex_number=dex_number,
            rarity=rarity,
            image_link=image_link,
            pokemon_type=pokemon_type,
        )
        if status.endswith("0"):
            pretty_log(
                message=f"ℹ️ Dex details for Pokémon '{pokemon_name}' already match the database.",
                tag="db",
            )
        else:
            pretty_log(
                message=f"✅ Updated dex details for Pokémon '{pokemon_name}' in database.",
                tag="db",
            )
    except Exception as e:
        pretty_log(
            message=f"❌ Error updating dex details for Pokémon '{pokemon_name}': {e}",
            tag="db",
        )
        raise


async def fetch_all_pokemons(bot: discord.Client):
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM pokemons;")
            pokemons = [
                {
                    "pokemon_name": row["pokemon_name"],
                    "dex_number": row["dex_number"],
                    "rarity": row["rarity"],
                    "pokemon_type": row.get("pokemon_type"),
                    "current_listing": row["current_listing"],
                    "lowest_market": row["lowest_market"],
                    "true_lowest": row["true_lowest"],
                    "listing_seen": row["listing_seen"],
                    "emoji_id": row["emoji_id"],
                    "image_link": row["image_link"],
                    "monthly_average": row["monthly_average"],
                    "last_updated": row.get("last_updated"),
                }
                for row in rows
            ]
            pretty_log(
                "db", f"✅ Fetched {len(pokemons)} Pokémon entries from database."
            )
            return pokemons
    except Exception as e:
        pretty_log("db", f"❌ Error fetching Pokémon entries from database: {e}")
        return []


async def update_emoji_id(bot: discord, pokemon_name: str, emoji_id: str):
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE pokemons
                SET emoji_id = $1
                WHERE pokemon_name = $2;
                """,
                emoji_id,
                pokemon_name.lower(),
            )
        pretty_log(
            message=f"✅ Updated emoji ID for Pokémon '{pokemon_name}' in database.",
            tag="db",
        )
        # Update cache as well
        from utils.cache.pokemon_cache import update_emoji_id_in_cache

        update_emoji_id_in_cache(pokemon_name, emoji_id)

    except Exception as e:
        pretty_log(
            message=f"❌ Error updating emoji ID for Pokémon '{pokemon_name}' in database: {e}",
            tag="db",
        )


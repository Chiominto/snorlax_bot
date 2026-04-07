import discord

from utils.logs.pretty_log import pretty_log
from datetime import datetime
# SQL SCRIPT
"""CREATE TABLE pokemons (
    pokemon_name TEXT PRIMARY KEY,
    dex_number INT,
    rarity TEXT,
    current_listing BIGINT,
    lowest_market BIGINT,
    true_lowest BIGINT,
    listing_seen TEXT,
    emoji_id TEXT,
    image_link TEXT,
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
):
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO pokemons (pokemon_name, dex_number, rarity, current_listing, lowest_market, true_lowest, listing_seen, emoji_id, image_link)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (pokemon_name) DO UPDATE SET
                    dex_number = EXCLUDED.dex_number,
                    rarity = EXCLUDED.rarity,
                    current_listing = EXCLUDED.current_listing,
                    lowest_market = EXCLUDED.lowest_market,
                    true_lowest = EXCLUDED.true_lowest,
                    listing_seen = EXCLUDED.listing_seen,
                    emoji_id = EXCLUDED.emoji_id,
                    image_link = EXCLUDED.image_link,
                    last_updated = CURRENT_TIMESTAMP;
                """,
                pokemon_name,
                dex_number,
                rarity,
                current_listing,
                lowest_market,
                true_lowest,
                listing_seen,
                emoji_id,
                image_link,
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
    lowest_market: int = 0,
    current_listing: int = 0,
    true_lowest: int = 0,
    listing_seen: str | None = None,
    image_link: str = None,
    rarity: str = "unknown",
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
                        current_listing, true_lowest, listing_seen, image_link, last_updated, rarity
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (pokemon_name) DO UPDATE SET
                        dex_number = $2,
                        lowest_market = $3,
                        current_listing = $4,
                        true_lowest = LEAST($5, pokemons.true_lowest),
                        listing_seen = COALESCE($6, pokemons.listing_seen),
                        image_link = COALESCE($7, pokemons.image_link),
                        last_updated = $8,
                        rarity = COALESCE($9, pokemons.rarity)
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
        )
    except Exception as e:
        pretty_log(
            message=f"❌ Error updating market value for Pokémon '{pokemon_name}': {e}",
            tag="db",
        )


async def fetch_all_pokemons(bot: discord.Client):
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM pokemons;")
            pokemons = [
                {
                    "pokemon_name": row["pokemon_name"],
                    "dex_number": row["dex_number"],
                    "rarity": row["rarity"],
                    "current_listing": row["current_listing"],
                    "lowest_market": row["lowest_market"],
                    "true_lowest": row["true_lowest"],
                    "listing_seen": row["listing_seen"],
                    "emoji_id": row["emoji_id"],
                    "image_link": row["image_link"],
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
                pokemon_name,
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

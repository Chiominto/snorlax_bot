import discord

from utils.cache.cache_list import pokemon_cache
from utils.db.pokemons_db import fetch_all_pokemons
from utils.logs.pretty_log import pretty_log


async def load_pokemon_cache(bot: discord.Client):
    pokemon_cache.clear()
    try:
        pokemons = await fetch_all_pokemons(bot)
        if not pokemons:
            pretty_log("cache", "⚠️ No Pokémon entries found to load into cache.")
            return

        for entry in pokemons:
            pokemon_cache[entry["pokemon_name"]] = entry

        pretty_log(
            "cache", f"✅ Loaded {len(pokemon_cache)} Pokémon entries into cache."
        )

        if len(pokemon_cache) == 0:
            pretty_log("cache", "⚠️ Pokémon cache is empty after loading.")

        return pokemon_cache

    except Exception as e:
        pretty_log("cache", f"❌ Error loading Pokémon cache: {e}")
        raise


def update_emoji_id_in_cache(pokemon_name: str, emoji_id: str):
    if pokemon_name in pokemon_cache:
        pokemon_cache[pokemon_name]["emoji_id"] = emoji_id
        pretty_log(
            "cache",
            f"✅ Updated emoji ID for Pokémon '{pokemon_name}' in cache.",
        )
    else:
        pretty_log(
            "cache",
            f"⚠️ Pokémon '{pokemon_name}' not found in cache to update emoji ID.",
        )
def update_market_value_in_cache(
    pokemon_name: str,
    dex_number: int,
    lowest_market: int,
    current_listing: int,
    true_lowest: int,
    listing_seen: str,
    image_link: str,
    rarity: str,
):
    if pokemon_name in pokemon_cache:
        pokemon_cache[pokemon_name].update(
            {
                "dex_number": dex_number,
                "lowest_market": lowest_market,
                "current_listing": current_listing,
                "true_lowest": true_lowest,
                "listing_seen": listing_seen,
                "image_link": image_link,
                "rarity": rarity,
            }
        )
        pretty_log(
            "cache",
            f"✅ Updated market value for Pokémon '{pokemon_name}' in cache.",
        )
    else:
        pretty_log(
            "cache",
            f"⚠️ Pokémon '{pokemon_name}' not found in cache to update market value.",
        )

# 🍩────────────────────────────────────────────
#        💤 Pokemon List Names
# 🍩────────────────────────────────────────────
def build_pokemon_list_from_cache():
    """
    Build a dictionary mapping Pokémon names to their dex numbers
    using the global pokemon_cache.
    """
    if not pokemon_cache:
        pretty_log("cache", "⚠️ Pokémon cache is empty, cannot build list.")
        return {}

    pokemon_list = {
        entry["pokemon_name"]: entry["dex_number"] for entry in pokemon_cache.values()
    }
    pretty_log("cache", f"✅ Built Pokémon list with {len(pokemon_list)} entries.")
    return pokemon_list


# 🍩────────────────────────────────────────────
#        💤 Fetch Cache Functions
# 🍩────────────────────────────────────────────
def fetch_pokemon_cache_entry(pokemon_name: str) -> dict | None:
    if pokemon_name in pokemon_cache:
        return pokemon_cache[pokemon_name]
    pretty_log(
        "cache",
        f"⚠️ Pokémon '{pokemon_name}' not found in cache to fetch entry.",
    )
    return None

def fetch_dex_number_cache(pokemon_name: str) -> int | None:
    if pokemon_name in pokemon_cache:
        return pokemon_cache[pokemon_name].get("dex_number")
    pretty_log(
        "cache",
        f"⚠️ Pokémon '{pokemon_name}' not found in cache to fetch dex number.",
    )
    return None

def fetch_rarity_cache(pokemon_name: str) -> str | None:
    if pokemon_name in pokemon_cache:
        return pokemon_cache[pokemon_name].get("rarity")
    pretty_log(
        "cache",
        f"⚠️ Pokémon '{pokemon_name}' not found in cache to fetch rarity.",
    )
    return None

def fetch_image_link_cache(pokemon_name: str) -> str | None:
    if pokemon_name in pokemon_cache:
        return pokemon_cache[pokemon_name].get("image_link")
    pretty_log(
        "cache",
        f"⚠️ Pokémon '{pokemon_name}' not found in cache to fetch image link.",
    )
    return None

def fetch_emoji_id_cache(pokemon_name: str) -> str | None:
    if pokemon_name in pokemon_cache:
        return pokemon_cache[pokemon_name].get("emoji_id")
    pretty_log(
        "cache",
        f"⚠️ Pokémon '{pokemon_name}' not found in cache to fetch emoji ID.",
    )
    return None

def fetch_current_listing_cache(pokemon_name: str) -> int | None:
    if pokemon_name in pokemon_cache:
        return pokemon_cache[pokemon_name].get("current_listing")
    pretty_log(
        "cache",
        f"⚠️ Pokémon '{pokemon_name}' not found in cache to fetch current listing.",
    )
    return None

def fetch_listing_seen_cache(pokemon_name: str) -> str | None:
    if pokemon_name in pokemon_cache:
        return pokemon_cache[pokemon_name].get("listing_seen")
    pretty_log(
        "cache",
        f"⚠️ Pokémon '{pokemon_name}' not found in cache to fetch listing seen.",
    )
    return None

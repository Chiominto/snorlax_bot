import re

import discord
from discord import app_commands

from utils.cache.cache_list import pokemon_cache, pokemon_list_cache
from utils.db.pokemons_db import fetch_all_pokemons
from utils.functions.pokemon_func import format_name_for_pokemons_db_lookup
from utils.logs.debug_log import debug_log, enable_debug
from utils.logs.pretty_log import pretty_log

# (raw_name, normalized_name, display_name, dex_number)
POKEMON_AUTOCOMPLETE_INDEX: list[tuple[str, str, str, int]] = []


def normalize_pokemon_search_text(value: str) -> str:
    return re.sub(r"[^\w\s]", "", value.lower()).replace(" ", "")


def rebuild_pokemon_autocomplete_index() -> None:
    POKEMON_AUTOCOMPLETE_INDEX.clear()
    POKEMON_AUTOCOMPLETE_INDEX.extend(
        (
            name,
            normalize_pokemon_search_text(name),
            format_display_name_for_autocomplete(name),
            dex,
        )
        for name, dex in pokemon_list_cache.items()
    )
    debug_log(
        f"Built POKEMON_AUTOCOMPLETE_INDEX with {len(POKEMON_AUTOCOMPLETE_INDEX)} entries"
    )


# enable_debug(f"{__name__}.pokemon_autocomplete")


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

        build_pokemon_list_from_cache()  # Rebuild the list cache after loading

        return pokemon_cache, pokemon_list_cache

    except Exception as e:
        pretty_log("cache", f"❌ Error loading Pokémon cache: {e}")
        raise


def format_display_name_for_autocomplete(raw_name: str) -> str:
    SPECIAL_CASES = {
        "jangmo-o": "Jangmo-o",
        "hakamo-o": "Hakamo-o",
        "kommo-o": "Kommo-o",
        "tapu-koko": "Tapu-Koko",
        "tapu-lele": "Tapu-Lele",
        "tapu-bulu": "Tapu-Bulu",
        "tapu-fini": "Tapu-Fini",
    }

    clean_name = raw_name.lower()

    if "mega-" in clean_name:
        clean_name = clean_name.replace("mega-", "mega ")

    if clean_name in SPECIAL_CASES:
        return SPECIAL_CASES[clean_name]

    def smart_capitalize(name: str) -> str:
        return " ".join(
            "-".join(sub.capitalize() for sub in part.split("-"))
            for part in name.split()
        )

    return smart_capitalize(clean_name)


# ==================== 🌟 Autocomplete Functions ==================== #
async def pokemon_autocomplete(
    interaction: discord.Interaction, current: str
) -> list[app_commands.Choice[str]]:
    """
    Autocomplete Pokémon names with #Dex display.
    Matches both names and dex numbers.
    Uses a precomputed autocomplete index from pokemon_list_cache.
    """
    debug_log(f"Autocomplete input: '{current}'")

    # Recover gracefully if autocomplete gets called before cache load.
    if not POKEMON_AUTOCOMPLETE_INDEX and pokemon_list_cache:
        rebuild_pokemon_autocomplete_index()

    current_simple = normalize_pokemon_search_text(current or "")
    debug_log(f"Normalized input: '{current_simple}'")

    results_with_name: list[tuple[str, app_commands.Choice[str]]] = []
    seen = set()

    # Check if input looks numeric (dex search)
    dex_query = None
    if current_simple.isdigit():
        try:
            dex_query = int(current_simple)
            debug_log(f"Parsed dex_query: {dex_query}")
        except ValueError:
            debug_log("Failed to parse dex_query")
            dex_query = None

    for name, norm, display_name, dex in POKEMON_AUTOCOMPLETE_INDEX:
        if len(results_with_name) >= 25:
            break

        # Match by name
        if not current_simple or current_simple in norm:
            display = f"{display_name} #{dex}"
            if display not in seen:
                results_with_name.append(
                    (display_name, app_commands.Choice(name=display, value=name))
                )
                seen.add(display)

        # Match by dex number
        if dex_query is not None and dex_query == dex:
            display = f"{display_name} #{dex}"
            if display not in seen:
                results_with_name.append(
                    (display_name, app_commands.Choice(name=display, value=name))
                )
                seen.add(display)

    if not results_with_name:
        debug_log("No matches found")
        results_with_name.append(
            ("", app_commands.Choice(name="No matches found", value=current or ""))
        )

    debug_log(f"Returning {len(results_with_name)} results")
    # Sort alphabetically by display name
    results_with_name.sort(key=lambda x: x[0])
    return [choice for _, choice in results_with_name]


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

    pokemon_list_cache.clear()
    pokemon_list_cache.update(
        {entry["pokemon_name"]: entry["dex_number"] for entry in pokemon_cache.values()}
    )
    rebuild_pokemon_autocomplete_index()
    pretty_log(
        "cache", f"✅ Built Pokémon list with {len(pokemon_list_cache)} entries."
    )
    return pokemon_list_cache


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
    key = pokemon_name.lower()
    if key in pokemon_cache:
        pokemon_cache[key]["emoji_id"] = emoji_id
        pretty_log(
            "cache",
            f"✅ Updated emoji ID for Pokémon '{pokemon_name}' in cache.",
        )
    else:
        pretty_log(
            "cache",
            f"⚠️ Pokémon '{pokemon_name}' not found in cache to update emoji ID.",
        )


def check_pokemon_in_cache(pokemon_name: str) -> bool:
    pokemon_name = format_name_for_pokemons_db_lookup(pokemon_name)
    if pokemon_name in pokemon_cache:
        return True
    key = pokemon_name.lower()
    return key in pokemon_cache


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
    # Normalize key to lowercase for case-insensitive handling
    key = pokemon_name.lower()

    if key in pokemon_cache:
        pokemon_cache[key].update(
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
#        💤 Fetch Cache Functions
# 🍩────────────────────────────────────────────
def fetch_pokemon_cache_entry(pokemon_name: str) -> dict | None:
    key = pokemon_name.lower()
    if key in pokemon_cache:
        return pokemon_cache[key]
    pretty_log(
        "cache",
        f"⚠️ Pokémon '{pokemon_name}' not found in cache to fetch entry.",
    )
    return None


def fetch_dex_number_cache(pokemon_name: str) -> int | None:
    key = pokemon_name.lower()
    if key in pokemon_cache:
        return pokemon_cache[key].get("dex_number")
    pretty_log(
        "cache",
        f"⚠️ Pokémon '{pokemon_name}' not found in cache to fetch dex number.",
    )
    return None


def fetch_rarity_cache(pokemon_name: str) -> str | None:
    key = pokemon_name.lower()
    if key in pokemon_cache:
        return pokemon_cache[key].get("rarity")
    pretty_log(
        "cache",
        f"⚠️ Pokémon '{pokemon_name}' not found in cache to fetch rarity.",
    )
    return None


def fetch_image_link_cache(pokemon_name: str) -> str | None:
    key = format_name_for_pokemons_db_lookup(pokemon_name)
    if key in pokemon_cache:
        return pokemon_cache[key].get("image_link")
    pretty_log(
        "cache",
        f"⚠️ Pokémon '{pokemon_name}' not found in cache to fetch image link.",
    )
    return None


def fetch_emoji_id_cache(pokemon_name: str) -> str | None:
    key = pokemon_name.lower()
    if key in pokemon_cache:
        return pokemon_cache[key].get("emoji_id")
    pretty_log(
        "cache",
        f"⚠️ Pokémon '{pokemon_name}' not found in cache to fetch emoji ID.",
    )
    return None


def fetch_current_listing_cache(pokemon_name: str) -> int | None:
    key = pokemon_name.lower()
    if key in pokemon_cache:
        return pokemon_cache[key].get("current_listing")
    pretty_log(
        "cache",
        f"⚠️ Pokémon '{pokemon_name}' not found in cache to fetch current listing.",
    )
    return None


def fetch_listing_seen_cache(pokemon_name: str) -> str | None:
    key = pokemon_name.lower()
    if key in pokemon_cache:
        return pokemon_cache[key].get("listing_seen")
    pretty_log(
        "cache",
        f"⚠️ Pokémon '{pokemon_name}' not found in cache to fetch listing seen.",
    )
    return None

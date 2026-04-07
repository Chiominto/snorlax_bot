from constants.paldea_galar_dict import dex, rarity_meta
from constants.pokemons import *
from constants.aesthetics import *
from utils.cache.pokemon_cache import (
    fetch_dex_number_cache,
    fetch_pokemon_cache_entry
)
from utils.logs.debug_log import debug_enabled, debug_log, enable_debug
from utils.logs.pretty_log import pretty_log

# ✨───────────────────────────────────────────────
#            📦 Precomputed Lookup Sets
# ✨───────────────────────────────────────────────
7
legendary_set = {mon.lower() for mon in legendary_mons}
superrare_set = {mon.lower() for mon in superrare_mons}
rare_set = {mon.lower() for mon in rare_mons}
uncommon_set = {mon.lower() for mon in uncommon_mons}
common_set = {mon.lower() for mon in common_mons}
exclusive_set = {mon.lower() for mon in exclusive_mons}


# ✨───────────────────────────────────────────────
#            📚 In-Game Pokémon List
# ✨───────────────────────────────────────────────

IN_GAME_MONS_LIST = (
    list(common_mons.keys())
    + list(uncommon_mons.keys())
    + list(rare_mons.keys())
    + list(superrare_mons.keys())
    + list(legendary_mons.keys())
    + list(mega_mons.keys())
    + list(gigantamax_mons.keys())
    + list(shiny_mons.keys())
    + list(shiny_mega_mons.keys())
    + list(shiny_gigantamax_mons.keys())
    + list(golden_mons.keys())
    + list(exclusive_mons.keys())
)

IN_GAME_MONS_SET = {mon.lower() for mon in IN_GAME_MONS_LIST}

# Combine all the mons dictionaries into one lookup
ALL_MONS = {}
ALL_MONS.update(common_mons)
ALL_MONS.update(uncommon_mons)
ALL_MONS.update(rare_mons)
ALL_MONS.update(superrare_mons)
ALL_MONS.update(legendary_mons)
ALL_MONS.update(mega_mons)
ALL_MONS.update(gigantamax_mons)
ALL_MONS.update(shiny_mons)
ALL_MONS.update(shiny_mega_mons)
ALL_MONS.update(shiny_gigantamax_mons)
ALL_MONS.update(golden_mons)
ALL_MONS.update(exclusive_mons)
# ✨───────────────────────────────────────────────
#            🔎 Dex Lookup
# ✨───────────────────────────────────────────────


def get_dex_number_by_name(name: str) -> int | None:
    """
    Returns the dex number for a given Pokémon name.
    Example: get_dex_number_by_name("flutter-mane") -> 987
    """

    name = name.lower().strip()
    mon = ALL_MONS.get(name)
    if mon and "dex" in mon:
        return mon["dex"]

    formatted_name = format_names_for_market_value_lookup(name)
    return fetch_dex_number_cache(formatted_name)


def get_name_via_dex(dex_number: str | int) -> str | None:
    """Returns the Pokémon name for a given dex number in IN_GAME_MONS_LIST."""
    try:
        dex_number = int(dex_number)
    except (ValueError, TypeError):
        return None

    for pokemon in IN_GAME_MONS_LIST:
        if get_dex_number_by_name(pokemon) == dex_number:
            return pokemon

    return None


# ✨───────────────────────────────────────────────
#            🧹 Name Formatting
# ✨───────────────────────────────────────────────


def format_names_for_market_value_lookup(pokemon_name: str) -> str:
    """Format Pokémon name for market value lookup."""

    if "-o" in pokemon_name:
        debug_log(f"SPECIAL: '-o' detected in name: {pokemon_name!r}")

    if pokemon_name.lower().strip() == "type null":
        debug_log(f"SPECIAL: 'type null' detected: {pokemon_name!r}")

    pokemon_name = pokemon_name.lower().strip()

    # ✨ Strip ID numbers (ex: "#7202")
    pokemon_name = pokemon_name.split("#")[0].strip()

    if pokemon_name.startswith("sgmax "):
        base = pokemon_name[6:].strip()
        return f"shiny gigantamax-{base}"

    if pokemon_name.startswith("gmax "):
        base = pokemon_name[5:].strip()
        return f"gigantamax-{base}"

    if "smega" in pokemon_name:
        return pokemon_name.replace("smega", "shiny mega").replace("-", " ")

    if "mega" in pokemon_name:
        return pokemon_name.replace("-", " ")

    return pokemon_name


def strip_prefixes(pokemon_name: str) -> str:
    """
    Strip prefixes like Shiny, Mega, etc. for cleaner display.
    """

    prefixes = [
        "shiny mega",
        "shiny gigantamax",
        "golden mega",
        "gigantamax",
        "mega",
        "shiny",
        "golden",
    ]

    name_lower = pokemon_name.lower()

    for prefix in prefixes:
        for sep in (" ", "-"):
            full = prefix + sep
            if name_lower.startswith(full):
                return pokemon_name[len(full) :].strip().title()

    return pokemon_name.strip().title()


# ✨───────────────────────────────────────────────
#            🎨 Display Helpers
# ✨───────────────────────────────────────────────


def get_display_name(pokemon_name: str, dex: bool = False) -> str:
    """Returns display name with rarity emoji."""

    rarity = get_rarity(pokemon_name)
    rarity_emoji = rarity_meta.get(rarity, {}).get("emoji", "") if rarity else ""

    stripped_name = strip_prefixes(pokemon_name)
    display_name = f"{rarity_emoji} {stripped_name}".strip()

    if dex:
        dex_number = get_dex_number_by_name(pokemon_name)
        if dex_number:
            display_name = f"{display_name} #{dex_number}"

    return display_name


def get_embed_color_by_rarity(pokemon_name: str) -> int:
    rarity = get_rarity(pokemon_name)
    return rarity_meta.get(rarity, {}).get("color", 0xFFFFFF)


def format_price_w_coin(n: int) -> str:
    """Format PokeCoin price with commas."""
    pokecoin = Emojis.pokecoin
    return f"{pokecoin} {n:,}"


# ✨───────────────────────────────────────────────
#            ⭐ Rarity Detection
# ✨───────────────────────────────────────────────


def get_rarity(pokemon: str):
    """Determines Pokémon rarity from its name."""

    name = pokemon.lower()

    if "golden" in name:
        return "golden"

    if "shiny" in name and "gigantamax" in name:
        return "shiny gigantamax"

    if "shiny" in name and "mega" in name:
        return "shiny mega"

    if "shiny" in name:
        return "shiny"

    if "gigantamax" in name:
        return "gigantamax"

    if "mega" in name and "yanmega" not in name and "meganium" not in name:
        return "mega"

    if name in legendary_set:
        return "legendary"

    if name in superrare_set:
        return "superrare"

    if name in rare_set:
        return "rare"

    if name in uncommon_set:
        return "uncommon"

    if name in common_set:
        return "common"

    return None


# ✨───────────────────────────────────────────────
#            🎮 In-Game Check
# ✨───────────────────────────────────────────────
def is_mon_in_game(pokemon_name: str) -> bool:
    """Check if a Pokémon exists in the game."""

    name_lower = pokemon_name.lower()

    if name_lower in IN_GAME_MONS_SET:
        return True

    pokemon_name_formatted = format_names_for_market_value_lookup(pokemon_name)

    market_value = fetch_pokemon_cache_entry(pokemon_name_formatted)

    return market_value is not None

# --------------------
#  Market embed parser utility
# --------------------
import re

import discord

from utils.db.pokemons_db import update_pokemon_dex_info

from utils.logs.debug_log import debug_log
from utils.logs.pretty_log import pretty_log

# enable_debug(f"{__name__}.dex_listener")

emoji_map = {
    "common": "common",
    "uncommon": "uncommon",
    "rare": "rare",
    "superrare": "superrare",
    "legendary": "legendary",
    "shiny": "shiny",
    "golden": "golden",
    "shinymega": "shiny mega",
    "shinygigantamax": "shiny gigantamax",
    "mega": "mega",
    "gigantamax": "gigantamax",
    "goldenmega": "golden mega",
    "goldengigantamax": "golden gigantamax",
}

pokemon_types = {
    "normal",
    "fire",
    "water",
    "electric",
    "grass",
    "ice",
    "fighting",
    "poison",
    "ground",
    "flying",
    "psychic",
    "bug",
    "rock",
    "ghost",
    "dragon",
    "dark",
    "steel",
    "fairy",
}


def extract_pokemon_name_and_dex(text):
    match = re.match(r"(.+?)\s*#(\d+)", text)
    if match:
        name = match.group(1).strip()
        dex = match.group(2).strip()
        return name, dex
    else:
        return text.strip(), None


def extract_rarity_from_embed(embed) -> str:
    """
    Extracts the rarity text or emoji name from the 'Rarity' field in a Discord embed object.
    Returns the mapped rarity as a string (e.g., 'shiny gigantamax').
    """
    debug_log("Starting rarity extraction from embed.")
    fields = []
    # Try to get fields from embed object (discord.py Embed or dict)
    if hasattr(embed, "fields"):
        fields = embed.fields
        debug_log(f"Embed fields attribute found: {fields}")
    elif isinstance(embed, dict) and "fields" in embed:
        fields = embed["fields"]
        debug_log(f"Embed fields key found: {fields}")
    else:
        debug_log(f"Embed has no fields attribute or key. Embed: {embed}")
    for idx, field in enumerate(fields):
        debug_log(f"Checking field {idx}: {field}")
        name = (
            field.get("name")
            if isinstance(field, dict)
            else getattr(field, "name", None)
        )
        value = (
            field.get("value")
            if isinstance(field, dict)
            else getattr(field, "value", None)
        )
        debug_log(f"Field name: {name}, value: {value}")
        if name and name.lower() == "rarity":
            debug_log(f"Found 'Rarity' field with value: {value}")
            match = re.search(r"<:([a-zA-Z0-9_]+):[0-9]+>", value)
            if match:
                emoji_name = match.group(1)
                debug_log(f"Extracted emoji name: {emoji_name}")
                mapped_rarity = emoji_map.get(emoji_name.lower(), emoji_name)
                debug_log(f"Mapped rarity: {mapped_rarity}")
                return mapped_rarity
            debug_log(f"Returning plain rarity value: {value.strip()}")
            return value.strip()
    debug_log("'Rarity' field not found in embed.")
    return ""


def extract_type_from_embed(embed) -> str:
    """Return the embed's type field as underscore-separated type names."""
    fields = getattr(embed, "fields", None)
    if fields is None and isinstance(embed, dict):
        fields = embed.get("fields", [])

    for field in fields or []:
        name = (
            field.get("name")
            if isinstance(field, dict)
            else getattr(field, "name", None)
        )
        value = (
            field.get("value")
            if isinstance(field, dict)
            else getattr(field, "value", None)
        )
        if not name or name.lower() != "type" or not value:
            continue

        found_types = []
        for match in re.finditer(r"<a?:([a-zA-Z0-9_]+):\d+>", value):
            emoji_name = match.group(1).lower()
            if emoji_name.endswith("type"):
                emoji_name = emoji_name[:-4]
            if emoji_name in pokemon_types and emoji_name not in found_types:
                found_types.append(emoji_name)

        if not found_types:
            type_pattern = (
                r"(?<![a-z])("
                + "|".join(sorted(pokemon_types))
                + r")(?![a-z])"
            )
            for match in re.finditer(type_pattern, value, re.IGNORECASE):
                pokemon_type = match.group(1).lower()
                if pokemon_type not in found_types:
                    found_types.append(pokemon_type)

        return "_".join(found_types)

    return ""


async def dex_listener(bot, message: discord.Message):
    """Listens to dex command and updates the image link in the market value cache if it differs from the one in the command output."""
    embed = message.embeds[0] if message.embeds else None
    if not embed:
        return

    embed_author_name = embed.author.name if embed.author else ""
    pokemon_name, dex_number = extract_pokemon_name_and_dex(embed_author_name)
    if not pokemon_name:
        debug_log(
            f"Could not extract pokemon name from embed title: '{embed_author_name}'"
        )
        return
    
    embed_image_url = embed.image.url if embed.image else None
    rarity = extract_rarity_from_embed(embed)
    pokemon_type = extract_type_from_embed(embed)

    updates = {
        "dex_number": int(dex_number) if dex_number else None,
        "rarity": rarity or None,
        "image_link": embed_image_url,
        "pokemon_type": pokemon_type or None,
    }
    if any(value is not None for value in updates.values()):
        await update_pokemon_dex_info(bot, pokemon_name, **updates)
        debug_log(f"Updated dex details for {pokemon_name}: {updates}")
        pretty_log("info", f"Updated dex details for {pokemon_name}.")

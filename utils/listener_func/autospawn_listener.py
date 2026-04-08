import re

import discord
from constants.aesthetics import *
from constants.shellshuckle_constants import SHELLSHUCKLE_TEXT_CHANNELS, SHELLSHUCKLE_ROLES
from constants.paldea_galar_dict import *
from utils.functions.webhook_func import send_webhook
from utils.cache.pokemon_cache import fetch_pokemon_cache_entry
from utils.functions.pokemon_func import format_price_w_coin, get_display_name
from utils.logs.pretty_log import pretty_log

# Colors that signify rare Pokémon (legendary/shiny/golden)
LEGENDARY_COLORS = {
    rarity_meta["legendary"]["color"],
    rarity_meta["shiny"]["color"],
    rarity_meta["golden"]["color"],
}
AUTO_SPAWN_ROLE_ID = SHELLSHUCKLE_ROLES.as_spawn_ping


def format_discord_timestamp(value):
    if value is None:
        return "N/A"
    if isinstance(value, (int, float)):
        return f"<t:{int(value)}:R>"
    if isinstance(value, str):
        if re.match(r"<t:\d+:R>", value):
            return value
        try:
            num = float(value)
            return f"<t:{int(num)}:R>"
        except ValueError:
            return "N/A"
    return "N/A"


def sentence_case_bold(text: str) -> str:
    """
    Convert a string to sentence case and wrap it in bold markdown.

    Example: "pikachu" -> "**Pikachu**"
    """
    if not text:
        return ""
    sentence_cased = text[0].upper() + text[1:].lower()
    return f"**{sentence_cased}**"


def remove_bold_title_case(text: str) -> str:
    """
    Remove bold markdown from a string and convert it to title case.

    Example: "**pikachu**" -> "Pikachu"
    """
    if not text:
        return ""

    # Remove ** at start and end if present
    if text.startswith("**") and text.endswith("**"):
        text = text[2:-2]

    # Convert to title case
    return text.title()


async def as_spawn_ping(bot: discord.Client, message: discord.Message):
    """
    Detects a wild Pokémon spawn in a message and sends the appropriate pings and embeds
    to the configured channels.

    Regular (common/uncommon/rare) Pokémon go to Off-Topic channel with a role ping.
    Paldean, shiny, legendary, golden, or superrare Pokémon also send an embed to the rare spawn channel.

    Args:
        bot (discord.Client): The bot instance.
        message (discord.Message): The Discord message containing the spawn embed.
    """
    # Ignore edited messages or messages without embeds
    if message.edited_at or not message.embeds:
        return

    embed = message.embeds[0]
    gif_url = embed.image.url if embed.image else None

    # Only proceed if the embed title indicates a wild spawn
    if not (embed.title and "A wild" in embed.title):
        return

    dex_number = None
    rarity_key = "unknown"
    rarity_info = rarity_meta.get("unknown", {})
    rarity_color = 0xFFFFFF

    # Extract rarity from embed title emoji
    rarity_emoji_match = re.search(r"<:([a-zA-Z0-9_]+):\d+>", embed.title)
    if rarity_emoji_match:
        raw_rarity_key = rarity_emoji_match.group(1).lower()
        rarity_key_map = {
            "common": "common",
            "uncommon": "uncommon",
            "rare": "rare",
            "superrare": "superrare",
            "legendary": "legendary",
            "shiny": "shiny",
            "golden": "golden",
        }
        rarity_key = rarity_key_map.get(raw_rarity_key, "unknown")
        rarity_info = rarity_meta.get(rarity_key, rarity_meta["unknown"])
        rarity_color = rarity_info["color"]

    # Extract Dex number from embed title emoji

    dex_match = re.search(r"<:([0-9]+):\d+>", embed.title)
    if dex_match:
        dex_number = int(dex_match.group(1))

    # Determine Pokémon name
    if dex_number and dex_number in paldea_galar_dict:
        pokemon_name = sentence_case_bold(paldea_galar_dict[dex_number])
        log_pokemon_name = remove_bold_title_case(pokemon_name)
    else:
        pokemon_name = sentence_case_bold(dex.get(dex_number, "Unknown Pokémon"))
        log_pokemon_name = remove_bold_title_case(pokemon_name)

    shiny_text = "shiny " if rarity_key == "shiny" else ""

    is_paldean = dex_number and dex_number in paldea_galar_dict
    is_legendary_or_rare = embed.color and embed.color.value in LEGENDARY_COLORS


    # -------------------- Regular auto-spawn --------------------
    if not (is_paldean or is_legendary_or_rare):
        # Only ping AS Channel channel
        emoji = rarity_info.get("emoji", "❓")
        AUTO_SPAWN_ROLE_MENTION = f"<@&{AUTO_SPAWN_ROLE_ID}>"
        content = (
            f"{AUTO_SPAWN_ROLE_MENTION} A wild {emoji} {pokemon_name} has appeared!"
        )

        await send_webhook(
            bot=bot,
            channel_id=message.channel.id,
            content=content,
        )
        pretty_log(
            message=f"Auto-spawn ping sent: {log_pokemon_name} in #{message.channel.name}",

            tag="sent",
        )

        return

    # -------------------- Rare / shiny / Paldean spawn --------------------

    mention_role = f"<@&{SHELLSHUCKLE_ROLES.as_rarespawn_ping}>"

    content = f"{mention_role} A wild {shiny_text}{rarity_info.get('emoji', '❓')} {pokemon_name} has appeared!"

    await send_webhook(
        bot=bot,
        channel_id=message.channel.id,
        content=content,
    )
    pretty_log(
        message=f"Rare spawn ping sent: {shiny_text}{log_pokemon_name} in #{message.channel.name}",

        tag="sent",
    )

    # Send embed to rare spawn channel
    has_market_value = False
    market_value_info = await fetch_pokemon_cache_entry(
        bot, log_pokemon_name or "Unknown"
    )
    current_listing_price = None
    last_seen = None
    if not market_value_info or not isinstance(market_value_info, dict):
        pretty_log(
            message=f"Market value not found for {log_pokemon_name or 'Unknown'}",

            tag="info",
        )
    else:
        current_listing_price = market_value_info.get("current_listing")
        last_seen = market_value_info.get("listing_seen", "N/A")
        if current_listing_price is not None and current_listing_price != 0:
            has_market_value = True

    message_link = f"https://discord.com/channels/{getattr(message.guild, 'id', '0')}/{getattr(message.channel, 'id', '0')}/{getattr(message, 'id', '0')}"
    desc = f"A wild {rarity_info.get('emoji', '❓')} {pokemon_name or 'Unknown Pokémon'} has spawned!"
    footer_text = f"Spawned in {getattr(message.guild, 'name', 'Unknown Guild')}"
    footer_icon = getattr(getattr(message.guild, "icon", None), "url", None) or ""
    embed_color = getattr(embed.color, "value", 0xFFFFFF) if embed.color else 0xFFFFFF
    rare_spawn_embed = discord.Embed(title=desc, url=message_link, color=embed_color)
    rare_spawn_embed.set_image(url=gif_url)
    rare_spawn_embed.set_footer(text=footer_text, icon_url=footer_icon)

    last_seen = format_discord_timestamp(last_seen)
    if has_market_value:
        current_listing_price_formatted = format_price_w_coin(current_listing_price)
        field_name_str = f"Value as of {last_seen}"
        rare_spawn_embed.add_field(
            name=field_name_str, value=current_listing_price_formatted or "N/A"
        )

    rare_spawn_channel = getattr(message.guild, "get_channel", lambda x: None)(
        SHELLSHUCKLE_TEXT_CHANNELS.rare_spawns
    )
    if rare_spawn_channel:
        await send_webhook(
            bot=bot,
            channel_id=rare_spawn_channel.id,
            embed=rare_spawn_embed,
        )
    if not has_market_value:
        return

    name_formatted = get_display_name(log_pokemon_name or "Unknown", dex=True)
    value_embed = discord.Embed(
        description=name_formatted,
        color=embed_color,
    )
    field_name_str = f"Value as of {last_seen}"
    value_embed.add_field(
        name=field_name_str, value=current_listing_price_formatted or "N/A"
    )
    await send_webhook(
        bot=bot,
        channel_id=message.channel.id,
        embed=value_embed,
    )

import re

import discord

from constants.aesthetics import *
from constants.celestial_constants import (CELESTIAL_ROLES,
                                           CELESTIAL_TEXT_CHANNELS)
from constants.paldea_galar_dict import *
from utils.cache.pokemon_cache import fetch_pokemon_cache_entry
from utils.functions.pokemon_func import format_price_w_coin, get_display_name
from utils.functions.webhook_func import send_webhook
from utils.logs.debug_log import debug_log, enable_debug
from utils.logs.pretty_log import pretty_log

enable_debug(f"{__name__}.as_spawn_ping")
# Colors that signify rare Pokémon (legendary/shiny/golden)
LEGENDARY_COLORS = {
    rarity_meta["legendary"]["color"],
    rarity_meta["shiny"]["color"],
    rarity_meta["golden"]["color"],
}
AUTO_SPAWN_ROLE_ID = CELESTIAL_ROLES.as_spawn_ping


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
        debug_log(
            f"Skipping message {getattr(message, 'id', 'N/A')}: edited_at={bool(message.edited_at)}, embeds={len(getattr(message, 'embeds', []))}"
        )
        return

    embed = message.embeds[0]
    gif_url = embed.image.url if embed.image else None

    # Only proceed if the embed title indicates a wild spawn
    if not (embed.title and "A wild" in embed.title):
        debug_log(
            f"Skipping message {getattr(message, 'id', 'N/A')}: title does not match wild spawn pattern -> {getattr(embed, 'title', None)!r}"
        )
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
        debug_log(
            f"Parsed rarity from title: raw={raw_rarity_key}, normalized={rarity_key}, color={hex(rarity_color)}"
        )
    else:
        debug_log("No rarity emoji match found in embed title; using unknown rarity")

    # Extract Dex number from embed title emoji

    dex_match = re.search(r"<:([0-9]+):\d+>", embed.title)
    if dex_match:
        dex_number = int(dex_match.group(1))
        debug_log(f"Parsed dex number from title: {dex_number}")
    else:
        debug_log("No dex number emoji match found in embed title")

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
    debug_log(
        f"Spawn classification: pokemon={log_pokemon_name}, paldean={bool(is_paldean)}, legendary_or_rare={bool(is_legendary_or_rare)}, embed_color={getattr(getattr(embed, 'color', None), 'value', None)}"
    )

    # -------------------- Regular auto-spawn --------------------
    if not (is_paldean or is_legendary_or_rare):
        # Only ping AS Channel channel
        emoji = rarity_info.get("emoji", "❓")
        AUTO_SPAWN_ROLE_MENTION = f"<@&{AUTO_SPAWN_ROLE_ID}>"
        content = (
            f"{AUTO_SPAWN_ROLE_MENTION} A wild {emoji} {pokemon_name} has appeared!"
        )
        debug_log(
            f"Sending regular auto-spawn ping to channel_id={getattr(message.channel, 'id', 'N/A')} with role_id={AUTO_SPAWN_ROLE_ID}"
        )

        await send_webhook(
            bot=bot,
            channel=message.channel,
            content=content,
        )
        pretty_log(
            message=f"Auto-spawn ping sent: {log_pokemon_name} in #{message.channel.name}",
            tag="sent",
        )

        return

    # -------------------- Rare / shiny / Paldean spawn --------------------

    mention_role = f"<@&{CELESTIAL_ROLES.as_rarespawn_ping}>"

    content = f"{mention_role} A wild {shiny_text}{rarity_info.get('emoji', '❓')} {pokemon_name} has appeared!"
    debug_log(
        f"Sending rare/paldean ping to channel_id={getattr(message.channel, 'id', 'N/A')} with role_id={CELESTIAL_ROLES.as_rarespawn_ping}"
    )

    await send_webhook(
        bot=bot,
        channel=message.channel,
        content=content,
    )
    pretty_log(
        message=f"Rare spawn ping sent: {shiny_text}{log_pokemon_name} in #{message.channel.name}",
        tag="sent",
    )

    # Send embed to rare spawn channel
    has_market_value = False
    try:
        market_value_info = fetch_pokemon_cache_entry(log_pokemon_name or "Unknown")
        debug_log(
            f"Market cache lookup for {log_pokemon_name or 'Unknown'} returned type={type(market_value_info).__name__}"
        )
        current_listing_price = None
        last_seen = None
        if not market_value_info or not isinstance(market_value_info, dict):
            pretty_log(
                message=f"Market value not found for {log_pokemon_name or 'Unknown'}",
                tag="info",
            )
            debug_log(f"No usable market value info for {log_pokemon_name or 'Unknown'}")
        else:
            current_listing_price = market_value_info.get("current_listing")
            last_seen = market_value_info.get("listing_seen", "N/A")
            if current_listing_price is not None and current_listing_price != 0:
                has_market_value = True
            debug_log(
                f"Market value parsed: current_listing={current_listing_price}, last_seen={last_seen}, has_market_value={has_market_value}"
            )

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

        rare_spawn_channel_id = CELESTIAL_TEXT_CHANNELS.rare_spawns
        rare_spawn_channel = getattr(message.guild, "get_channel", lambda x: None)(
            rare_spawn_channel_id
        ) or bot.get_channel(rare_spawn_channel_id)
        debug_log(
            f"Resolved rare spawn channel from cache: found={bool(rare_spawn_channel)}, channel_id={rare_spawn_channel_id}"
        )

        # Fallback fetch for cache-miss cases where get_channel returns None.
        if not rare_spawn_channel and message.guild:
            try:
                rare_spawn_channel = await message.guild.fetch_channel(
                    rare_spawn_channel_id
                )
                debug_log(
                    f"Fetched rare spawn channel via API: found={bool(rare_spawn_channel)}, channel_id={rare_spawn_channel_id}"
                )
            except Exception as e:
                pretty_log(
                    tag="error",
                    message=f"Failed to fetch rare spawn channel ({rare_spawn_channel_id}): {e}",
                )
                debug_log(
                    f"API fetch failed for rare spawn channel_id={rare_spawn_channel_id}: {e}"
                )

        if rare_spawn_channel:
            pretty_log(
                tag="info",
                message=f"Attempting rare spawn embed send to #{rare_spawn_channel.name} ({rare_spawn_channel.id})",
            )

            sent_to_rare_channel = False
            try:
                await send_webhook(
                    bot=bot,
                    channel=rare_spawn_channel,
                    embed=rare_spawn_embed,
                )
                sent_to_rare_channel = True
                debug_log(
                    f"Rare spawn embed sent via webhook to channel_id={getattr(rare_spawn_channel, 'id', 'N/A')}"
                )
                pretty_log(
                    message=f"Rare spawn embed sent to #{rare_spawn_channel.name} via webhook",
                    tag="sent",
                )
            except Exception as e:
                pretty_log(
                    tag="error",
                    message=f"Webhook send failed for rare spawn embed ({log_pokemon_name}) in #{rare_spawn_channel.name}: {e}",
                )
                debug_log(f"Webhook send failed for rare spawn embed: {e}")

            if not sent_to_rare_channel:
                try:
                    await rare_spawn_channel.send(embed=rare_spawn_embed)
                    debug_log(
                        f"Rare spawn embed sent via direct fallback to channel_id={getattr(rare_spawn_channel, 'id', 'N/A')}"
                    )
                    pretty_log(
                        message=f"Rare spawn embed sent to #{rare_spawn_channel.name} via direct channel send fallback",
                        tag="sent",
                    )
                except Exception as e:
                    pretty_log(
                        tag="error",
                        message=f"Direct send fallback failed for rare spawn embed ({log_pokemon_name}) in #{rare_spawn_channel.name}: {e}",
                    )
                    debug_log(f"Direct fallback send failed for rare spawn embed: {e}")
        else:
            debug_log(
                f"Rare spawn channel unresolved for channel_id={rare_spawn_channel_id}; skipping embed send"
            )
            pretty_log(
                tag="warn",
                message=f"Rare spawn channel not found in guild cache/API (ID: {rare_spawn_channel_id})",
            )
        if not has_market_value:
            debug_log(
                f"Skipping value embed for {log_pokemon_name or 'Unknown'} because has_market_value=False"
            )
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
        debug_log(
            f"Sending value embed to original channel_id={getattr(message.channel, 'id', 'N/A')} with listing={current_listing_price}"
        )
        await send_webhook(
            bot=bot,
            channel=message.channel,
            embed=value_embed,
        )
        pretty_log(
            message=f"Value embed sent to #{message.channel.name} for {log_pokemon_name or 'Unknown'} with listing price {current_listing_price_formatted}",
            tag="sent",
        )
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Error processing rare spawn embed for {log_pokemon_name or 'Unknown'}: {e}",
        )
        debug_log(f"Exception in rare spawn embed processing: {e}")
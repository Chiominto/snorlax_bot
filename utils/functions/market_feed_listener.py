import re

import discord
from discord import Embed

from constants.aesthetics import Emojis
from constants.paldea_galar_dict import (
    Legendary_icon_url,
    get_rarity_by_color,
    icon_url_map,
    paldean_mons,
)
from constants.shellshuckle_constants import (
    SHELLSHUCKLE_ROLES,
    SHELLSHUCKLE_TEXT_CHANNELS,
)
from utils.cache.cache_list import (
    _market_alert_index,
    market_alert_cache,
    pokemon_cache,
    processed_market_feed_message_ids,
    processed_snipe_ids,
)
from utils.db.pokemons_db import update_market_value
from utils.functions.webhook_func import send_webhook
from utils.logs.debug_log import debug_log, enable_debug
from utils.logs.pretty_log import pretty_log

PokeCoin = Emojis.pokecoin
ALLOWED_WEBHOOKS = {
    1490890393816924341,  # Shiny
    1490891825597255700,  # Regular
    1490893743111405638,  # Legendary
    1490889694118940672,  # Golden
}
SNIPE_MAP = {
    "common": {"role": SHELLSHUCKLE_ROLES.common_snipe},
    "uncommon": {"role": SHELLSHUCKLE_ROLES.uncommon_snipe},
    "rare": {"role": SHELLSHUCKLE_ROLES.rare_snipe},
    "superrare": {"role": SHELLSHUCKLE_ROLES.super_rare_snipe},
    "legendary": {"role": SHELLSHUCKLE_ROLES.legendary_snipe},
    "shiny": {"role": SHELLSHUCKLE_ROLES.shiny_snipe},
    "golden": {"role": SHELLSHUCKLE_ROLES.golden_snipe},
    "gmax": {"role": SHELLSHUCKLE_ROLES.gigantamax_snipe},
    "mega": {"role": SHELLSHUCKLE_ROLES.mega_snipe},
    "event_exclusive": {"role": SHELLSHUCKLE_ROLES.exclusive_snipe},
}
enable_debug(f"{__name__}.process_market_feed_message")
enable_debug(f"{__name__}.snipe_handler")
def determine_rarity_from_name_and_author_icon(
    poke_name: str, author_icon_url: str, embed_color: int
) -> str:
    rarity = get_rarity_by_color(embed_color)
    if rarity == "golden":
        if "mega " in poke_name.lower():
            rarity = "golden mega"
    if rarity == "unknown":
        if "shiny mega " in poke_name.lower():
            rarity = "shiny mega"
        elif (
            "shiny gigantamax-" in poke_name.lower()
            or "shiny eternamax-" in poke_name.lower()
        ):
            rarity = "shiny gigantamax"
        elif "shiny" in poke_name.lower():
            rarity = "shiny"
        elif "mega" in poke_name.lower():
            rarity = "mega"
        elif "gigantamax-" in poke_name.lower() or "eternamax-" in poke_name.lower():
            rarity = "gigantamax"
        elif author_icon_url == Legendary_icon_url:
            rarity = "legendary"
    return rarity


async def snipe_handler(
    bot: discord.Client,
    poke_name: str,
    listed_price: int,
    id: str,
    lowest_market: int,
    amount: int,
    listing_seen: str,
    message: discord.Message,
    embed: discord.Embed,
):
    debug_log(
        f"snipe_handler called for {poke_name} id={id} listed_price={listed_price} lowest_market={lowest_market}"
    )
    DEFAULT_COLOR = 0x0855FB
    embed_color = None
    if embed and hasattr(embed, "color") and embed.color is not None:
        # Defensive: Only access .value if it exists
        if hasattr(embed.color, "value"):
            embed_color = embed.color.value
    if embed_color is None:
        embed_color = DEFAULT_COLOR

    debug_log(f"embed_color resolved to {embed_color}")
    rarity = get_rarity_by_color(embed_color) if embed_color is not None else "unknown"
    debug_log(f"rarity resolved to {rarity}")
    second_snipe_rarity_role = None
    if rarity == "unknown":
        if "shiny" in poke_name.lower():
            rarity = "shiny"
        elif "mega" in poke_name.lower():
            rarity = "mega"
        elif "gigantamax-" in poke_name.lower() or "eternamax-" in poke_name.lower():
            rarity = "gmax"
        elif embed.author and embed.author.icon_url == Legendary_icon_url:
            rarity = "legendary"
        debug_log(f"rarity fallback resolved to {rarity}")
    elif rarity == "event_exclusive":
        icon_url = embed.author.icon_url
        if poke_name.title() in paldean_mons:
            second_rarity_role_id = SHELLSHUCKLE_ROLES.paldean_snipe
            second_snipe_rarity_role = message.guild.get_role(second_rarity_role_id)
            debug_log(f"paldean_snipe role resolved to {second_snipe_rarity_role}")
        else:
            second_snipe_rarity = icon_url_map.get(icon_url)
            if second_snipe_rarity:
                second_rarity_role_id = SNIPE_MAP.get(second_snipe_rarity, {}).get(
                    "role"
                )
                if second_rarity_role_id:
                    second_snipe_rarity_role = message.guild.get_role(
                        second_rarity_role_id
                    )
                    debug_log(
                        f"second_snipe_rarity_role from icon_url_map resolved to {second_snipe_rarity_role}"
                    )

    ping_role_id = SNIPE_MAP.get(rarity, {}).get("role")
    debug_log(f"ping_role_id resolved to {ping_role_id}")
    if ping_role_id:
        guild = message.guild
        role = guild.get_role(ping_role_id)
        snipe_channel = guild.get_channel(SHELLSHUCKLE_TEXT_CHANNELS.market_snipe)
        debug_log(f"role resolved to {role}, snipe_channel resolved to {snipe_channel}")
        # snipe_channel = guild.get_channel(STRAYMONS__TEXT_CHANNELS.test_snipe)
        if role and snipe_channel:
            display_pokemon_name = poke_name.title()
            if second_snipe_rarity_role:
                content = f"{role.mention} {second_snipe_rarity_role.mention} {display_pokemon_name} listed for {PokeCoin} {listed_price:,} each"
            else:
                content = f"{role.mention} {display_pokemon_name} listed for {PokeCoin} {listed_price:,} each"

            debug_log(f"content for snipe alert: {content}")
            # Check if lowest market is int or "?"
            if isinstance(lowest_market, int):
                lowest_market_str = f"{PokeCoin} {lowest_market:,}"
            else:
                lowest_market_str = f"{PokeCoin} {lowest_market}"

            debug_log(f"lowest_market_str resolved to {lowest_market_str}")
            # Build embed
            snipe_embed = Embed(color=embed_color)
            if embed.thumbnail:
                snipe_embed.set_thumbnail(url=embed.thumbnail.url)
            snipe_embed.set_author(
                name=embed.author.name, icon_url=embed.author.icon_url
            )
            snipe_embed.add_field(
                name="Buy Command (Android)", value=f";m b {id}", inline=False
            )
            snipe_embed.add_field(
                name="Buy Command (iPhone)", value=f"`;m b {id}`", inline=False
            )
            snipe_embed.add_field(name="ID", value=id, inline=True)
            snipe_embed.add_field(
                name="Listed Price", value=f"{PokeCoin} {listed_price:,}", inline=True
            )
            snipe_embed.add_field(name="Amount", value=amount, inline=True)
            snipe_embed.add_field(
                name="Lowest Market", value=lowest_market_str, inline=True
            )
            snipe_embed.add_field(name="Listing Seen", value=listing_seen, inline=True)
            snipe_embed.set_footer(
                text="Please check listing before purchase. 💤",
                icon_url=message.guild.icon.url,
            )
            # await snipe_channel.send(content=content, embed=snipe_embed)
            try:
                debug_log(f"Sending snipe alert to channel {snipe_channel.id}")
                await send_webhook(
                    bot,
                    snipe_channel,
                    content=content,
                    embed=snipe_embed,
                )
                pretty_log(
                    "snipe",
                    f"Sent snipe alert for {display_pokemon_name} to channel {snipe_channel.id}",
                )
            except Exception as e:
                debug_log(f"Failed to send snipe alert: {e}")
                pretty_log(
                    "error",
                    f"Failed to send snipe alert: {e}",
                )


async def process_market_feed_message(
    bot: discord.Client, message: discord.Message, market_category_id: int
):

    debug_log(
        f"process_market_feed_message called for message.id={message.id}, channel={getattr(message.channel, 'id', None)}"
    )
    if message.channel.category_id != market_category_id:
        debug_log(
            f"Skipping message.id={message.id}: wrong category_id {getattr(message.channel, 'category_id', None)}"
        )
        return
    if message.webhook_id not in ALLOWED_WEBHOOKS:
        debug_log(
            f"Skipping message.id={message.id}: webhook_id {message.webhook_id} not allowed"
        )
        return
    if not message.embeds:
        debug_log(f"Skipping message.id={message.id}: no embeds")
        return

    if message.id in processed_market_feed_message_ids:
        debug_log(f"Skipping message.id={message.id}: already processed")
        return
    processed_market_feed_message_ids.add(message.id)

    # Check every embed in the message for validity and extract data
    for embed in message.embeds:
        debug_log(f"Processing embed in message.id={message.id}")
        embed_author_name = embed.author.name if embed.author else ""
        match = re.match(r"(.+?)\s+#(\d+)", embed_author_name)
        if not match:
            debug_log(
                f"Skipping embed: author name format not matched: {embed_author_name}"
            )
            continue

        poke_name = match.group(1)
        poke_dex = int(match.group(2))

        fields = {f.name: f.value for f in embed.fields}
        listed_price_str = re.sub(r"<a?:\w+:\d+>", "", fields.get("Listed Price", "0"))
        match_price = re.search(r"(\d[\d,]*)", listed_price_str)
        listed_price = int(match_price.group(1).replace(",", "")) if match_price else 0
        lowest_market_str = re.sub(
            r"<a?:\w+:\d+>", "", fields.get("Lowest Market", "0")
        )
        lowest_market_match = re.search(r"(\d[\d,]*)", lowest_market_str)
        lowest_market = (
            int(lowest_market_match.group(1).replace(",", ""))
            if lowest_market_match
            else 0
        )
        listing_seen = fields.get("Listing Seen", "N/A")
        amount = fields.get("Amount", "1")
        embed_color = embed.color.value
        is_exclusive = True if embed_color == 0xEA260B else False
        author_icon_url = embed.author.icon_url if embed.author else None
        thumbnail_url = embed.thumbnail.url if embed.thumbnail else None
        original_id = fields.get("ID", "0")

        # Snipe detection: only process unprocessed IDs
        if original_id not in processed_snipe_ids:
            processed_snipe_ids.add(original_id)
            if lowest_market > 0 and listed_price <= lowest_market * 0.7:
                debug_log(
                    f"Snipe detected for {poke_name} #{poke_dex}: listed_price={listed_price}, lowest_market={lowest_market}"
                )
                pretty_log(
                    "snipe",
                    f"Detected snipe listing for {poke_name} #{poke_dex} at {listed_price} (lowest market: {lowest_market})",
                )
                await snipe_handler(
                    bot,
                    poke_name,
                    listed_price,
                    original_id,
                    lowest_market,
                    amount,
                    listing_seen,
                    message,
                    embed,
                )
            elif lowest_market == 0:
                debug_log(
                    f"Snipe detected for {poke_name} #{poke_dex}: listed_price={listed_price}, lowest_market unknown"
                )
                pretty_log(
                    "snipe",
                    f"Detected snipe listing for {poke_name} #{poke_dex} at {listed_price} (lowest market unknown)",

                )
                lowest_market = "?"
                await snipe_handler(
                    bot,
                    poke_name,
                    listed_price,
                    original_id,
                    lowest_market,
                    amount,
                    listing_seen,
                    message,
                    embed,
                )

        # 💎────────────────────────────────────────────
        #           🏪 Update Market Value Cache & DB
        # 💎────────────────────────────────────────────
        # Update market value cache with new listing data
        # Extract additional market data
        market_value_rarity = determine_rarity_from_name_and_author_icon(
            poke_name, author_icon_url, embed_color
        )
        debug_log(f"Determined market value rarity: {market_value_rarity}")
        pretty_log(
            "info",
            f"Determined market value rarity for {poke_name} #{poke_dex}: {market_value_rarity}",
        )
        poke_dex = int(poke_dex)
        lowest_market_str = re.sub(
            r"<a?:\w+:\d+>", "", fields.get("Lowest Market", "0")
        )
        lowest_market_match = re.search(r"(\d[\d,]*)", lowest_market_str)
        lowest_market = (
            int(lowest_market_match.group(1).replace(",", ""))
            if lowest_market_match
            else 0
        )

        listing_seen = fields.get("Listing Seen", "Unknown")
        # Only get the number in listing seen if it's the format of <t:unix_seconds:R>
        listing_seen_match = re.search(r"<t:(\d+):", listing_seen)
        if listing_seen_match:
            listing_seen = int(listing_seen_match.group(1))

        # Upsert into market value cache
        cache_key = poke_name.lower()

        # Get existing data to preserve true lowest price
        existing_data = pokemon_cache.get(cache_key, {})
        existing_lowest = existing_data.get("true_lowest", float("inf"))

        # Ensure all values are not None for min/max
        price_candidates = [listed_price, lowest_market, existing_lowest]
        price_candidates = [p for p in price_candidates if p is not None]
        if price_candidates:
            true_lowest = min(price_candidates)
        else:
            true_lowest = 0

        # Only update if we have a valid price (not 0)
        if true_lowest == float("inf") or true_lowest == 0:
            max_candidates = [listed_price, lowest_market]
            max_candidates = [p for p in max_candidates if p is not None]
            if max_candidates and max(max_candidates) > 0:
                true_lowest = max(max_candidates)
            else:
                true_lowest = 0

        # Only update DB if any value has changed
        cache_update = {
            "pokemon": poke_name,
            "dex_number": poke_dex,
            "lowest_market": lowest_market,
            "current_listing": listed_price,
            "true_lowest": true_lowest,
            "listing_seen": listing_seen,
            "image_link": thumbnail_url,
            "rarity": market_value_rarity,
        }
        prev = pokemon_cache.get(cache_key, {})
        needs_update = (
            prev.get("lowest_market") != lowest_market
            or prev.get("current_listing") != listed_price
            or prev.get("true_lowest") != true_lowest
            or prev.get("listing_seen") != listing_seen
            or prev.get("dex_number") != poke_dex
            or prev.get("image_link") != thumbnail_url
            or prev.get("rarity") != market_value_rarity
        )

        pokemon_cache[cache_key] = cache_update
        if needs_update:
            await update_market_value(
                bot=bot,
                pokemon_name=poke_name,
                dex_number=int(poke_dex),
                lowest_market=lowest_market,
                current_listing=listed_price,
                true_lowest=true_lowest,
                listing_seen=str(listing_seen),
                image_link=thumbnail_url,
                rarity=market_value_rarity,
            )
            pretty_log(
                "market_value",
                f"Updated market value for {poke_name} #{poke_dex}: listed_price={listed_price}, lowest_market={lowest_market}, true_lowest={true_lowest}, rarity={market_value_rarity}",
            )

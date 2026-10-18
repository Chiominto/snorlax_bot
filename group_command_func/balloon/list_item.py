import re
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from constants.aesthetics import *

from constants.server_currency import SHOP_COLOR
from utils.db.balloon_prizes_db import (add_balloon_prize,
                                        fetch_all_balloon_prizes,
                                        fetch_balloon_prize,
                                        fetch_total_stock_for_balloon)
from utils.functions.get_pokemon_gifs import get_pokemon_gif
from utils.functions.pokemon_func import (get_dex_number_by_name,
                                          get_display_name, get_rarity)
from utils.functions.pretty_defer import pretty_defer
from utils.logs.debug_log import debug_log, enable_debug
from utils.logs.pretty_log import pretty_log

# enable_debug(f"{__name__}.list_item_func")


def strip_emoji(item_name):
    # Remove Discord custom emoji (e.g., <...>) and leading emoji/spaces
    item_name = re.sub(r"^<[^>]+>\s*", "", item_name)
    item_name = re.sub(r"^[^a-zA-Z0-9#]+\s*", "", item_name)
    return item_name


async def list_item_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
):
    """List all items in a balloon."""
    # Defer the response
    loader = await pretty_defer(
        interaction=interaction,
        content=f"Fetching balloon items...",
        ephemeral=True,
    )

    # Fetch all balloon prizes from the database
    debug_log(f"Fetching all balloon prizes from the database...")
    balloon_prizes = await fetch_all_balloon_prizes(bot)
    if not balloon_prizes:
        await loader.error(content="No items found in any balloon.")
        return

    # Create dict for each balloon with list of items categorized by type (golden, shiny, legendary)
    categorized_balloons = {}

    def format_stocked_list(prizes_dict, filter_func):
        result = []
        for prize_name, prize_info in prizes_dict.items():
            item_name = get_display_name(prize_name)
            item_name_no_emoji = strip_emoji(item_name)
            # Use the raw prize_name for filtering, not the formatted name
            if filter_func(prize_name):
                stock = prize_info.get("stock", 1)
                if stock and stock > 1:
                    result.append(f"{stock} {item_name_no_emoji}")
                else:
                    result.append(item_name_no_emoji)
        return result

    balloon_item_counts = {}
    from utils.db.balloon_prizes_db import fetch_total_stock_for_balloon

    for balloon_name, prizes in balloon_prizes.items():
        debug_log(f"Balloon: {balloon_name} | prizes: {prizes}")
        # Fetch DB total for this balloon for debugging
        db_total = await fetch_total_stock_for_balloon(bot, balloon_name)
        debug_log(f"Balloon: {balloon_name} | DB total stock: {db_total}")
        already_categorized = set()

        def format_stocked_list_unique(prizes_dict, filter_func):
            result = []
            for prize_name, prize_info in prizes_dict.items():
                if prize_name in already_categorized:
                    continue
                rarity = get_rarity(prize_name)
                item_name = get_display_name(prize_name)
                item_name_no_emoji = strip_emoji(item_name)
                if filter_func(prize_name):
                    stock = prize_info.get("stock", 1)
                    if stock and stock > 1:
                        result.append(f"{stock} {item_name_no_emoji}")
                    else:
                        result.append(item_name_no_emoji)
                    already_categorized.add(prize_name)
            return result

        def is_legendary(n):
            rarity = get_rarity(n)
            return (
                rarity is not None
                and rarity.lower() == "legendary"
                and n not in already_categorized
            )

        def is_superrare(n):
            rarity = get_rarity(n)
            return (
                rarity is not None
                and rarity.lower() == "super rare"
                and n not in already_categorized
            )

        def is_rare(n):
            rarity = get_rarity(n)
            return (
                rarity is not None
                and rarity.lower() == "rare"
                and n not in already_categorized
            )

        def is_uncommon(n):
            rarity = get_rarity(n)
            return (
                rarity is not None
                and rarity.lower() == "uncommon"
                and n not in already_categorized
            )

        def is_common(n):
            rarity = get_rarity(n)
            return (
                rarity is not None
                and rarity.lower() == "common"
                and n not in already_categorized
            )

        def is_rock(n):
            return "rock" in n.lower() and n not in already_categorized

        categorized_balloons[balloon_name] = {
            "golden": format_stocked_list_unique(
                prizes, lambda n: "golden" in n.lower()
            ),
            "shiny gigantamax": format_stocked_list_unique(
                prizes, lambda n: "shiny gigantamax" in n.lower()
            ),
            "shiny mega": format_stocked_list_unique(
                prizes, lambda n: "shiny mega" in n.lower()
            ),
            "shiny": format_stocked_list_unique(
                prizes,
                lambda n: "shiny" in n.lower()
                and "gigantamax" not in n.lower()
                and "mega" not in n.lower(),
            ),
            "gigantamax": format_stocked_list_unique(
                prizes,
                lambda n: "gigantamax" in n.lower() and "shiny" not in n.lower(),
            ),
            "mega": format_stocked_list_unique(
                prizes,
                lambda n: "mega" in n.lower() and "shiny" not in n.lower(),
            ),
            "legendary": format_stocked_list_unique(prizes, is_legendary),
            "super rare": format_stocked_list_unique(prizes, is_superrare),
            "rare": format_stocked_list_unique(prizes, is_rare),
            "uncommon": format_stocked_list_unique(prizes, is_uncommon),
            "common": format_stocked_list_unique(prizes, is_common),
            "rock": format_stocked_list_unique(prizes, is_rock),
        }
        # Always count the total number of items in the balloon (sum of all stocks, including multiples)
        total_stock = sum(prize_info.get("stock", 1) for prize_info in prizes.values())
        debug_log(f"Balloon: {balloon_name} | Computed total stock: {total_stock}")
        for pname, pinfo in prizes.items():
            debug_log(f"  {pname}: stock={pinfo.get('stock', 1)}")
        balloon_item_counts[balloon_name] = total_stock
    # Now categorized_balloons is in the format:
    # {
    #   'box_1': {'golden': [...], 'shiny': [...], 'legendary': [...]},
    #   ...
    # }

    # Create embed
    embed = discord.Embed(
        title="Balloon Items",
        description="Here are the items currently in the balloons:",
        color=SHOP_COLOR,
    )
    total_all = sum(balloon_item_counts.values())
    for balloon_name, categories in categorized_balloons.items():
        count = balloon_item_counts.get(balloon_name, 0)
        field_name = f"**{balloon_name.title()} ({count})**"
        legendary_mons_str = (
            f"{Emojis.Legendary}" + (", ".join(categories["legendary"]))
            if categories["legendary"]
            else ""
        )
        mega_mons_str = (
            f"{Emojis.Mega}" + (", ".join(categories["mega"]))
            if categories["mega"]
            else ""
        )
        gigantamax_mons_str = (
            f"{Emojis.gigantamax}" + (", ".join(categories["gigantamax"]))
            if categories["gigantamax"]
            else ""
        )
        shiny_mons_str = (
            f"{Emojis.Shiny}" + (", ".join(categories["shiny"]))
            if categories["shiny"]
            else ""
        )
        shiny_mega_mons_str = (
            f"{Emojis.shinymega}" + (", ".join(categories["shiny mega"]))
            if categories["shiny mega"]
            else ""
        )
        shiny_gigantamax_mons_str = (
            f"{Emojis.shinygigantamax}" + (", ".join(categories["shiny gigantamax"]))
            if categories["shiny gigantamax"]
            else ""
        )
        golden_mons_str = (
            f"{Emojis.Golden}" + (", ".join(categories["golden"]))
            if categories["golden"]
            else ""
        )
        super_rare_mons_str = (
            f"{Emojis.Super_Rare}" + (", ".join(categories["super rare"]))
            if categories["super rare"]
            else ""
        )
        rare_mons_str = (
            f"{Emojis.Rare}" + (", ".join(categories["rare"]))
            if categories["rare"]
            else ""
        )
        uncommon_mons_str = (
            f"{Emojis.Uncommon}" + (", ".join(categories["uncommon"]))
            if categories["uncommon"]
            else ""
        )
        common_mons_str = (
            f"{Emojis.Common}" + (", ".join(categories["common"]))
            if categories["common"]
            else ""
        )
        rock_mons_str = (
            f"🪨" + (", ".join(categories["rock"])) if categories["rock"] else ""
        )
        field_value = "\n".join(
            filter(
                None,
                [
                    golden_mons_str,
                    shiny_gigantamax_mons_str,
                    shiny_mega_mons_str,
                    shiny_mons_str,
                    gigantamax_mons_str,
                    mega_mons_str,
                    legendary_mons_str,
                    super_rare_mons_str,
                    rare_mons_str,
                    uncommon_mons_str,
                    common_mons_str,
                    rock_mons_str,
                ],
            )
        )
        embed.add_field(name=field_name, value=field_value, inline=False)
    embed.set_footer(text=f"Total number of all items: {total_all}")
    await loader.success(content="", embed=embed)

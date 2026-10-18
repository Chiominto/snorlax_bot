from datetime import datetime

import discord
from discord.ext import commands

from constants.server_currency import CURRENCY_EMOJI, CURRENCY_NAME, SHOP_COLOR
from utils.cache.cache_list import server_shop_cache
from utils.db.server_shop_db import (format_item_name, remove_all_items,
                                     remove_item)
from utils.functions.pretty_defer import pretty_defer
from utils.functions.role_checks import *
from utils.functions.webhook_func import send_webhook_log
from utils.logs.pretty_log import pretty_log

from .buy import fetch_dex


async def remove_item_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    item_name: str,
):
    """
    Remove an item from the server shop.
    """
    # Defer the interaction to allow more time for processing
    loader = await pretty_defer(
        interaction=interaction,
        content="Removing item from server shop...",
        ephemeral=True,
    )
    # Check if user is a staff member
    if not is_staff_member(interaction.user):
        await loader.error("You do not have permission to use this command.")
        return

    # Check if item exists
    from utils.cache.server_shop_cache import fetch_item_id_by_name

    item_id = fetch_item_id_by_name(item_name)
    if not item_id:
        await loader.error(
            f"No item with the name '{item_name}' exists in the server shop."
        )
        return

    # Get item details for logging
    item_info = server_shop_cache.get(item_id)
    if not item_info:
        await loader.error(
            "Failed to retrieve item details from cache. Please try again later."
        )
        return
    price = item_info.get("price", 0)
    stock = item_info.get("stock", 0)
    description = item_info.get("description", "No description.")
    image_link = item_info.get("image_link")
    dex = item_info.get("dex")
    if not dex:
        dex = await fetch_dex(
            bot=bot,
            item_name=item_name,
            item_id=item_id,
        )
    if dex and dex != "N/A":
        has_dex = True
    else:
        has_dex = False

    # Remove the item from the database
    await remove_item(bot=bot, item_id=item_id)
    item_name = format_item_name(item_name)
    item_name = f"{item_name} (Dex: #{dex})" if has_dex else item_name
    # Sucess embed
    desc = (
        f"**Item Name:** {item_name}\n"
        f"**Price:** {price} {CURRENCY_EMOJI}\n"
        f"**Stock:** {stock}\n"
        f"**Description:** {description}\n"
    )
    embed = discord.Embed(
        title="Item Removed from Server Shop",
        description=desc,
        color=SHOP_COLOR,
        timestamp=datetime.now(),
    )
    embed.set_author(
        name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url
    )
    embed.set_footer(
        text=f"Item ID: {item_id}",
        icon_url=interaction.guild.icon.url if interaction.guild else None,
    )
    if image_link:
        embed.set_thumbnail(url=image_link)

    await loader.success(embed=embed, content="")
    pretty_log(
        "info",
        f"Removed item from server shop: {item_name} (ID: {item_id})",
    )

    # Send webhook log
    await send_webhook_log(
        bot=bot,
        embed=embed,
    )


async def shop_clear_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
):
    """
    Remove all items from the server shop.
    """
    # Defer the interaction to allow more time for processing
    loader = await pretty_defer(
        interaction=interaction,
        content="Clearing all items from server shop...",
        ephemeral=True,
    )
    # Check if user is a staff member
    if not is_staff_member(interaction.user):
        await loader.error("You do not have permission to use this command.")
        return

    # Fetch all items to check if shop is already empty
    from utils.cache.server_shop_cache import fetch_all_shop_items_cache

    all_items = fetch_all_shop_items_cache()
    if not all_items:
        await loader.error("The server shop is already empty.")
        return
    item_count = len(all_items)

    # Remove all items from the database
    await remove_all_items(bot=bot)

    # Success embed
    embed = discord.Embed(
        timestamp=datetime.now(),
        title="All Items Removed from Server Shop",
        color=SHOP_COLOR,
        description=f"Successfully removed {item_count} items from the server shop.",
    )
    embed.set_author(
        name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url
    )

    await loader.success(embed=embed, content="")
    pretty_log(
        "info",
        "Cleared all items from server shop.",
    )

    # Send webhook log
    await send_webhook_log(
        bot=bot,
        embed=embed,
    )

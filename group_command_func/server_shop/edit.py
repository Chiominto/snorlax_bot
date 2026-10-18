from datetime import datetime

import discord
from discord.ext import commands

from constants.server_currency import CURRENCY_EMOJI, CURRENCY_NAME, SHOP_COLOR
from utils.cache.cache_list import server_shop_cache
from utils.db.server_shop_db import format_item_name, update_item
from utils.functions.pretty_defer import pretty_defer
from utils.functions.role_checks import *
from utils.functions.webhook_func import send_webhook_log
from utils.logs.pretty_log import pretty_log

from .buy import fetch_dex


async def edit_item_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    item_name: str,
    new_price: int = None,
    new_stock: int = None,
    new_description: str = None,
    new_image_link: str = None,
):
    """
    Edit an existing item in the server shop.
    """

    # Defer the interaction to allow more time for processing
    loader = await pretty_defer(
        interaction=interaction,
        content="Editing item in server shop...",
        ephemeral=True,
    )

    # Check if user is a staff member
    if not is_staff_member(interaction.user):
        await loader.error("You do not have permission to use this command.")
        return

    # Check if there are fields to update
    if (
        new_price is None
        and new_stock is None
        and new_description is None
        and new_image_link is None
    ):
        await loader.error("No new values provided to update the item.")
        return

    # Check if item exists
    from utils.cache.server_shop_cache import fetch_item_id_by_name

    item_id = fetch_item_id_by_name(item_name)
    if not item_id:
        await loader.error(
            f"No item with the name '{item_name}' exists in the server shop."
        )
        return
    # Get current item details for logging
    item_info = server_shop_cache.get(item_id)
    if not item_info:
        await loader.error(
            "Failed to retrieve item details from cache. Please try again later."
        )
        return
    current_price = item_info.get("price", 0)
    current_stock = item_info.get("stock", 0)
    current_description = item_info.get("description", "No description.")
    current_image_link = item_info.get("image_link")
    dex = item_info.get("dex")
    if not dex:
        dex = await fetch_dex(
            bot=bot,
            item_name=item_name,
            item_id=item_id,
        )

    # Update the item in the database
    await update_item(
        bot=bot,
        item_id=item_id,
        price=new_price,
        stock=new_stock,
        description=new_description,
        image_link=new_image_link,
    )
    pretty_log(
        "info",
        f"Edited item '{item_name}' (ID: {item_id}) in server shop.",
        label="Edit Server Shop Item",
    )
    # Success embed
    if dex and dex != "N/A":
        has_dex = True
    else:
        has_dex = False
    item_name = format_item_name(item_name)
    item_name = f"{item_name} (Dex: #{dex})" if has_dex else item_name
    desc = f"**Item Name:** {item_name}\n**ID:** {item_id}\n"
    embed = discord.Embed(
        timestamp=datetime.now(),
        title="Item Edited in Server Shop",
        color=SHOP_COLOR,
        description=desc,
    )
    if new_price is not None:
        value_str = f"> - **Old:** {current_price} {CURRENCY_EMOJI}\n> - **New:** {new_price} {CURRENCY_EMOJI}"
        embed.add_field(name="Price", value=value_str, inline=False)
    if new_stock is not None:
        value_str = f"> - **Old:** {current_stock}\n> - **New:** {new_stock}"
        embed.add_field(name="Stock", value=value_str, inline=False)
    if new_description is not None:
        value_str = (
            f"> - **Old:** {current_description}\n> - **New:** {new_description}"
        )
        embed.add_field(name="Description", value=value_str, inline=False)
    if new_image_link is not None:
        value_str = f"> - **Old:** {current_image_link}\n> - **New:** {new_image_link}"
        embed.add_field(name="Image Link", value=value_str, inline=False)

    if new_image_link:
        embed.set_thumbnail(url=new_image_link)
    elif current_image_link is not None:
        embed.set_thumbnail(url=current_image_link)

    await loader.success(embed=embed, content="")
    pretty_log(
        "info",
        f"Edited item in server shop: {item_name} (ID: {item_id})",
    )
    # Send in action log channel
    await send_webhook_log(
        bot=bot,
        embed=embed,
    )

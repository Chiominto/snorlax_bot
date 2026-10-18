import re
from datetime import datetime

import discord
from discord.ext import commands

from constants.celestial_constants import CELESTIAL_TEXT_CHANNELS
from constants.server_currency import SHOP_COLOR
from utils.db.balloon_prizes_db import (fetch_balloon_prize_with_balloon,
                                        remove_balloon_prize)
from utils.db.server_shop_db import fetch_item_by_name, update_stock
from utils.functions.pokemon_func import get_display_name
from utils.functions.pretty_defer import pretty_defer
from utils.logs.pretty_log import pretty_log

from .multi_add_item import get_dart_name_and_price, log_event


async def remove_item_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    balloon_name: str,
    item_name: str,
):
    """Remove an item from a box in the database."""
    # Defer the response
    loader = await pretty_defer(
        interaction=interaction,
        content=f"Removing {item_name} from {balloon_name}...",
        ephemeral=False,
    )

    #  Check if the item exists in the box
    existing_prize = await fetch_balloon_prize_with_balloon(
        bot, balloon_name=balloon_name, prize=item_name
    )

    if not existing_prize:
        await loader.error(content=f"{item_name} is not in {balloon_name}.")
        return

    # Get data for the item to be removed (for logging purposes)
    dex = existing_prize.get("dex")
    image_link = existing_prize.get("image_link")
    stock = existing_prize.get("stock")

    # Get dart name to decrease stock by existing prize's stock
    dart_name, _ = get_dart_name_and_price(balloon_name)
    dart_info = await fetch_item_by_name(bot, item_name=dart_name)
    if not dart_info:
        await loader.error(
            content=f"Associated dart '{dart_name}' not found for {balloon_name}. Cannot update stock."
        )
        return

    dart_id = dart_info.get("id") if dart_info else None
    dart_stock = dart_info.get("stock") if dart_info else None
    new_dart_stock = dart_stock - stock if dart_stock is not None and stock is not None else None


    # Remove the item from the box in the database
    try:
        await remove_balloon_prize(bot=bot, balloon_name=balloon_name, prize=item_name)
        pretty_log(
            tag="info",
            message=f"✅ Successfully removed item '{item_name}' from box '{balloon_name}'.",
            label="🎁 BALLOON PRIZE",
        )
        # Decrease the stock of the corresponding dart by the stock of the removed item
        if dart_id and stock:
            await update_stock(bot=bot, item_id=dart_id, new_stock=new_dart_stock)
            pretty_log(
                tag="info",
                message=(
                    f"Updated stock for associated dart '{dart_name}' (ID: {dart_id}): "
                    f"{dart_stock} -> {new_dart_stock}"
                ),
                label="🎁 BALLOON PRIZE",
            )
    except Exception as e:
        pretty_log(
            tag="warn",
            message=f"⚠️ Failed to remove item '{item_name}' from box '{balloon_name}': {e}",
            label="🎁 BALLOON PRIZE",
        )
        await loader.error(content=f"Failed to remove {item_name} from {balloon_name}.")
        return

    # Build success embed
    display_name = get_display_name(item_name, dex=True)
    embed = discord.Embed(
        title=f"Item Removed",
        description=(
            f"**Item Name:** {display_name}\n"
            f"**Balloon Name:** {balloon_name}\n"
            f"**Dex Number:** {dex}\n"
            f"**Stock:** {stock}\n"
        ),
        color=SHOP_COLOR,
        timestamp=datetime.now(),
    )
    embed.set_author(
        name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url
    )
    embed.set_thumbnail(url=image_link)
    await loader.success(content="", embed=embed)

    # Send webhook notification
    log_channel = interaction.guild.get_channel(CELESTIAL_TEXT_CHANNELS.server_logs)
    await log_event(bot=bot, embed=embed, channel=log_channel)

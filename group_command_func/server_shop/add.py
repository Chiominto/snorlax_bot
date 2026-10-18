from datetime import datetime

import discord
from discord.ext import commands

from constants.celestial_constants import CELESTIAL_TEXT_CHANNELS
from constants.server_currency import CURRENCY_EMOJI, CURRENCY_NAME, SHOP_COLOR
from utils.cache.cache_list import server_shop_cache
from utils.db.server_shop_db import format_item_name, upsert_item
from utils.functions.get_pokemon_gifs import get_pokemon_gif
from utils.functions.pokemon_func import get_dex_number_by_name
from utils.functions.pretty_defer import pretty_defer
from utils.functions.role_checks import *
from utils.functions.webhook_func import send_webhook_log
from utils.logs.pretty_log import pretty_log


async def add_item_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    item_name: str,
    price: int,
    stock: int,
    description: str = None,
    image_link: str = None,
):
    """
    Add or update an item in the server shop.
    """

    # Defer the interaction to allow more time for processing
    loader = await pretty_defer(
        interaction=interaction,
        content="Adding item to server shop...",
        ephemeral=False,
    )
    # Check if user is a staff member
    if not is_staff_member(interaction.user):
        await loader.error("You do not have permission to use this command.")
        return

    # Check if item already exists
    existing_item = None
    from utils.cache.server_shop_cache import fetch_item_id_by_name

    item_name = item_name.strip().title()

    item_id = fetch_item_id_by_name(item_name)
    if item_id:
        await loader.error(
            f"An item with the name '{item_name}' already exists in the server shop."
        )
        return

    # Try to fetch gif if no image link provided
    if not image_link:
        gif_url = get_pokemon_gif(item_name)
        if gif_url:
            image_link = gif_url
    # Get Dex number if applicable
    dex_number = get_dex_number_by_name(item_name)

    # Upsert the item in the database
    item_id = await upsert_item(
        bot=bot,
        item_name=item_name,
        price=price,
        stock=stock,
        description=description,
        image_link=image_link,
        dex=dex_number,
    )
    if not item_id:
        await loader.error(
            "Failed to add the item to the server shop. Please try again later."
        )
        return
    if dex_number and dex_number != "N/A":
        has_dex = True
    else:
        has_dex = False
    item_name = format_item_name(item_name)
    dex_str = f"**Dex Number:** {dex_number}\n" if has_dex else ""
    # Success embed
    embed = discord.Embed(
        title="Item Added to Server Shop",
        color=SHOP_COLOR,
        timestamp=datetime.now(),
        description=(
            f"**Name:** {item_name}\n"
            f"{dex_str}"
            f"**Price:** {price} {CURRENCY_EMOJI}\n"
            f"**Stock:** {stock}\n"
            f"**Description:** {description if description else 'No description provided.'}"
        ),
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
        f"Added new item to server shop: {item_name} (ID: {item_id})",
        label="Server Shop",
    )
    # Send in action log channel
    await send_webhook_log(
        bot=bot,
        embed=embed,
    )

    # send in offtopic
    offtopic_channel = interaction.guild.get_channel(CELESTIAL_TEXT_CHANNELS.off_topic)
    if offtopic_channel:
        await offtopic_channel.send(embed=embed)

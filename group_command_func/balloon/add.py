import re
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from constants.celestial_constants import CELESTIAL_TEXT_CHANNELS
from constants.server_currency import (SHOP_COLOR, CURRENCY_EMOJI, ROCK_EMOJI,
                                       ROCK_IMAGE_LINK, mc_dart_balloons,
                                       nugget_launcher_balloons)
from utils.cache.global_flags import TESTING_BURGER_SHOP_EVENT
from utils.db.balloon_prizes_db import (add_balloon_prize, fetch_balloon_prize,
                                        fetch_balloon_prize_with_balloon)
from utils.db.server_shop_db import (fetch_item_by_name, update_stock,
                                     upsert_item)
from utils.functions.get_pokemon_gifs import get_pokemon_gif
from utils.functions.pokemon_func import (get_dex_number_by_name,
                                          get_display_name)
from utils.functions.pretty_defer import pretty_defer
from utils.logs.debug_log import debug_log, enable_debug
from utils.logs.pretty_log import pretty_log

from .multi_add_item import get_dart_name_and_price, log_event

enable_debug(f"{__name__}.add_item_func")


async def add_item_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    balloon_name: str,
    item_name: str,
    stock: int = 1,
):
    balloon_name = balloon_name.lower()
    is_rock = item_name.lower() == "rock"
    debug_log(
        f"add_item_func called with balloon_name='{balloon_name}', item_name='{item_name}', stock={stock}"
    )
    # Defer
    loader = await pretty_defer(
        interaction=interaction,
        content=f"Adding item to {balloon_name.title()}...",
        ephemeral=False,
    )
    dart_name, dart_prize = get_dart_name_and_price(balloon_name)
    debug_log(f"Dart name: {dart_name}, Dart prize: {dart_prize}")

    # Check if dart exists
    existing_dart = await fetch_item_by_name(bot, item_name=dart_name)
    debug_log(f"Existing dart: {existing_dart}")
    if not existing_dart:
        # Upsert dart in the database if it doesn't exist
        try:
            dart_id = await upsert_item(
                bot=bot,
                item_name=dart_name,
                price=dart_prize,
                stock=0,
                image_link=None,
                description=None,
                dex=None,
            )
            pretty_log(
                tag="info",
                message=f"Created new dart '{dart_name}' in server shop with ID {dart_id}.",
                label="🎁 BALLOON PRIZE DB",
            )
            debug_log(f"Created new dart '{dart_name}' with ID {dart_id}")
        except Exception as e:
            pretty_log(
                tag="warn",
                message=f"⚠️ Failed to create dart '{dart_name}' in server shop: {e}",
                label="🎁 BALLOON PRIZE DB",
            )
            debug_log(f"Failed to create dart '{dart_name}': {e}")
            await loader.error(
                content=f"⚠️ Failed to create dart '{dart_name}' in server shop."
            )
            return
    # Add balloon prize to the database
    if not is_rock:
        dex = get_dex_number_by_name(item_name)
        image_link = get_pokemon_gif(item_name)
        display_name = get_display_name(item_name)
    else:
        dex = None
        image_link = ROCK_IMAGE_LINK
        display_name = f"{ROCK_EMOJI} Rock"

    debug_log(f"dex: {dex}, image_link: {image_link}, display_name: {display_name}")
    try:
        # Check if the item already exists in the box
        existing_prize = await fetch_balloon_prize_with_balloon(
            bot, balloon_name=balloon_name, prize=item_name
        )
        debug_log(f"existing_prize: {existing_prize}")
        if existing_prize:
            current_item_stock = existing_prize.get("stock", 0)
            new_item_stock = current_item_stock + stock
        else:
            new_item_stock = stock
        debug_log(f"new_item_stock: {new_item_stock}")
        await add_balloon_prize(
            bot=bot,
            balloon_name=balloon_name,
            prize=item_name,
            stock=new_item_stock,
            image_link=image_link,
            dex=dex,
        )
        pretty_log(
            tag="info",
            message=f"Added item '{item_name}' to balloon '{balloon_name}' with stock {new_item_stock}.",
            label="🎁 BALLOON PRIZE DB",
        )
        debug_log(
            f"Added item '{item_name}' to balloon '{balloon_name}' with stock {new_item_stock}"
        )
    except Exception as e:
        pretty_log(
            tag="warn",
            message=f"⚠️ Failed to add item '{item_name}' to balloon '{balloon_name}': {e}",
            label="🎁 BALLOON PRIZE DB",
        )
        debug_log(f"Failed to add item '{item_name}' to balloon '{balloon_name}': {e}")
        await loader.error(
            content=f"⚠️ Failed to add item '{item_name}' to balloon '{balloon_name}'.",
        )
        return
    # Update stock of the dart itself to reflect the new items added (sum all item stocks in the box)
    try:
        # Fetch all prizes in the box and sum their stock
        from utils.db.balloon_prizes_db import fetch_balloon_prizes_by_balloon

        balloon_total = []
        if dart_name.lower() == "nugget launcher dart":
            balloon_list = nugget_launcher_balloons
        else:
            balloon_list = mc_dart_balloons
        debug_log(f"balloon_list: {balloon_list}")
        for balloon in balloon_list:
            all_prizes = await fetch_balloon_prizes_by_balloon(
                bot, balloon_name=balloon
            )
            debug_log(f"all_prizes for balloon '{balloon}': {all_prizes}")
            if all_prizes:
                total_stock = sum(prize.get("stock", 1) for prize in all_prizes)
                debug_log(f"total_stock for balloon '{balloon}': {total_stock}")
                balloon_total.append(total_stock)
        total_stock = sum(balloon_total) if balloon_total else 0
        debug_log(f"total_stock for dart '{dart_name}': {total_stock}")
        # Change to dart
        existing_dart = await fetch_item_by_name(bot, item_name=dart_name)
        dart_id = existing_dart.get("item_id")
        debug_log(f"Updating dart '{dart_name}' (ID: {dart_id}) stock to {total_stock}")
        await update_stock(bot=bot, item_id=dart_id, stock=total_stock)
        # Success embed
        desc = (
            f"**Balloon Name:** {balloon_name.title()}\n"
            f"**Item Added:** {display_name}\n"
            f"**Stock:** {new_item_stock}\n"
            f"**{dart_name} Stock:** {total_stock}"
        )
        embed = discord.Embed(
            title=f"Items Added to {balloon_name.title()}!",
            description=desc,
            color=SHOP_COLOR,
        )
        embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.display_avatar.url,
        )
        if image_link:
            embed.set_thumbnail(url=image_link)

        await loader.success(embed=embed, content="")
        debug_log(
            f"Successfully updated stock and sent success embed for '{balloon_name}'"
        )
    except Exception as e:
        pretty_log(
            tag="warn",
            message=f"⚠️ Failed to update stock for box '{balloon_name}' after adding items: {e}",
            label="🎁 BALLOON PRIZE DB",
        )
        debug_log(
            f"Failed to update stock for box '{balloon_name}' after adding items: {e}"
        )
        await loader.error(
            content=f"⚠️ Failed to update stock for box '{balloon_name}' after adding items."
        )
        return

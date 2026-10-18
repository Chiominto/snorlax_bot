import re
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands
from utils.functions.webhook_func import send_webhook
from constants.celestial_constants import CELESTIAL_TEXT_CHANNELS, CELESTIAL_VOICE_CHANNELS
from constants.server_currency import (SHOP_COLOR, CURRENCY_EMOJI, mc_dart_balloons,
                                       nugget_launcher_balloons)
from utils.cache.global_flags import TESTING_BURGER_SHOP_EVENT
from utils.db.balloon_prizes_db import (add_balloon_prize,
                                        fetch_all_balloon_prizes,
                                        fetch_balloon_prize,
                                        fetch_balloon_prize_with_balloon)
from utils.db.server_shop_db import (fetch_item_by_name, update_stock,
                                     upsert_item)
from utils.functions.get_pokemon_gifs import get_pokemon_gif
from utils.functions.pokemon_func import (get_dex_number_by_name,
                                          get_display_name)
from utils.functions.pretty_defer import pretty_defer
from utils.logs.debug_log import debug_log, enable_debug
from utils.logs.pretty_log import pretty_log

enable_debug(f"{__name__}.multi_add_item_func")

def get_dart_name_and_price(balloon_name: str):
    if balloon_name in nugget_launcher_balloons:
        return "Nugget Launcher Dart", 10
    else:
        return "McDart", 125


async def log_event(
    bot, embed: discord.Embed, channel: discord.TextChannel, context: str = "log_event"
):
    from group_command_func.server_shop.buy import is_event_ongoing

    """Log event changes to the designated log channel via webhook if logging is enabled."""
    if not is_event_ongoing():
        pretty_log(
            tag="debug",
            message="Event logging is currently disabled. Skipping log.",
            label="🎁 Event Log",
        )
        return
    if context == "add_item":
        pretty_log(
            tag="info",
            message="Not sending log to Discord channel because context is 'add_item' and we want to avoid spamming logs for every item added.",
            label="🎁 Event Log",
        )
        return  # Don't send logs

    if channel.id == CELESTIAL_TEXT_CHANNELS.burger_shop_log:
        guild = channel.guild
        clan_event_log_channel = guild.get_channel(CELESTIAL_TEXT_CHANNELS.burger_shop_log)
        if channel != clan_event_log_channel:
            log_channels = [channel, clan_event_log_channel]
        else:
            log_channels = [channel]
        for log_channel in log_channels:
            await send_webhook(
                channel=log_channel,
                embed=embed,
                bot=bot,
            )
    else:
        await send_webhook(
            channel=channel,
            embed=embed,
            bot=bot,
        )


async def multi_add_item_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    balloon_name: str,
    item_1: str,
    item_2: str = None,
    item_3: str = None,
    item_4: str = None,
    item_5: str = None,
    item_6: str = None,
    item_7: str = None,
    item_8: str = None,
    item_9: str = None,
    item_10: str = None,
):
    stock = 1
    balloon_name = balloon_name.lower()
    # Defer
    loader = await pretty_defer(
        interaction=interaction,
        content=f"Adding items to {balloon_name.title()}...",
        ephemeral=False,
    )
    dart_name, dart_prize = get_dart_name_and_price(balloon_name)

    # Check if dart exists
    existing_dart = await fetch_item_by_name(bot, item_name=dart_name)
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
        except Exception as e:
            pretty_log(
                tag="warn",
                message=f"⚠️ Failed to create dart '{dart_name}' in server shop: {e}",
                label="🎁 BALLOON PRIZE DB",
            )
            await loader.error(
                content=f"⚠️ Failed to create dart '{dart_name}' in server shop."
            )
            return

    # List of items to add
    items_to_add = [
        item_1,
        item_2,
        item_3,
        item_4,
        item_5,
        item_6,
        item_7,
        item_8,
        item_9,
        item_10,
    ]
    items_to_add = [item for item in items_to_add if item is not None]

    # Add each item to the box, incrementing stock by the number of times it appears
    from collections import Counter

    item_counts = Counter(items_to_add)
    for item_name, count in item_counts.items():
        dex = get_dex_number_by_name(item_name)
        image_link = get_pokemon_gif(item_name)
        # Debug log for dex and item_name
        pretty_log(
            tag="debug",
            message=f"About to add item: {item_name}, dex type: {type(dex)}, dex value: {dex}",
            label="🎁 BALLOON PRIZE DB",
        )
        try:
            # Check if the item already exists in the box
            existing_prize = await fetch_balloon_prize_with_balloon(
                bot, balloon_name=balloon_name, prize=item_name
            )
            if existing_prize:
                current_item_stock = existing_prize.get("stock", 0)
                new_item_stock = current_item_stock + count
            else:
                new_item_stock = count
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
        except Exception as e:
            pretty_log(
                tag="warn",
                message=f"⚠️ Failed to add item '{item_name}' to balloon '{balloon_name}': {e}",
                label="🎁 BALLOON PRIZE DB",
            )
            await loader.error(
                content=f"⚠️ Failed to add item '{item_name}' to balloon '{balloon_name}'."
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

        for balloon in balloon_list:
            all_prizes = await fetch_balloon_prizes_by_balloon(
                bot, balloon_name=balloon
            )
            if all_prizes:
                total_stock = sum(prize.get("stock", 1) for prize in all_prizes)
                balloon_total.append(total_stock)
        total_stock = sum(balloon_total) if balloon_total else 0

        # Change to dart
        existing_dart = await fetch_item_by_name(bot, item_name=dart_name)
        if not existing_dart:
            pretty_log(
                tag="warn",
                message=f"Associated dart '{balloon_name}' not found for {balloon_name}. Cannot update stock.",
                label="🎁 BALLOON PRIZE DB",
            )
            await loader.error(
                content=f"Associated dart '{balloon_name}' not found for {balloon_name}. Cannot update stock."
            )
            return
        dart_id = existing_dart.get("item_id")
        pretty_log(
            tag="debug",
            message=f"Updating stock for dart '{dart_name}' (ID: {dart_id}) to {total_stock} based on total items in balloon '{balloon_name}'.",
            label="🎁 BALLOON PRIZE DB"
            ),
        await update_stock(bot=bot, item_id=dart_id, stock=total_stock)

        # Success embed
        desc = (
            f"**Balloon Name:** {balloon_name.title()}\n"
            f"**Items Added:** {', '.join(items_to_add)}\n"
            f"**Total Items in Balloon:** {total_stock}\n"
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
        await loader.success(embed=embed, content="")
    except Exception as e:
        pretty_log(
            tag="warn",
            message=f"⚠️ Failed to update stock for box '{balloon_name}' after adding items: {e}",
            label="🎁 BALLOON PRIZE DB",
        )
        await loader.error(
            content=f"⚠️ Failed to update stock for box '{balloon_name}' after adding items."
        )
        return

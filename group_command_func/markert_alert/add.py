import discord
from discord.ext import commands

from constants.aesthetics import Emojis
from constants.celestial_constants import KHY_USER_ID
from utils.cache.cache_list import market_alert_cache
from utils.db.market_alert_db import insert_market_alert
from utils.functions.design_embed import design_embed
from utils.functions.parsers import parse_compact_number
from utils.functions.pokemon_func import get_display_name,get_dex_number_by_name, is_mon_in_game
from utils.functions.pretty_defer import pretty_defer
from utils.logs.debug_log import debug_log, enable_debug
from utils.logs.pretty_log import pretty_log
from utils.logs.server_log import send_log_to_server_log


# Add a market alert for a user
async def add_market_alert_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    pokemon: str,
    max_price: str,
    channel: discord.TextChannel,
    ping: str,
):
    """
    Adds a market alert for a user.
    """
    # Log pokemon
    pretty_log(
        "info",
        f"Attempting to add market alert for Pokemon input '{pokemon}' by user {interaction.user.name} (ID: {interaction.user.id})",
        label="MARKET ALERT ADD",
    )
    from utils.cache.market_alert_cache import (
        check_if_user_has_market_alert_roles,
        determine_total_market_alerts_for_user,
        get_user_total_market_alerts_from_cache,
    )

    try:
        # Initialize loader
        loader = await pretty_defer(
            interaction=interaction,
            content="Setting up your market alert...",
            ephemeral=False,
        )
        user = interaction.user
        user_id = user.id
        user_name = user.name
        guild = interaction.guild

        # Check if user has special role
        has_role, role_error_message = check_if_user_has_market_alert_roles(user)
        if not has_role:
            await loader.error(role_error_message)
            return
        # Check user's current total alerts against their max allowed alerts
        total_alerts = get_user_total_market_alerts_from_cache(user_id)
        max_alerts = determine_total_market_alerts_for_user(user)
        if total_alerts >= max_alerts:
            await loader.error(
                f"You have reached your maximum number of market alerts ({total_alerts}/{max_alerts}). Please delete an existing alert before adding a new one."
            )
            return

        ping = True if ping.lower() == "yes" else False

        # Validate max price
        parse_price = parse_compact_number(max_price)
        if not parse_price:
            await loader.error(
                content="Invalid max price. Use formats like '1000', '1k', '1.5m'. Max is 10 billion.",
            )
            return
        max_price = int(parse_price)

        # Get dex number and validate pokemon
        if not is_mon_in_game(pokemon):
            await loader.error(
                content=f"'{pokemon}' is not a valid Pokémon name.",
            )
            return
        dex_number = get_dex_number_by_name(pokemon)
        target_name = pokemon.lower()

        # Insert market alert into database
        try:
            await insert_market_alert(
                bot=bot,
                user_id=user_id,
                user_name=user_name,
                pokemon=target_name.lower(),
                dex=dex_number,
                max_price=max_price,
                channel_id=channel.id,
                ping=ping,
            )
            pretty_log(
                "info",
                f"✅ Added market alert for {target_name} (Dex: {dex_number}) at max price {max_price} for user {user_name} (ID: {user_id})",
                label="MARKET ALERT ADD",
            )
            # Get updated total alerts after adding new alert
            current_alerts_used = get_user_total_market_alerts_from_cache(user_id)
            current_max_alerts = determine_total_market_alerts_for_user(user)
            ping_str = "Yes" if ping else "No"
            display_name = get_display_name(target_name, dex=True)
            embed = discord.Embed(
                title="✅ Market Alert Added",
                description=(
                    f"**Alerts:** {current_alerts_used}/{current_max_alerts}\n"
                    f"**Pokemon:** {display_name}\n"
                    f"**Max Price:** {Emojis.pokecoin} {max_price:,}\n"
                    f"**Channel:** {channel.mention}\n"
                    f"**Ping:** {ping_str}\n\n"
                ),
            )
            footer_text = (
                "You will be notified when a matching market listing is found."
            )
            embed = design_embed(
                embed=embed,
                user=user,
                footer_text=footer_text,
                pokemon_name=target_name,
            )
            pretty_log(
                "sucess",
                f"✅ Successfully set market alert for user {user_name} (ID: {user_id})",
                label="MARKET ALERT ADD",
            )
            await loader.success(embed=embed, content="")

            # Send log to server log channel
            log_embed = discord.Embed(
                title="📢 New Market Alert Set",
                description=(
                    f"**User:** {user.mention}\n"
                    f"**Alerts:** {current_alerts_used}/{current_max_alerts}\n"
                    f"**Pokemon:** {display_name}\n"
                    f"**Max Price:** {Emojis.pokecoin} {max_price:,}\n"
                    f"**Channel:** {channel.mention}\n"
                    f"**Ping:** {ping_str}\n"
                ),
            )
            log_embed = design_embed(
                embed=log_embed, user=user, pokemon_name=target_name
            )

            if interaction.user.id != KHY_USER_ID:
                await send_log_to_server_log(bot, guild, log_embed)

        except Exception as e:
            pretty_log(
                "error",
                f"Failed to set market alert for user {user_name} (ID: {user_id}): {e}",
                label="MARKET ALERT ADD",
            )
            await loader.error(f"Failed to set market alert: {e}")
            return
    except Exception as e:
        pretty_log(
            "error",
            f"Unexpected error in add_market_alert_func for user {user_name} (ID: {user_id}): {e}",
            label="MARKET ALERT ADD",
        )

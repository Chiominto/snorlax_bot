import discord
from discord.ext import commands

from constants.aesthetics import Emojis
from constants.celestial_constants import KHY_USER_ID
from utils.cache.cache_list import market_alert_cache
from utils.db.market_alert_db import (
    insert_market_alert,
    remove_all_market_alerts_for_user,
    remove_market_alert,
    update_market_alert,
)
from utils.functions.design_embed import design_embed
from utils.functions.pokemon_func import get_dex_number_by_name, is_mon_in_game, get_display_name
from utils.functions.pretty_defer import pretty_defer, pretty_error
from utils.logs.pretty_log import pretty_log
from utils.logs.server_log import send_log_to_server_log


async def remove_market_alert_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    pokemon: str,
):
    """
    Removes an/all existing market alert(s) for a user.
    """

    user = interaction.user
    user_id = user.id
    user_name = user.name
    guild = interaction.guild

    # Initialize loader
    loader = await pretty_defer(
        interaction=interaction,
        content="Removing your market alert...",
        ephemeral=False,
    )
    from utils.cache.market_alert_cache import (
        determine_total_market_alerts_for_user,
        get_user_total_market_alerts_from_cache,
    )

    if pokemon.lower() == "all":
        # Check if user has any alerts
        existing_alerts = [
            alert for alert in market_alert_cache if alert["user_id"] == user_id
        ]
        if not existing_alerts:
            await loader.error(content="You have no market alerts to remove.")
            return

        # Get count of alerts to be removed
        alert_count = len(existing_alerts)

        # Remove all alerts for the user
        await remove_all_market_alerts_for_user(bot, user_id)

        # Send success message
        embed = discord.Embed(
            title="✅ Market Alerts Removed",
            description=f"All ({alert_count}) of your market alerts have been removed.",
        )
        footer_text = "You can add new alerts using the /market-alert add command."
        embed = design_embed(embed=embed, user=user, footer_text=footer_text)
        await loader.success(embed=embed, content="")
        pretty_log(
            message=f"✅ Removed all ({alert_count}) market alerts for user {user_name} ({user_id}).",
            tag="market_alert",
        )
        # Fetch max alerts for logging
        max_alerts = determine_total_market_alerts_for_user(user)
        alert_count = get_user_total_market_alerts_from_cache(user_id)

        # Send log to server log
        embed = discord.Embed(
            title="🗑️ All Market Alerts Removed",
            description=(
                f"**User:** {user.mention}\n"
                f"**Alerts Removed:** {alert_count}\n"
                f"**Max Alerts Allowed:** {max_alerts}\n"
            ),
        )
        embed = design_embed(embed=embed, user=user)
        await send_log_to_server_log(bot, guild, embed)

        return

    else:
        # Get dex number and validate pokemon
        if not is_mon_in_game(pokemon):
            await loader.error(
                content=f"'{pokemon}' is not a valid Pokémon name.",
            )
            return
        dex_number = get_dex_number_by_name(pokemon)
        target_name = pokemon.lower()

        # Check if user has an existing alert for this pokemon
        existing_alert = None
        for alert in market_alert_cache:
            if (
                alert["user_id"] == user_id
                and alert["pokemon"].lower() == target_name.lower()
            ):
                existing_alert = alert
                break
        if not existing_alert:
            await loader.error(
                content=f"You do not have an existing market alert for **{target_name}**."
            )
            return

        # Get values before removal for logging
        channel_id = existing_alert["channel_id"]

        max_price = existing_alert["max_price"]

        ping_str = "Yes" if existing_alert.get("ping") else "No"

        # Remove the specific market alert
        await remove_market_alert(bot, user_id, target_name.lower())

        # Update alerts used in db

        # Get updated alerts used count
        new_alerts_used = get_user_total_market_alerts_from_cache(user_id)
        max_alerts = determine_total_market_alerts_for_user(user)
        display_name = get_display_name(target_name, dex=True)

        # Send success message
        desc = (
            f"**Alerts Used:** {new_alerts_used}/{max_alerts}\n"
            f"**Pokemon:** {display_name}\n"
            f"**Max Price:** {Emojis.pokecoin} {max_price:,}\n"
            f"**Channel:** <#{channel_id}>\n"
            f"**Ping:** {ping_str}\n"
        )
        embed = discord.Embed(
            title="✅ Market Alert Removed",
            description=desc,
        )
        footer_text = "You can add a new alert using the /market-alert add command."
        embed = design_embed(
            embed=embed, user=user, footer_text=footer_text, pokemon_name=target_name
        )
        await loader.success(embed=embed, content="")
        pretty_log(
            message=f"✅ Removed market alert for {target_name} for user {user_name} ({user_id}).",
            tag="market_alert",
        )
        desc = (
            f"**User:** {user.mention}\n"
            f"**Alerts Used:** {new_alerts_used}/{max_alerts}\n"
            f"**Pokemon:** {display_name}\n"
            f"**Max Price:** {Emojis.pokecoin} {max_price:,}\n"
            f"**Channel:** <#{channel_id}>\n"
            f"**Ping:** {ping_str}\n"
        )
        # Send log to server log channel
        embed = discord.Embed(
            title="🗑️ Market Alert Removed",
            description=desc,
        )
        embed = design_embed(embed=embed, user=user, pokemon_name=target_name)
        if interaction.user.id != KHY_USER_ID:
            await send_log_to_server_log(bot, guild, embed)

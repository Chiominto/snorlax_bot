import discord
from discord.ext import commands
from utils.functions.parsers import parse_compact_number

from constants.aesthetics import Emojis
from utils.cache.cache_list import market_alert_cache
from utils.db.market_alert_db import (
    update_market_alert,
)
from utils.functions.design_embed import design_embed
from utils.functions.pretty_defer import pretty_defer, pretty_error
from utils.logs.pretty_log import pretty_log
from utils.logs.server_log import send_log_to_server_log

from utils.functions.pokemon_func import get_display_name, get_dex_number_by_name, is_mon_in_game


async def update_market_alert_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    pokemon: str,
    new_max_price: str = None,
    new_channel: discord.TextChannel = None,
    new_ping: str = None,
):
    """
    Updates an existing market alert for a user.
    """

    # Check if there are anything to update
    if not any([new_max_price, new_channel, new_ping]):
        await pretty_error(
            interaction,
            "No update parameters provided. Please specify at least one field to update.",
        )
        return

    user = interaction.user
    user_id = user.id
    user_name = user.name
    guild = interaction.guild

    # Initialize loader
    loader = await pretty_defer(
        interaction=interaction,
        content="Updating your market alert...",
        ephemeral=False,
    )

    # Get dex number and validate pokemon
    if not is_mon_in_game(pokemon):
        await loader.error(
            content=f"'{pokemon}' is not a valid Pokémon name.",
        )
        return
    dex_number = get_dex_number_by_name(pokemon)
    target_name = pokemon.lower()

    # Validate new price
    if new_max_price:
        parsed_price = parse_compact_number(new_max_price)
        if not parsed_price:
            await loader.error(
                content="Invalid price format. Please enter a valid number."
            )
            return

    # Fetch existing alert from cache
    old_market_alert_info = None
    for alert in market_alert_cache:
        if (
            alert["user_id"] == user_id
            and alert["pokemon"].lower() == target_name.lower()
        ):
            old_market_alert_info = alert
            break
    if not old_market_alert_info:
        await loader.error(
            content=f"No existing market alert found for **{target_name}**. Please add an alert first."
        )
        return

    old_channel_id = old_market_alert_info["channel_id"]
    old_max_price = old_market_alert_info["max_price"]
    old_ping = old_market_alert_info.get("ping", False)
    old_ping_str = "Yes" if old_ping else "No"
    new_ping_str = "Yes" if new_ping and new_ping.lower() == "yes" else "No"
    new_ping = True if new_ping and new_ping.lower() == "yes" else False
    # Update in database
    try:
        await update_market_alert(
            bot=bot,
            user_id=user_id,
            pokemon=target_name.lower(),
            new_max_price=int(parsed_price) if new_max_price else None,
            new_channel_id=new_channel.id if new_channel else None,
            new_ping=new_ping,
        )
        pretty_log(
            message=f"✅ Updated market alert for {user_name} (ID: {user_id}) - {target_name}",
            tag="db",
        )
        display_name = get_display_name(target_name, dex=True)
        # Build confirmation message
        embed = discord.Embed(
            title="Market Alert Updated!",
            description=f"**Pokemon:** {display_name}\n",
        )
        if new_max_price:
            embed.description += f"**Max Price:** {Emojis.pokecoin} {old_max_price} → {Emojis.pokecoin} {parsed_price}\n"
        if new_channel:
            old_channel_mention = f"<#{old_channel_id}>"
            new_channel_mention = f"<#{new_channel.id}>"
            embed.description += (
                f"**Channel:** {old_channel_mention} → {new_channel_mention}\n"
            )
        if new_ping is not None:
            embed.description += f"**Ping:** {old_ping_str} → {new_ping_str}\n"

        footer_text = "You will be notified when a matching market listing is found."
        embed = design_embed(
            embed=embed, user=user, pokemon_name=target_name, footer_text=footer_text
        )
        await loader.success(embed=embed, content="")

        # Send log to server log channel
        log_embed = discord.Embed(
            title="📢 Market Alert Updated",
            description=(
                f"**User:** {user.mention}\n"
                f"**Pokemon:** {display_name}\n"
            ),
        )
        if new_max_price:
            log_embed.description += f"**Max Price:** {Emojis.pokecoin} {old_max_price} → {Emojis.pokecoin} {parsed_price}\n"
        if new_channel:
            old_channel_mention = f"<#{old_channel_id}>"
            new_channel_mention = f"<#{new_channel.id}>"
            log_embed.description += (
                f"**Channel:** {old_channel_mention} → {new_channel_mention}\n"
            )
        if new_ping is not None:
            embed.description += f"**Ping:** {old_ping_str} → {new_ping_str}\n"

        log_embed = design_embed(embed=log_embed, user=user, pokemon_name=target_name)
        await send_log_to_server_log(bot, embed=log_embed, guild=guild)

    except Exception as e:
        await loader.error(
            content="An error occurred while updating your market alert. Please try again later."
        )
        pretty_log(
            message=f"❌ Failed to update market alert for {user_name} (ID: {user_id}): {e}",
            tag="error",
            include_trace=True,
        )
        return

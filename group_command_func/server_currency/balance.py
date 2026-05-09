from datetime import datetime
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands
from constants.celestial_constants import CELESTIAL_SERVER_ID, DEFAULT_EMBED_COLOR

from constants.server_currency import (
    CURRENCY_EMOJI,
    FRY_POINT_EMOJI,

)
from utils.cache.cache_list import server_currency_cache
from utils.db.server_currency_db import (
    reset_server_currency_table,
    upsert_user_currency,
    upsert_user_fry_points,
    upsert_server_currency,
)
from utils.functions.pretty_defer import pretty_defer

from utils.logs.pretty_log import pretty_log
from utils.logs.server_log import send_log_to_server_log
from utils.functions.role_checks import is_clan_member, is_staff_member
SHOP_COLOR = DEFAULT_EMBED_COLOR

# Add Balance
async def add_balance_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    member: discord.Member,
    starry_meal: int = 0,
    fry_points: int = 0,
):
    """
    Add currency balance and/or raffle tickets to a member.
    """
    # Check if at least one parameter is provided
    if starry_meal is None and fry_points is None:
        return await interaction.response.send_message(
            "You must specify at least one of starry_meal or fry points to add.",
            ephemeral=True,
        )

    # Defer the interaction to allow more time for processing
    loader = await pretty_defer(
        interaction=interaction,
        content="Adding balance to member...",
        ephemeral=False,
    )

    # Update balance and/or raffle tickets in the database
    current_balance_info = server_currency_cache.get(member.id)
    if not current_balance_info:
        pretty_log(
            "debug",
            f"No existing balance info for member ID {member.id} in cache.",
            label="Server Currency",
        )
        current_balance = 0
        await upsert_server_currency(
            bot=bot,
            user_id=member.id,
            user_name=member.name,
            currency=0,
            fry_points=0,

        )
    else:

        current_balance = current_balance_info.get("currency") or 0

    if starry_meal is None:
        starry_meal = 0

    updated_starry_meal = False
    updated_fry_points = False
    if starry_meal:
        new_balance = current_balance + starry_meal
        await upsert_user_currency(
            bot=bot,
            user_id=member.id,
            user_name=member.name,
            currency=new_balance,
        )
        updated_starry_meal = True

    if fry_points:
        current_fry_points = (
            current_balance_info.get("fry_points", 0) if current_balance_info else 0
        )
        new_fry_points = current_fry_points + fry_points
        await upsert_user_fry_points(
            bot=bot,
            user_id=member.id,
            user_name=member.name,
            fry_points=new_fry_points,
        )
        updated_fry_points = True
    # Success embed
    description_parts = [f"**Member:** {member.mention}\n"]
    if updated_starry_meal:
        description_parts.append(
            f"**Starry Meals Added:** {starry_meal} {CURRENCY_EMOJI}\n"
            f"**New Balance:** {new_balance} {CURRENCY_EMOJI}"
        )

    if updated_fry_points:
        description_parts.append(
            f"**Fry Points Added:** {fry_points} {FRY_POINT_EMOJI}\n"
            f"**New Fry Points:** {new_fry_points} {FRY_POINT_EMOJI}"
        )
    desc = "\n".join(description_parts)
    embed = discord.Embed(
        title="Balance Added",
        color=SHOP_COLOR,
        timestamp=datetime.now(),
        description=desc,
    )
    embed.set_author(
        name=interaction.user.display_name,
        icon_url=interaction.user.display_avatar.url,
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(
        text=f"Member ID: {member.id}",
        icon_url=interaction.guild.icon.url if interaction.guild else None,
    )
    await loader.success(embed=embed, content="")
    pretty_log(
        "info",
        f"Added balance to member: {member.display_name} (ID: {member.id}). "
        f"Starry Meals Added: {starry_meal if starry_meal else 0}, ",
        label="Server Currency",
    )
    # Send in action log channel
    guild = interaction.guild
    await send_log_to_server_log(
        bot=bot,
        guild=guild,
        embed=embed,
    )


# Remove Balance
async def remove_balance_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    member: discord.Member,
    starry_meal: int = None,
    fry_points: int = None,
):
    """
    Remove currency balance and/or raffle tickets from a member.
    """
    # Check if at least one parameter is provided
    if starry_meal is None and fry_points is None:
        return await interaction.response.send_message(
            "You must specify at least one of starry_meal, or fry_points to remove.",
            ephemeral=True,
        )

    # Defer the interaction to allow more time for processing
    loader = await pretty_defer(
        interaction=interaction,
        content="Removing balance from member...",
        ephemeral=False,
    )

    # Update balance and/or raffle tickets in the database
    current_balance_info = server_currency_cache.get(member.id)
    if not current_balance_info:
        current_balance = 0
        current_fry_points = 0
    else:
        current_balance = current_balance_info.get("currency", 0)
        current_fry_points = (
            current_balance_info.get("fry_points", 0) if current_balance_info else 0
        )


    updated_starry_meal = False
    updated_fry_points = False
    if starry_meal:
        new_balance = max(0, current_balance - starry_meal)
        await upsert_user_currency(
            bot=bot,
            user_id=member.id,
            user_name=member.name,
            balance=new_balance,
        )
        updated_starry_meal = True


    if fry_points:
        new_fry_points = max(0, current_fry_points - fry_points)
        await upsert_user_fry_points(
            bot=bot,
            user_id=member.id,
            user_name=member.name,
            fry_points=new_fry_points,
        )
        updated_fry_points = True

    # Success embed
    description_parts = [f"**Member:** {member.mention}\n"]
    if updated_starry_meal:
        description_parts.append(
            f"**Starry Meals Removed:** {starry_meal} {CURRENCY_EMOJI}\n"
            f"**New Balance:** {new_balance} {CURRENCY_EMOJI}"
        )

    if updated_fry_points:
        description_parts.append(
            f"**Fry Points Removed:** {fry_points} {FRY_POINT_EMOJI}\n"
            f"**New Fry Points:** {new_fry_points} {FRY_POINT_EMOJI}"
        )

    desc = "\n".join(description_parts)
    embed = discord.Embed(
        title="Balance Removed",
        color=SHOP_COLOR,
        timestamp=datetime.now(),
        description=desc,
    )
    embed.set_author(
        name=interaction.user.display_name,
        icon_url=interaction.user.display_avatar.url,
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(
        text=f"Member ID: {member.id}",
        icon_url=interaction.guild.icon.url if interaction.guild else None,
    )
    await loader.success(embed=embed, content="")
    pretty_log(
        "info",
        f"Removed balance from member: {member.display_name} (ID: {member.id}). "
        f"Happy Meals Removed: {starry_meal if starry_meal else 0}, ",
        label="Server Currency",
    )
    # Send in action log channel
    guild = interaction.guild
    await send_log_to_server_log(
        bot=bot,
        guild=guild,
        embed=embed,
    )


async def reset_all_balances_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
):
    """
    Reset all members' currency balances to zero.
    """
    # Defer the interaction to allow more time for processing
    loader = await pretty_defer(
        interaction=interaction,
        content="Resetting all member balances...",
        ephemeral=False,
    )

    # Reset all balances and raffle tickets in the database
    await reset_server_currency_table(bot=bot)

    # Success embed
    embed = discord.Embed(
        title="All Balances Reset",
        color=SHOP_COLOR,
        timestamp=datetime.now(),
        description="Successfully reset all members' starry meals and fry points to zero.",
    )
    embed.set_author(
        name=interaction.user.display_name,
        icon_url=interaction.user.display_avatar.url,
    )
    await loader.success(embed=embed, content="")
    pretty_log(
        "info",
        "Reset all members' starry meals and fry points to zero.",
        label="Server Currency",
    )
    # Send in action log channel
    guild = interaction.guild
    await send_log_to_server_log(
        bot=bot,
        guild=guild,
        embed=embed,
    )


async def view_balance_func(
    bot: commands.Bot, interaction: discord.Interaction, member: discord.Member = None
):
    """
    View a member's currency balance and raffle tickets.
    # If no member specified, view own balance
    """
    # Check if clan member
    if not is_clan_member(interaction):
        return await interaction.response.send_message(
            "You do not have permission to view balances. Clan members only.",
            ephemeral=True,
        )

    target_member = interaction.user
    if member:
        target_member = member
        # Only allow staff to view others' balances
        if not is_staff_member(member=interaction.user):
            return await interaction.response.send_message(
                "You do not have permission to view other members' balances.",
                ephemeral=True,
            )
    # Defer the interaction to allow more time for processing
    loader = await pretty_defer(
        interaction=interaction,
        content="Fetching member balance...",
        ephemeral=False,
    )
    # Fetch balance and raffle tickets from cache
    balance_info = server_currency_cache.get(target_member.id)
    if not balance_info:
        balance = 0
        fry_points = 0
    else:
        balance = balance_info.get("currency", 0)
        fry_points = balance_info.get("fry_points", 0)
    # Create embed
    embed = discord.Embed(
        title="Balance Info",
        color=SHOP_COLOR,
        timestamp=datetime.now(),
        description=(
            f"**Member:** {target_member.mention}\n"
            f"**Starry Meals:** {balance} {CURRENCY_EMOJI}\n"
            f"**Fry Points:** {fry_points} {FRY_POINT_EMOJI}"
        ),
    )
    embed.set_author(
        name=target_member.display_name, icon_url=target_member.display_avatar.url
    )
    embed.set_thumbnail(url=target_member.display_avatar.url)
    await loader.success(embed=embed, content="")

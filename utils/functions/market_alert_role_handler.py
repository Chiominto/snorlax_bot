from datetime import datetime

import discord
from discord.ext import commands


from utils.db.market_alert_db import remove_recent_market_alerts
from utils.logs.pretty_log import pretty_log


async def market_alert_role_remove_handler(
    bot: discord.Client,
    member: discord.Member,
    role: discord.Role,
):
    from utils.cache.market_alert_cache import fetch_user_alerts_from_cache, MARKET_ALERT_ROLE_MAP, determine_total_market_alerts_for_user, get_user_total_market_alerts_from_cache
    # Check if user has any market alerts in cache
    user_alerts = fetch_user_alerts_from_cache(member.id)
    if not user_alerts:
        pretty_log(
            message=(
                f"No market alerts found in cache for member '{member.display_name}' "
                f"after role removal. No alerts to remove."
            ),
            tag="info",
            label="Role Remove Event",
        )
        return

    # Get how many alerts to remove based on role removed
    alerts_used = len(user_alerts)
    role_alert_count = MARKET_ALERT_ROLE_MAP.get(role.id, 0)
    max_alerts = determine_total_market_alerts_for_user(member)
    # Return Early if user is now within max alerts after role removal
    if alerts_used <= max_alerts:
        pretty_log(
            message=(
                f"Member '{member.display_name}' has {alerts_used} market alerts, "
                f"which is within the new max of {max_alerts} after role removal. "
                f"No alerts need to be removed."
            ),
            tag="info",
            label="Role Remove Event",
        )
        return

    # Dm member about decreased max alerts
    old_max_alerts = max_alerts + role_alert_count
    new_max_alerts = max_alerts
    alert_difference = old_max_alerts - new_max_alerts
    removed_alerts = []
    if alerts_used > new_max_alerts:
        # Remove most recent alerts to fit new max_alerts
        num_alerts_to_remove = alerts_used - new_max_alerts
        removed_alerts = await remove_recent_market_alerts(
            bot, member, num_alerts_to_remove
        )
        pretty_log(
            message=(
                f"Removed {len(removed_alerts)} market alerts for member "
                f"'{member.display_name}' due to decreased max alerts."
            ),
            tag="info",
            label="Role Remove Event",
        )
    try:
        removed_alerts_line = ""
        if removed_alerts:
            removed_alerts_line = "\n**Removed Alerts:**\n" + "\n".join(
                [
                    f"- {alert['pokemon']} (Dex: {alert['dex']}, Max Price: {alert['max_price']})"
                    for alert in removed_alerts
                ]
            )
        embed = discord.Embed(
            title="📉 Market Alert Limit Decreased!",
            description=(
                f"**Old Max Alerts:** {old_max_alerts}\n"
                f"**New Max Alerts:** {new_max_alerts}\n"
                f"**Alerts Currently Used:** {alerts_used}\n"
                f"{removed_alerts_line}"
            ),
            color=0xFF0000,
        )
        await member.send(
            content=f"Your market alert limit has been decreased due to {role.name} role removal.",
            embed=embed,
        )
    except Exception as e:
        pretty_log(
            message=(
                f"Failed to DM member '{member.display_name}' about decreased max alerts: {e}"
            ),
            tag="error",
            label="Role Remove Event",
        )

async def market_alert_role_add_handler(
    bot: discord.Client,
    member: discord.Member,
    role: discord.Role,
):
    from utils.cache.market_alert_cache import (
        fetch_user_alerts_from_cache,
        MARKET_ALERT_ROLE_MAP,
        determine_total_market_alerts_for_user,
        get_user_total_market_alerts_from_cache,
    )
    # Get how many alerts to remove based on role removed
    alerts_used = get_user_total_market_alerts_from_cache(member.id)
    role_alert_count = MARKET_ALERT_ROLE_MAP.get(role.id, 0)
    max_alerts = determine_total_market_alerts_for_user(member)
    old_max_alerts = max_alerts - role_alert_count
    new_max_alerts = max_alerts
    # Dm member about increased max alerts
    try:
        embed = discord.Embed(
            title="📈 Market Alert Limit Increased!",
            description=(
                f"**Old Max Alerts:** {old_max_alerts}\n"
                f"**New Max Alerts:** {new_max_alerts}\n"
                f"**Alert Usage:** {alerts_used}/{new_max_alerts}\n"
                f"**Reason:** You gained {role.name} role!"
            ),
            color=discord.Color.green(),
            timestamp=datetime.now(),
        )
        embed.set_author(
            name=member.display_name, icon_url=member.display_avatar.url
        )
        await member.send(embed=embed)
    except Exception as e:
        pretty_log(
            message=(
                f"Failed to send DM to member '{member.display_name}' "
                f"about increased max alerts: {e}"
            ),
            tag="error",
            label="Role Add Event",
        )

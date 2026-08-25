
import discord

from constants.celestial_constants import (CELESTIAL_ROLES,
                                           CELESTIAL_SERVER_ID,
                                           CELESTIAL_TEXT_CHANNELS)
from utils.logs.pretty_log import pretty_log


async def lock_snipe_channel(bot):
    """
    Locks the snipe channel by removing the 'Send Messages' permission for roles that are not in the CELESTIAL_ROLES list.
    """

    guild = bot.get_guild(CELESTIAL_SERVER_ID)
    if not guild:
        pretty_log(
            "error",
            f"Guild with ID {CELESTIAL_SERVER_ID} not found.",
            label="SNIPE_CHANNEL_LOCK",
        )
        return

    snipe_channel = guild.get_channel(CELESTIAL_TEXT_CHANNELS.giveaway_snipe)
    if not snipe_channel:
        pretty_log(
            "error",
            f"Snipe channel with ID {CELESTIAL_TEXT_CHANNELS.giveaway_snipe} not found.",
            label="SNIPE_CHANNEL_LOCK",
        )
        return
    celestial_nova_role = guild.get_role(CELESTIAL_ROLES.celestialnova_)
    giveaway_host_role = guild.get_role(CELESTIAL_ROLES.giveaway_host)
    if not celestial_nova_role or not giveaway_host_role:
        pretty_log(
            "error",
            f"One or both roles not found: Celestial Nova Role ID {CELESTIAL_ROLES.celestialnova_}, Giveaway Host Role ID {CELESTIAL_ROLES.giveaway_host}.",
            label="SNIPE_CHANNEL_LOCK",
        )
        return

    # Lock the channel by removing 'Send Messages' permission for everyone except Celestial Nova and Giveaway Host roles
    try:
        for role in (celestial_nova_role, giveaway_host_role):
            overwrite = snipe_channel.overwrites_for(role)
            overwrite.send_messages = False
            await snipe_channel.set_permissions(role, overwrite=overwrite)
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to lock snipe channel: {e}",
            label="SNIPE_CHANNEL_LOCK",
        )


async def unlock_snipe_channel(bot):
    """
    Unlocks the snipe channel by restoring the 'Send Messages' permission for everyone.
    """

    guild = bot.get_guild(CELESTIAL_SERVER_ID)
    if not guild:
        pretty_log(
            "error",
            f"Guild with ID {CELESTIAL_SERVER_ID} not found.",
            label="SNIPE_CHANNEL_LOCK",
        )
        return

    snipe_channel = guild.get_channel(CELESTIAL_TEXT_CHANNELS.giveaway_snipe)
    if not snipe_channel:
        pretty_log(
            "error",
            f"Snipe channel with ID {CELESTIAL_TEXT_CHANNELS.giveaway_snipe} not found.",
            label="SNIPE_CHANNEL_LOCK",
        )
        return
    celestial_nova_role = guild.get_role(CELESTIAL_ROLES.celestialnova_)
    giveaway_host_role = guild.get_role(CELESTIAL_ROLES.giveaway_host)

    # Unlock the channel by restoring 'Send Messages' permission for everyone
    try:
        default_overwrite = snipe_channel.overwrites_for(guild.default_role)
        default_overwrite.send_messages = True
        await snipe_channel.set_permissions(guild.default_role, overwrite=default_overwrite)

        for role in filter(None, (celestial_nova_role, giveaway_host_role)):
            overwrite = snipe_channel.overwrites_for(role)
            overwrite.send_messages = True
            await snipe_channel.set_permissions(role, overwrite=overwrite)
        pretty_log(
            "ready",
            f"✅ Snipe channel unlocked successfully.",
            label="SNIPE_CHANNEL_LOCK",
        )
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to unlock snipe channel: {e}",
            label="SNIPE_CHANNEL_LOCK",
        )
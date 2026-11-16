import re
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from constants.celestial_constants import (
    CELESTIAL_ROLES,
    CELESTIAL_SERVER_ID,
    CELESTIAL_TEXT_CHANNELS,
    KHY_USER_ID,
)
from constants.paldea_galar_dict import rarity_meta
from constants.server_currency import POINT_MAP, EVENT_EGG_EXCLUSIVES
from utils.functions.pokemeow_reply import get_pokemeow_reply_or_interaction_member
from utils.listener_func.rarespawn_listener import add_points_to_member
from utils.logs.debug_log import debug_log, enable_debug
from utils.logs.pretty_log import pretty_log

RARE_EGG_EXCLUSIVES = [
    "chingling",
    "mimejr",
    "happiny",
    "chatot",
    "munchlax",
    "riolu",
    "audino",
    "zorua",
    "emolga",
    "ferroseed",
    "golett",
    "pawniard",
    "pancham",
    "spritzee",
    "swirlix",
    "noibat",
    "crabrawler",
    "rockruff",
    "type-null",
    "yamper",
    "nickit",
]
SUPER_RARE_EGG_EXCLUSIVE = ["carbink", "mimikyu"]
LEGENDARY_EGG_EXCLUSIVES = ["manaphy", "victini", "phione"]

TEST_BOT_LOG_ID = 1220786187401302036
REAL_BOT_LOG_ID = 1076441765059502233
BOT_LOG_ID = TEST_BOT_LOG_ID
processed_egg_hatches = set()


# enable_debug(f"{__name__}.egg_hatch_listener_func")


# ❀─────────────────────────────────────────❀
#      💖  Egg Hatch Listener
# ❀─────────────────────────────────────────❀
async def egg_hatch_listener_func(
    bot: discord.Client,
    message: discord.Message,
):
    """
    Listens for egg hatch messages and logs them.
    """

    embed = message.embeds[0] if message.embeds else None
    content = message.content if message.content else None
    if not embed and not content:
        debug_log(f"No embed or content found in message ID {message.id}, skipping.")
        return

    # Color
    embed_color = embed.color.value if embed and embed.color else None
    thumbnail_url = embed.image.url if embed and embed.image else None

    # Extract Pokemon name from message content
    pokemon_name = None
    if content:
        # Pattern: "just hatched a <:447:...> **Riolu**!"
        hatch_match = re.search(r"just hatched a.*?\*\*([^*]+)\*\*", content)
        if hatch_match:
            pokemon_name = hatch_match.group(1).strip()
            pretty_log(
                tag="info",
                message=f"Detected egg hatch of '{pokemon_name}' from message content.",
                label="💖 EGG HATCH LISTENER",
            ),

    if not pokemon_name:
        # Say why it didnt match
        debug_log(
            f"No pokemon_name matched in message content: '{content}' (ID: {message.id}). "
            f"Pattern used: r'just hatched a.*?\\*\\*([^*]+)\\*\\*'. "
            f"Regex result: {'No match' if not 'hatch_match' in locals() or not hatch_match else hatch_match}"
        )
        return

    member = await get_pokemeow_reply_or_interaction_member(message)
    if not member:
        debug_log(
            f"Could not determine member from message ID {message.id} in {message.channel.name}, skipping."
        )
        return

    if message.id in processed_egg_hatches:
        return
    processed_egg_hatches.add(message.id)

    lowered_pokemon_name = pokemon_name.lower()
    stripped_pokemon_name = pokemon_name.replace("Shiny ", "").strip()

    clan_role = message.guild.get_role(CELESTIAL_ROLES.celestialnova_)
    donated_role = message.guild.get_role(CELESTIAL_ROLES.tip_jar_titan)

    # Check if member has donated role and clan role
    if (not clan_role or clan_role not in member.roles) and (
        not donated_role or donated_role not in member.roles
    ):
        return  # dont reward if not clan member or donor

    # Reward points
    if lowered_pokemon_name not in EVENT_EGG_EXCLUSIVES:
        return  # Skip non-event exclusive egg hatches

    # Determine points to award
    catch_type = "shiny_egg_exclusive"
    rarity = "shiny"

    points = POINT_MAP.get(catch_type, 0)
    rarity_emoji = rarity_meta.get(rarity, {}).get("emoji", "")
    pokemon_name = stripped_pokemon_name.title()
    display_pokemon_name = (
        f"{rarity_emoji} {pokemon_name}" if rarity_emoji else pokemon_name
    )
    context = catch_type.replace("_", " ").title()

    # Add points to member
    try:
        await add_points_to_member(
            bot=bot,
            member=member,
            points=points,
            display_pokemon_name=display_pokemon_name,
            message=message,
            catch_type=context,
        )
        pretty_log(
            tag="info",
            message=f"Successfully added {points} points to member {member} for message ID {message.id}.",
            label="💖 EGG HATCH LISTENER",
        )
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to add points to member {member} for message ID {message.id}: {e}",
            label="💖 EGG HATCH LISTENER",
        )

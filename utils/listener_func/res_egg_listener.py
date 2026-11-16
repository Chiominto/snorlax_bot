import re

import discord

from constants.celestial_constants import CELESTIAL_ROLES
from constants.paldea_galar_dict import rarity_meta
from constants.server_currency import POINT_MAP, EVENT_EGG_EXCLUSIVES
from utils.listener_func.rarespawn_listener import add_points_to_member
from utils.logs.pretty_log import pretty_log

LOG_LABEL = "🥚 RESEARCH LAB EGG HATCH"

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


def get_res_egg_hatch_member(message: discord.Message) -> discord.Member | None:
    guild = message.guild
    if guild is None:
        pretty_log(
            tag="warn",
            message="Cannot look up Research Lab hatch member without a guild.",
            label=LOG_LABEL,
            include_trace=False,
        )
        return None

    embed = message.embeds[0] if message.embeds else None
    author_name = embed.author.name if embed and embed.author else None
    if not author_name:
        pretty_log(
            tag="warn",
            message="Research Lab hatch message has no embed author name.",
            label=LOG_LABEL,
            include_trace=False,
        )
        return None

    match = re.fullmatch(
        r"\s*(?:👤\s*)?(.+?)'s Research Lab Hatch\s*",
        author_name,
        re.IGNORECASE,
    )
    if not match:
        pretty_log(
            tag="warn",
            message=f"Could not extract username from hatch embed author: {author_name!r}",
            label=LOG_LABEL,
            include_trace=False,
        )
        return None

    username = match.group(1).strip()
    member = guild.get_member_named(username)
    if member is None:
        pretty_log(
            tag="warn",
            message=f"Could not find guild member for Research Lab username {username!r}.",
            label=LOG_LABEL,
            include_trace=False,
        )
    return member


def extract_hatch_info(message: str) -> dict | None:
    match = re.search(
        r"\*\*(.+?)\*\* hatched in \*\*(.+?)\*\*!.*?" r"\*\*(.+?)\*\*",
        message,
        re.DOTALL,
    )

    if not match:
        return None

    return {
        "egg_type": match.group(1),
        "incubator_num": match.group(2),
        "hatched_mon": match.group(3),
    }


async def handle_res_egg_hatch(bot: discord.Client, message: discord.Message):
    pretty_log(
        tag="info",
        message=(
            f"Processing Research Lab hatch message {message.id} in guild "
            f"{getattr(message.guild, 'id', None)}."
        ),
        label=LOG_LABEL,
        include_trace=False,
    )
    embed = message.embeds[0] if message.embeds else None
    if not embed:
        pretty_log(
            tag="warn",
            message="No embed found; ignoring message.",
            label=LOG_LABEL,
            include_trace=False,
        )
        return
    pretty_log(
        tag="info",
        message=f"Using embed with title: {embed.title!r}",
        label=LOG_LABEL,
        include_trace=False,
    )

    hatch_info = extract_hatch_info(embed.description)
    if not hatch_info:
        pretty_log(
            tag="warn",
            message="Could not extract hatch information from the embed description.",
            label=LOG_LABEL,
            include_trace=False,
        )
        return
    pretty_log(
        tag="info",
        message=f"Extracted hatch information: {hatch_info}",
        label=LOG_LABEL,
        include_trace=False,
    )

    hatched_mon = hatch_info["hatched_mon"]

    if hatched_mon.lower() not in EVENT_EGG_EXCLUSIVES:
        pretty_log(
            tag="info",
            message=f"{hatched_mon} is not an event egg exclusive; ignoring it.",
            label=LOG_LABEL,
            include_trace=False,
        )
        return

    member = get_res_egg_hatch_member(message)
    if not member:
        pretty_log(
            tag="warn",
            message="Could not determine member for Research Lab hatch; ignoring message.",
            label=LOG_LABEL,
            include_trace=False,
        )
        return

    clan_role = message.guild.get_role(CELESTIAL_ROLES.celestialnova_)
    donated_role = message.guild.get_role(CELESTIAL_ROLES.tip_jar_titan)

    # Check if member has donated role and clan role
    if (not clan_role or clan_role not in member.roles) and (
        not donated_role or donated_role not in member.roles
    ):
        pretty_log(
            tag="info",
            message=f"Skipping reward for {member}: member lacks the clan or donor role.",
            label=LOG_LABEL,
            include_trace=False,
        )
        return

    catch_type = "shiny_egg_exclusive"
    rarity = "shiny"
    stripped_pokemon_name = hatched_mon.replace("Shiny ", "").strip()

    # Determine points to award
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
            message=(
                f"Added {points} points to Research Lab hatch member {member} "
                f"for message ID {message.id}."
            ),
            label=LOG_LABEL,
            include_trace=False,
        )
    except Exception as e:
        pretty_log(
            tag="error",
            message=(
                f"Failed to add Research Lab hatch points to {member} "
                f"for message ID {message.id}: {e}"
            ),
            label=LOG_LABEL,
        )

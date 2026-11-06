import re
from datetime import datetime
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands

from constants.paldea_galar_dict import legendary_mons, rarity_meta
from constants.celestial_constants import (
    CELESTIAL_ROLES,
    CELESTIAL_SERVER_ID,
    CELESTIAL_TEXT_CHANNELS,
    KHY_USER_ID,
)
from constants.server_currency import (
    CURRENCY_EMOJI,
    CURRENCY_NAME,
    POINT_MAP,
    RAFFLE_TICKET_EMOJI,
    SHOP_COLOR,
)
from utils.cache.cache_list import server_currency_cache, processed_rare_catches
from utils.db.server_currency_db import (
    update_currency,
    upsert_server_currency,
    user_exists_in_server_currency,
)

from utils.functions.pokemeow_reply import get_pokemeow_reply_member
from utils.functions.pretty_defer import pretty_defer
from utils.functions.role_checks import is_clan_member, is_staff_member
from utils.functions.webhook_func import send_webhook_log
from utils.functions.burger_shop import is_burger_shop_ongoing
from utils.logs.pretty_log import pretty_log


TEST_LOG_ID = 1455090114240708711
REAL_LOG_ID = CELESTIAL_TEXT_CHANNELS.burger_shop_log
BOT_LOG_ID = TEST_LOG_ID

SHINY_COLOR = 16751052
LEGENDARY_COLOR = 10487800
EVENT_EXCLUSIVE_COLOR = 15345163
FISHING_COLOR = 8900346
LOW_RARITY_COLORS = [
    rarity_meta["rare"]["color"],
    rarity_meta["superrare"]["color"],
    rarity_meta["common"]["color"],
    rarity_meta["uncommon"]["color"],
]
VALID_COLOR = [SHINY_COLOR, EVENT_EXCLUSIVE_COLOR, LEGENDARY_COLOR]
LOWER_RARITY_EXCLUSIVE = [
    "sprigatito",
    "fuecoco",
    "quaxly",
    "lechonk",
    "swirlix",
    "yamper",
]
EVENT_EXCLUSIVE_MON = [
    "hoopa-unbound"
]

LOWER_RARITIES = ["common", "uncommon", "rare", "superrare", "super rare"]

from datetime import datetime
from zoneinfo import ZoneInfo


# ❀─────────────────────────────────────────❀
#      Extract Rarity from Footer
# ❀─────────────────────────────────────────❀
def extract_rarity_from_footer(footer_text: str) -> str:
    # Extract rarity from embed footer
    rarity_match = re.search(r"Rarity:\s*([A-Za-z ]+)", footer_text)
    if rarity_match:
        rarity = rarity_match.group(1).strip().lower().replace(" ", "")
        pretty_log(
            "info",
            f"Extracted rarity from footer: {rarity}",
        )
        return rarity
    else:
        pretty_log(
            "info",
            f"Could not extract rarity from footer: {footer_text}",
        )
        return None


# ❀─────────────────────────────────────────❀
#      Extract Member Username from Embed
# ❀─────────────────────────────────────────❀
def extract_member_username_from_embed(embed: discord.Embed) -> str | None:
    """
    Extracts the username from the embed author name, e.g. "Congratulations, frayl!" -> "frayl".
    Returns None if not found.
    """
    if embed.author and embed.author.name:
        # Try 'Congratulations, username!' first
        match = re.search(r"Congratulations, ([^!]+)!", embed.author.name)
        if match:
            return match.group(1).strip()
        # Fallback: 'Well done, username!'
        match = re.search(r"Well done, ([^!]+)!", embed.author.name)
        if match:
            return match.group(1).strip()
        # Fallback: 'Great work, username!'
        match = re.search(r"Great work, ([^!]+)!", embed.author.name)
        if match:
            return match.group(1).strip()
    return None


def extract_pokemon_name_from_description(description: str) -> str | None:
    """
    Extracts the Pokémon name from the embed description.
    Returns None if not found.
    """
    match = re.search(r"You caught a.*?\*\*([^*]+)\*\*", description)
    if match:
        name = match.group(1).strip()
        pretty_log(
            "info",
            f"Extracted Pokémon name: {name}",
        )
        return name
    return None


async def add_points_to_member(
    bot: discord.Client,
    member: discord.Member,
    points: int,
    display_pokemon_name: str,
    message: discord.Message,
    catch_type: str,
):
    """Add points to a clan member for catching a rarespawn."""
    member_id = member.id
    member_name = member.name
    image_url = message.embeds[0].image.url if message.embeds else None
    embed_color = message.embeds[0].color.value if message.embeds else SHOP_COLOR
    pretty_log(
        "debug",
        f"Checking server_currency_cache for member_id: {member_id} (type: {type(member_id)}). Current cache keys: {[k for k in server_currency_cache.keys()]}",
    )
    user_currency_info = server_currency_cache.get(member_id)
    if not user_currency_info:
        # Double-check DB if not in cache

        user_exists = await user_exists_in_server_currency(bot, member_id)
        if user_exists:
            # User exists in DB, reload cache and update
            from utils.cache.server_currency_cache import load_server_currency_cache

            await load_server_currency_cache(bot)
            user_currency_info = server_currency_cache.get(member_id)
            if user_currency_info:
                current_balance = user_currency_info.get("currency", 0)
                new_balance = current_balance + points
                await update_currency(
                    bot=bot,
                    user_id=member_id,
                    currency=new_balance,
                )
                pretty_log(
                    "info",
                    f"Added {points} {CURRENCY_NAME} to {member_name} ({member_id}). New balance: {new_balance} {CURRENCY_NAME}.",
                )
            else:
                # Fallback: treat as new
                await upsert_server_currency(
                    bot=bot,
                    user_id=member_id,
                    user_name=member_name,
                    currency=points,
                )
                new_balance = points
                pretty_log(
                    "info",
                    f"Created server currency entry for {member_name} ({member_id}) with {points} {CURRENCY_NAME}.",
                )
        else:
            # User truly does not exist, upsert
            await upsert_server_currency(
                bot=bot,
                user_id=member_id,
                user_name=member_name,
                currency=points,
            )
            new_balance = points
            pretty_log(
                "info",
                f"Created server currency entry for {member_name} ({member_id}) with {points} {CURRENCY_NAME}.",
            )
    else:
        # Update balance
        current_balance = user_currency_info.get("currency", 0)
        new_balance = current_balance + points
        await update_currency(
            bot=bot,
            user_id=member_id,
            currency=new_balance,
        )
        pretty_log(
            "info",
            f"Added {points} {CURRENCY_NAME} to {member_name} ({member_id}). New balance: {new_balance} {CURRENCY_NAME}.",
        )

    # Send log to log channel
    log_channel = bot.get_channel(BOT_LOG_ID)
    embed = discord.Embed(
        title="Rare Catch Detected",
        url=message.jump_url,
        color=embed_color,
        description=(
            f"- **Member:** {member.mention}\n"
            f"- **Pokemon:** {display_pokemon_name}\n"
            f"- **Catch Type:** {catch_type}\n"
            f"- **Reward:** {points} {CURRENCY_EMOJI}\n"
            f"- **New Balance:** {new_balance} {CURRENCY_EMOJI}\n"
        ),
        timestamp=datetime.now(),
    )
    if image_url:
        embed.set_thumbnail(url=image_url)
    embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)

    if log_channel:
        await log_channel.send(embed=embed)

    # Send Message to Member
    await message.channel.send(embed=embed)


async def handle_rarespawn_catch(
    bot: discord.Client,
    before_message: discord.Message,
    after_message: discord.Message,
):
    if not is_burger_shop_ongoing():
        return

    embed = after_message.embeds[0] if after_message.embeds else None
    if not embed:
        return

    embed_color = embed.color.value
    embed_description = embed.description or ""
    embed_footer = embed.footer.text or ""

    rarity = None
    guild = after_message.guild

    # check if rare spawn based on color and description
    if embed_color in LOW_RARITY_COLORS:
        return

    # Identify the user who caught the rarespawn
    member = await get_pokemeow_reply_member(before_message)
    if not member:
        # Extract username from embed as fallback
        username = extract_member_username_from_embed(embed)
        if not username:
            return
        from utils.cache.celestial_members_cache import (
            fetch_user_id_by_user_name_or_pokemon_name_cache,
        )

        user_id = fetch_user_id_by_user_name_or_pokemon_name_cache(username)
        if not user_id:
            return
        member = guild.get_member(user_id)
        if not member:
            return

    if after_message.id in processed_rare_catches:
        return
    processed_rare_catches.add(after_message.id)

    # Check if clan member
    clan_role = guild.get_role(CELESTIAL_ROLES.celestialnova_)
    donated_role = guild.get_role(CELESTIAL_ROLES.tip_jar_titan)

    # Check if member has donated role and clan role
    if (not clan_role or clan_role not in member.roles) and (not donated_role or donated_role not in member.roles):
        return

    # Extract pokemon name
    rarity = None
    pokemon_name = extract_pokemon_name_from_description(embed_description)
    if not pokemon_name:
        return
    lower_pokemon_name = pokemon_name.lower()
    if lower_pokemon_name in LOWER_RARITY_EXCLUSIVE:
        return

    if lower_pokemon_name in EVENT_EXCLUSIVE_MON:
        catch_type = "event_exclusive"
        rarity = extract_rarity_from_footer(embed_footer)
        if rarity and rarity.lower() == "super rare":
            rarity = "superrare"
            return  # Not a rare catch
        elif rarity and rarity.lower() == "shiny":
            rarity = "shiny"
            pokemon_name = pokemon_name.replace("Shiny ", "")  # Clean for display
        pretty_log(
            "info",
            f"Event exclusive rarespawn caught: {pokemon_name} by {member.name}",
        )

    elif embed_color == EVENT_EXCLUSIVE_COLOR:
        catch_type = "event_exclusive"
        rarity = extract_rarity_from_footer(embed_footer)
        # Block both 'super rare' and 'superrare' (with or without spaces)
        if rarity and rarity.lower().replace(" ", "") == "superrare":
            return  # Not a rare catch

        pretty_log(
            "info",
            f"Identified event exclusive catch: {pokemon_name}, Rarity: {rarity}",
        )

        if rarity and rarity.lower().replace(" ", "") in [
            r.replace(" ", "") for r in LOWER_RARITIES
        ]:
            pretty_log(
                "info",
                f"Event exclusive catch is of lower rarity ({rarity}): {pokemon_name}",
            )
            return  # Not a rare catch

    elif embed_color == SHINY_COLOR:
        rarity = "shiny"
        catch_type = "shiny"
        if "on event shiny encounter" in embed_footer.lower():
            catch_type = "event_exclusive"

        pokemon_name = pokemon_name.replace("Shiny ", "")  # Clean for display

        pretty_log(
            "info",
            f"Shiny rarespawn caught: {pokemon_name} by {member.name}",
        )
    elif embed_color == LEGENDARY_COLOR:
        rarity = "legendary"
        catch_type = "legendary"
        pretty_log(
            "info",
            f"Legendary rarespawn caught: {pokemon_name} by {member.name}",
        )
    elif embed_color not in VALID_COLOR and embed_color != FISHING_COLOR:
        rarity = extract_rarity_from_footer(embed_footer)
        if rarity.lower() == "legendary":
            catch_type = "legendary"
            pretty_log(
                "info",
                f"Identified legendary catch from footer: {pokemon_name}",
            )
        else:
            pretty_log(
                "info",
                f"Catch is neither shiny, event exclusive, nor legendary: {pokemon_name}",
            )
            return  # Not a rare catch
    elif embed_color == FISHING_COLOR:
        pretty_log(
            "info",
            f"Processing fishing catch for Pokémon: {pokemon_name}",
        )
        if "Golden" in embed_description:
            rarity = "golden"
            catch_type = "fishing_golden"
            pokemon_name = pokemon_name.replace("Golden ", "")  # Clean for display
            pretty_log(
                "info",
                f"Golden fishing rarespawn caught: {pokemon_name} by {member.name}",
            )

        elif "Shiny" in embed_description:
            rarity = "shiny"
            catch_type = "fishing_shiny"
            pokemon_name = pokemon_name.replace("Shiny ", "")  # Clean for display
            pretty_log(
                "info",
                f"Shiny fishing rarespawn caught: {pokemon_name} by {member.name}",
            )
        elif pokemon_name in legendary_mons:
            catch_type = "fishing_legendary"
            rarity = "legendary"
            pretty_log(
                "info",
                f"Identified fishing legendary catch: {pokemon_name}",
            )
        else:
            pretty_log(
                "info",
                f"Fishing catch is neither golden, exclusive, shiny, nor legendary: {pokemon_name}",
            )
            return  # Not a rare fishing catch
    else:
        pretty_log(
            "info",
            f"Catch does not meet rare criteria: {pokemon_name}",
        )
        return  # Not a rare catch

    # Determine points to award
    points = POINT_MAP.get(catch_type, 0)
    rarity_emoji = rarity_meta.get(rarity, {}).get("emoji", "")
    pokemon_name = pokemon_name.title()
    display_pokemon_name = (
        f"{rarity_emoji} {pokemon_name}" if rarity_emoji else pokemon_name
    )
    context = catch_type.replace("_", " ").title()

    # Add points to member
    await add_points_to_member(
        bot=bot,
        member=member,
        points=points,
        display_pokemon_name=display_pokemon_name,
        message=after_message,
        catch_type=context,
    )

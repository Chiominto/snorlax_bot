from random import randint


import discord

from constants.celestial_constants import (
    CELESTIAL_ROLES,
    CELESTIAL_SERVER_ID,
    CELESTIAL_TEXT_CHANNELS,
    KHY_USER_ID,
    POKEMEOW_APPLICATION_ID
)
from constants.server_currency import (
    CURRENCY_EMOJI,
    CURRENCY_NAME,
)
from utils.cache.cache_list import server_currency_cache
from utils.db.server_currency_db import (
    update_currency,
    upsert_server_currency,
    user_exists_in_server_currency,
)

from utils.functions.pokemeow_reply import get_pokemeow_reply_member, get_pokemeow_reply_two
from utils.logs.debug_log import debug_log, enable_debug
from utils.functions.webhook_func import send_webhook_log
from utils.functions.burger_shop import is_burger_shop_ongoing
from utils.logs.pretty_log import pretty_log

enable_debug(f"{__name__}.quest_helper_listener")

points = 1


async def quest_helper_listener(
    bot: discord.Client, message: discord.Message
):
    if message.author.id != POKEMEOW_APPLICATION_ID:
        return

    # Make it bypass if the context is testing
    if not is_burger_shop_ongoing():
        return

    member = await get_pokemeow_reply_two(message)
    if not member:
        return

    # Only in quest helper channel
    if message.channel.id != CELESTIAL_TEXT_CHANNELS.quest_help:
        return

    guild = message.guild
    member_id = member.id
    member_name = member.name

    clan_member_role = guild.get_role(CELESTIAL_ROLES.celestialnova_)

    # Only members with the clan member role or sakura bear role can earn points
    if clan_member_role not in member.roles:
        debug_log(
            f"Member {member} does not have the required role to earn points.",
        )
        return

    # 20% chance to earn points (for testing)
    random_num = randint(1, 100)
    if random_num <= 20:
        # Earn points
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
            current_balance = user_currency_info.get("balance", 0)
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
        content = f"{member.mention} earned {points} {CURRENCY_EMOJI} for helping with the quest! You now have {new_balance} {CURRENCY_EMOJI}."
        replied_message = message.reference and message.reference.resolved
        (
            await replied_message.reply(content=content)
            if replied_message
            else await message.channel.send(content=content)
        )
        pretty_log(
            "info",
            f"Sent quest helper reward for {member_name} ({member_id}).",
        )
    else:
        pretty_log(
            "info",
            f"{member_name} ({member_id}) did not earn points this time (random number: {random_num}).",
        )

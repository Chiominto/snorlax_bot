import math
from datetime import datetime

import discord
from discord.ext import commands

from constants.celestial_constants import CELESTIAL_SERVER_ID, DEFAULT_EMBED_COLOR
from constants.server_currency import CURRENCY_EMOJI
from utils.cache.cache_list import server_currency_cache
from utils.db.server_currency_db import upsert_user_currency, upsert_server_currency
from utils.functions.pretty_defer import pretty_defer
from utils.functions.webhook_func import send_webhook
from utils.logs.pretty_log import pretty_log
from utils.logs.server_log import send_log_to_server_log
SHOP_COLOR = DEFAULT_EMBED_COLOR
async def give_balance_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    receiver: discord.Member,
    amount: int,
):
    """Gives another member your server currency balance, with 10% tax applied."""

    # Defer the interaction to allow more time for processing
    loader = await pretty_defer(
        interaction=interaction,
        content="Processing balance transfer...",
        ephemeral=False,
    )

    giver = interaction.user
    receiver = receiver

    # Check if giver has enough balance
    giver_data = server_currency_cache.get(giver.id)
    if not giver_data or giver_data.get("currency", 0) < amount:
        await loader.error("You do not have enough currency to complete this transfer.")
        return

    # Minimum amount of 10 currency to give
    if amount < 10:
        await loader.error("You must give at least 10 currency.")
        return

    # Calculate tax and final amount
    tax_rate = 0.10

    tax_amount = math.ceil(amount * tax_rate)
    final_amount = amount - tax_amount
    if final_amount <= 0:
        await loader.error("The amount after tax must be greater than zero.")
        return

    # Update balances in the database
    giver_balance = giver_data.get("currency")
    giver_new_balance = giver_balance - amount
    receiver_data = server_currency_cache.get(receiver.id)
    # Upsert receiver data if not exists
    if not receiver_data:
        await upsert_server_currency(
            bot=bot,
            user_id=receiver.id,
            user_name=receiver.name,
            currency=0,
            fry_points=0,
        )
        receiver_data = server_currency_cache.get(receiver.id)
    receiver_balance = receiver_data.get("currency", 0)
    receiver_new_balance = receiver_balance + final_amount

    await upsert_user_currency(
        bot=bot,
        user_id=receiver.id,
        user_name=receiver.name,
        currency=receiver_new_balance,
    )

    await upsert_user_currency(
        bot=bot,
        user_id=giver.id,
        user_name=giver.name,
        currency=giver_new_balance,
    )

    # Success embed
    embed = discord.Embed(
        title=f" {CURRENCY_EMOJI} Balance Transfer Successful!",
        color=SHOP_COLOR,
        description=(
            f"**Giver:** {giver.mention}\n"
            f"**Receiver:** {receiver.mention}\n"
            f"**Amount Given:** {amount} {CURRENCY_EMOJI}\n"
            f"**Tax Applied (10%):** {tax_amount} {CURRENCY_EMOJI}\n"
            f"**Final Amount Received:** {final_amount} {CURRENCY_EMOJI}\n\n"
            f"**{giver.name}'s New Balance:** {giver_new_balance} {CURRENCY_EMOJI}\n"
            f"**{receiver.name}'s New Balance:** {receiver_new_balance} {CURRENCY_EMOJI}"
        ),
        timestamp=datetime.now(),
    )
    await loader.success(embed=embed, content="")

    # Log the transfer via webhook
    guild = interaction.guild
    await send_log_to_server_log(
        bot=bot,
        embed=embed,
    )
    pretty_log(
        "info",
        f"{giver.name} ({giver.id}) gave {amount} {CURRENCY_EMOJI} to "
        f"{receiver.name} ({receiver.id}) with {tax_amount} {CURRENCY_EMOJI} tax applied.",
        label="Server Currency",
    )

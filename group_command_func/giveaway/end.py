import discord

from utils.db.ga_db import fetch_giveaway_row_by_message_id
from utils.functions.pretty_defer import pretty_defer
from utils.functions.role_checks import *
from utils.giveaway.giveaway_end_func import end_giveaway_handler
from utils.logs.pretty_log import pretty_log


async def end_giveaway_func(
    bot: discord.Client, interaction: discord.Interaction, message_id: str
):
    message_id = int(message_id)  # Convert message_id to int
    # Defer response early since this can take a while
    loader = await pretty_defer(
        interaction=interaction, content="Ending giveaway...", ephemeral=True
    )
    # Check if staff
    if not is_staff_member(interaction.user):
        await loader.error(content="You do not have permission to end giveaways.")
        return

    giveaway_row = await fetch_giveaway_row_by_message_id(bot, message_id)

    if not giveaway_row:
        pretty_log(
            "error",
            f"No giveaway found for message ID {message_id}",
        )
        await loader.error(
            content="No giveaway found for this message.",
        )
        return

    # End giveaway and pick winners
    try:
        winners = await end_giveaway_handler(bot, message_id)
        if winners:
            await loader.success(content="Giveaway ended! Winners have been picked.")
        else:
            await loader.error(
                content="No entries found or giveaway not found for message."
            )
    except Exception as e:
        pretty_log(
            "error",
            f"Error ending giveaway for message ID {message_id}: {e}",
            include_trace=True,
        )
        await loader.error(content="An error occurred while ending the giveaway.")
        return

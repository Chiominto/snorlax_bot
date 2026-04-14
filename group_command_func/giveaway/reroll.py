import discord

from constants.aesthetics import *
from utils.db.ga_db import fetch_giveaway_row_by_message_id
from utils.db.ga_entry_db import fetch_entries_by_giveaway
from utils.functions.pretty_defer import pretty_defer
from utils.functions.role_checks import *
from utils.giveaway.giveaway_end_func import reroll_giveaway_handler
from utils.logs.pretty_log import pretty_log


async def reroll_giveaway_func(
    bot: discord.Client,
    interaction: discord.Interaction,
    message_id: str,
    reroll_count: int,
):
    message_id = int(message_id)  # Convert message_id to int
    # Defer response early since this can take a while
    loader = await pretty_defer(
        interaction=interaction, content="Rerolling giveaway...", ephemeral=True
    )
    # Check if staff
    if not is_staff_member(interaction.user):
        await loader.error(content="You do not have permission to reroll giveaways.")
        return

    giveaway_row = await fetch_giveaway_row_by_message_id(bot, message_id)
    giveaway_id = giveaway_row["giveaway_id"] if giveaway_row else None

    if not giveaway_row:
        pretty_log(
            "error",
            f"No giveaway found for message ID {message_id}",
        )
        await loader.error(
            content="No giveaway found for this message.",
        )
        return
    entries = await fetch_entries_by_giveaway(bot, giveaway_id)
    if not entries:
        pretty_log(
            "error",
            f"No entries found for giveaway ID {giveaway_id}",
            label="Reroll Giveaway Handler",
        )
        await loader.error(
            content="No entries found for this giveaway. Cannot reroll.",
        )
        return

    # Reroll giveaway and pick new winners
    try:
        success, error_msg = await reroll_giveaway_handler(
            bot,
            reroll_count,
            giveaway_row,
            entries,
        )
        if success:
            await loader.success(
                content="Giveaway rerolled! New winners have been picked."
            )
            return
        else:
            await loader.error(
                content=error_msg or "An error occurred while rerolling the giveaway."
            )
    except Exception as e:
        pretty_log(
            "error",
            f"Error rerolling giveaway for message ID {message_id}: {e}",
            include_trace=True,
        )

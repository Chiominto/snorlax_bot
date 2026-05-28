import discord

from constants.celestial_constants import (
    CELESTIAL_ROLES,
    CELESTIAL_SERVER_ID,
    CELESTIAL_TEXT_CHANNELS,
)
from constants.server_currency import FRY_POINT_EMOJI
from utils.db.server_currency_db import (
    fetch_all_fry_points,
    get_all_people_with_most_fry_points,
    reset_all_fry_points_only,
)
from utils.db.temp_roles_db import fetch_temp_role_by_role_id
from utils.logs.pretty_log import pretty_log


async def make_fry_point_leaderboard(bot: discord.Client):
    """Fetches all fry points from the database, sorts them, and returns a formatted leaderboard string."""
    fry_points_data = await fetch_all_fry_points(bot)
    if not fry_points_data:
        pretty_log(
            "error",
            "No fry points found while building leaderboard.",
            label="FRY POINT RESET",
        )
        return None
    guild = bot.get_guild(CELESTIAL_SERVER_ID)

    # Sort the data by fry points in descending order
    sorted_data = sorted(fry_points_data, key=lambda x: x["fry_points"], reverse=True)

    # Build the leaderboard string
    embed = discord.Embed(
        title="🍟 Fry Point Leaderboard 🍟", color=discord.Color.gold()
    )
    total_users = len(sorted_data)

    embed.set_footer(text=f"Total users with fry points: {total_users}")
    for index, entry in enumerate(sorted_data[:10], start=1):
        user_id = entry["user_id"]
        fry_points = entry["fry_points"]
        user = bot.get_user(user_id)
        member = None
        if user is None and guild:
            member = guild.get_member(user_id)
        display_name = None
        mention = None
        username = None
        if user:
            display_name = user.display_name
            mention = user.mention
            username = user.name
        elif member:
            display_name = member.display_name
            mention = member.mention
            username = member.name
        else:
            # fallback to user_id as string
            display_name = f"User {user_id}"
            mention = f"<@{user_id}>"
            username = f"User {user_id}"
        field_value = f"> - {mention}\n> - {fry_points} {FRY_POINT_EMOJI}"
        field_name = f"{index}. {display_name} | {username}"
        if index == 1:
            field_name = f"🥇 {display_name} | {username}"
        elif index == 2:
            field_name = f"🥈 {display_name} | {username}"
        elif index == 3:
            field_name = f"🥉 {display_name} | {username}"
        embed.add_field(name=field_name, value=field_value, inline=False)
    return embed


async def fry_point_reset(bot: discord.Client):
    """Announces the members with the most fry points and resets all fry points to zero."""
    top_fry_points = await get_all_people_with_most_fry_points(bot)
    if not top_fry_points:
        pretty_log(
            "info", "No fry points data found to reset.", label="FRY POINT RESET"
        )
        return

    guild = bot.get_guild(CELESTIAL_SERVER_ID)
    if not guild:
        pretty_log(
            "error",
            "Guild not found. Cannot announce fry point reset.",
            label="FRY POINT RESET",
        )
        return
    golden_fry_disciple_role = (
        guild.get_role(CELESTIAL_ROLES.golden_fry_disciple) if guild else None
    )
    # Get the previous top fry point holder
    previous_top_holder_id = await fetch_temp_role_by_role_id(
        bot, CELESTIAL_ROLES.golden_fry_disciple
    )
    if previous_top_holder_id:
        previous_top_holder = guild.get_member(previous_top_holder_id)
        if previous_top_holder:
            # Remove the golden fry disciple role from the previous top holder
            if golden_fry_disciple_role in previous_top_holder.roles:
                try:
                    await previous_top_holder.remove_roles(
                        golden_fry_disciple_role,
                        reason="Fry point reset - removing old top holder role",
                    )
                    pretty_log(
                        "info",
                        f"Removed Golden Fry Disciple role from previous top holder {previous_top_holder.display_name} ({previous_top_holder.id})",
                        label="FRY POINT RESET",
                    )
                except discord.HTTPException as e:
                    pretty_log(
                        "error",
                        f"Failed to remove Golden Fry Disciple role from previous top holder: {e}",
                        label="FRY POINT RESET",
                    )

    # Channel
    news_channel = bot.get_channel(CELESTIAL_TEXT_CHANNELS.clan_annoucement)
    if not news_channel:
        pretty_log(
            "error",
            "News channel not found. Cannot announce fry point reset.",
            label="FRY POINT RESET",
        )
        return
    golden_fry_disciple_role = guild.get_role(CELESTIAL_ROLES.golden_fry_disciple)

    #  Get leaderboard embed
    leaderboard_message = f"""🍟 THE FRY PRAYING SHRINE HAS SPOKEN 🍟

The sacred fryer oil has settled… the golden potatoes have been counted… and the Fry Elders have revealed this month’s most devoted worshippers. 🙏✨"""
    leaderboard_embed = await make_fry_point_leaderboard(bot)
    if leaderboard_embed is None:
        pretty_log(
            "error",
            "Failed to build fry point leaderboard. Aborting fry point reset.",
            label="FRY POINT RESET",
        )
        return

    # Prepare the announcement message
    message = None
    tie_message = None
    if len(top_fry_points) == 1:
        winner = top_fry_points[0]
        user_id = winner["user_id"]
        points = winner["fry_points"]
        user = bot.get_user(user_id)
        member = guild.get_member(user_id)
        winner_mention = (
            user.mention if user else (member.mention if member else f"<@{user_id}>")
        )

        # Assign the golden fry disciple role to the new top holder
        if golden_fry_disciple_role and member:
            try:
                await member.add_roles(
                    golden_fry_disciple_role,
                    reason="Fry point reset - assigning new top holder role",
                )
                pretty_log(
                    "info",
                    f"Assigned Golden Fry Disciple role to new top holder {member.display_name} ({member.id})",
                    label="FRY POINT RESET",
                )
            except discord.HTTPException as e:
                pretty_log(
                    "error",
                    f"Failed to assign Golden Fry Disciple role to new top holder: {e}",
                    label="FRY POINT RESET",
                )
        message = f"""👑🍟 ALL HAIL THE SUPREME FRY DISCIPLE 🍟👑

After countless prayers, dangerous levels of grease inhalation, and unwavering devotion to the sacred fryer… {winner_mention} has officially claimed 1ST PLACE at the Fry Praying Shrine with **__{points}__** {FRY_POINT_EMOJI}. 🙏✨

The Fry Gods reportedly said:
“Yeah… this one’s definitely addicted.”

Their fries remain forever crispy.

Their prayers echoed louder than the fryer alarm itself.

Side effects of winning may include:
• Sudden god complex
• Smelling like McDonald’s fries permanently
• Random visions of potatoes
• Being worshipped by lower fry disciples

Everyone congratulate {winner_mention} for becoming this month’s High Priest of the Holy Fry Shrine 🍟✨"""

    elif len(top_fry_points) > 1:
        tied_members = []
        tied_points = top_fry_points[0]["fry_points"] if top_fry_points else 0
        for entry in top_fry_points:
            tied_user_id = entry["user_id"]
            tied_user = bot.get_user(tied_user_id)
            tied_member = guild.get_member(tied_user_id)
            tied_name = (
                tied_user.mention
                if tied_user
                else (tied_member.mention if tied_member else f"<@{tied_user_id}>")
            )
            tied_members.append(f"• {tied_name}")

        tie_message = (
            "Hey clan staff, we have a tie for the most fry points this month. "
            f"Each has **{tied_points}** {FRY_POINT_EMOJI}:\n"
            + "\n".join(tied_members)
            + f"\nPlease decide how to handle the tie and announce it in {news_channel.mention}."
        )

    # Send the leaderboard announcement then the message if its not None
    try:
        if leaderboard_embed:
            await news_channel.send(
                content=leaderboard_message, embed=leaderboard_embed
            )
        if message:
            await news_channel.send(content=message)
        if tie_message:
            # Ask clan staff to decide how to handle ties and include tied members
            staff_room_channel = bot.get_channel(CELESTIAL_TEXT_CHANNELS.moderator_only)
            if staff_room_channel:
                await staff_room_channel.send(content=tie_message)
        # Reset fry points after announcing the leaderboard
        await reset_all_fry_points_only(bot)

    except discord.HTTPException as e:
        pretty_log(
            "error",
            f"Failed to send fry point reset announcement: {e}",
            label="FRY POINT RESET",
        )
        return

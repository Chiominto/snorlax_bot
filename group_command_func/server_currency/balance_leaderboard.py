import discord
from discord.ext import commands
from discord.ui import Button, View

from constants.celestial_constants import CELESTIAL_SERVER_ID, DEFAULT_EMBED_COLOR
from constants.server_currency import CURRENCY_EMOJI, FRY_POINT_EMOJI
from utils.cache.cache_list import server_currency_cache
from utils.db.server_currency_db import fetch_all_server_currency
from utils.functions.pretty_defer import pretty_defer

SHOP_COLOR = DEFAULT_EMBED_COLOR


class Leaderboard_Paginator(View):
    def __init__(self, bot, user, sorted_balances, type, per_page=10, timeout=120):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.user = user
        self.sorted_balances = sorted_balances
        self.type = type
        self.per_page = per_page
        self.page = 0
        self.max_page = (len(sorted_balances) - 1) // per_page
        self.message: discord.Message | None = None  # Store the sent message

        # If only one page, remove all buttons
        if self.max_page == 0:
            self.clear_items()

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary)
    async def previous_page(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message(
                "You cannot interact with this paginator.", ephemeral=True
            )
        if self.page > 0:
            self.page -= 1
            embed = await self.get_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message(
                "You cannot interact with this paginator.", ephemeral=True
            )
        if self.page < self.max_page:
            self.page += 1
            embed = await self.get_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()

    async def get_embed(self):
        start_index = self.page * self.per_page
        end_index = start_index + self.per_page
        page_balances = self.sorted_balances[start_index:end_index]

        rank_offset = start_index + 1
        title = f"Celestial Server Currency Leaderboard"
        embed = discord.Embed(
            title=title,
            color=SHOP_COLOR,
        )
        guild = self.bot.get_guild(CELESTIAL_SERVER_ID)  # Get the guild object
        total_users = len(self.sorted_balances)
        embed.set_footer(
            text=f"Page {self.page + 1} of {self.max_page + 1} | Total Users: {total_users}",
            icon_url=guild.icon.url if guild and guild.icon else None,
        )
        for i, (user_id, balance) in enumerate(page_balances, start=rank_offset):
            user = self.bot.get_user(user_id)
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

            balance_info = server_currency_cache.get(user_id)
            balance_str = f"> - {balance} {CURRENCY_EMOJI}\n"

            fry_points = balance_info.get("fry_points", 0) if balance_info else 0
            fry_points_str = (
                f"> - {fry_points} {FRY_POINT_EMOJI}" if fry_points > 0 else ""
            )
            if self.type.lower() == "starry meal":
                fry_points_str = ""  # Hide fry points if type is starry meal
            if self.type.lower() == "fry points":
                balance_str = ""  # Hide currency if type is fry points

            field_value_str = f"> - {mention}\n{balance_str}{fry_points_str}"
            field_name = f"{i}. {display_name} | {username}"
            if i == 1:
                field_name = f"🥇 {display_name} | {username}"
            elif i == 2:
                field_name = f"🥈 {display_name} | {username}"
            elif i == 3:
                field_name = f"🥉 {display_name} | {username}"
            embed.add_field(name=field_name, value=field_value_str, inline=False)
        return embed

    async def on_timeout(self):
        # Disable all buttons on timeout
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except (discord.NotFound, discord.HTTPException):
                pass


async def balance_leaderboard_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    type: str = "all",
):
    """
    Show the balance leaderboard for the server currency.
    """
    # Defer the interaction to allow more time for processing

    loader = await pretty_defer(
        interaction=interaction,
        content=f"Fetching {type.lower()} balance leaderboard...",
        ephemeral=False,
    )
    type = type.lower()
    # Fetch and sort balances
    user_balances = await fetch_all_server_currency(bot=bot)
    if not user_balances:
        await loader.error("No balance data found.")
        return

    fry_points_map = {
        row["user_id"]: row.get("fry_points") or 0 for row in user_balances
    }

    # Filter out users with all values as 0 or None; keep if any is > 0
    if type.lower() == "starry meal":
        filtered_balances = [
            (row["user_id"], row.get("fry_points") or 0)
            for row in user_balances
            if (row.get("fry_points") or 0) > 0 or (row.get("currency") or 0) > 0
        ]
    elif type.lower() == "fry points":
        filtered_balances = [
            (row["user_id"], row.get("fry_points") or 0)
            for row in user_balances
            if (row.get("fry_points") or 0) > 0
        ]
    else:
        filtered_balances = [
            (row["user_id"], row.get("currency") or 0)
            for row in user_balances
            if (row.get("currency") or 0) > 0 or (row.get("fry_points") or 0) > 0
        ]

    # Sort by balance descending
    if type == "all" and filtered_balances:
        all_starry_meal_zero = all(balance == 0 for _, balance in filtered_balances)

        if all_starry_meal_zero:
            sorted_balances = sorted(
                filtered_balances,
                key=lambda x: fry_points_map.get(x[0], 0),
                reverse=True,
            )
        else:
            sorted_balances = sorted(
                filtered_balances,
                key=lambda x: (x[1], fry_points_map.get(x[0], 0)),
                reverse=True,
            )
    else:
        sorted_balances = sorted(filtered_balances, key=lambda x: x[1], reverse=True)

    # Create paginator
    paginator = Leaderboard_Paginator(bot, interaction.user, sorted_balances, type=type)
    embed = await paginator.get_embed()
    sent_message = await loader.success(embed=embed, view=paginator, content="")
    paginator.message = sent_message

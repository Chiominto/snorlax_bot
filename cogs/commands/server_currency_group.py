from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands

from utils.functions.role_checks import *
from utils.functions.command_safe import run_command_safe
from group_command_func.server_currency import *


# 💠────────────────────────────────────────────
# [🟣 COG] Server Currency Group Cog
# ─────────────────────────────────────────────
class ServerCurrencyCommandGroup(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    balance_group = app_commands.Group(
        name="balance",
        description="Commands related to the server currency",
    )

    # 🌐───────────────────────────────────────
    # [🌐 COMMAND] /balance view
    # ───────────────────────────────────────
    @balance_group.command(
        name="view",
        description="View your server currency balance",
    )
    @app_commands.describe(
        member="The member whose balance you want to view (Staff only)",
    )
    async def balance_view(
        self,
        interaction: discord.Interaction,
        member: discord.Member = None,
    ):
        slash_cmd_name = "balance view"
        await run_command_safe(
            command_func=view_balance_func,
            slash_cmd_name=slash_cmd_name,
            bot=self.bot,
            interaction=interaction,
            member=member,
        )

    balance_view.extras = {"category": "Public"}

    # 🌐───────────────────────────────────────
    # [🌐 COMMAND] /balance add
    # ───────────────────────────────────────
    @balance_group.command(
        name="add",
        description="Add server currency to a member's balance",
    )
    @app_commands.describe(
        member="The member to whom you want to add currency",
        starry_meal="The amount of starry meal to add",
        fry_points="The amount of fry points to add",
    )
    async def balance_add(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        starry_meal: int = None,
        fry_points: int = None,
    ):
        slash_cmd_name = "balance add"
        await run_command_safe(
            command_func=add_balance_func,
            slash_cmd_name=slash_cmd_name,
            bot=self.bot,
            interaction=interaction,
            member=member,
            starry_meal=starry_meal,
            fry_points=fry_points,
        )

    balance_add.extras = {"category": "Staff"}

    # 🌐───────────────────────────────────────
    # [🌐 COMMAND] /balance remove
    # ───────────────────────────────────────
    @balance_group.command(
        name="remove",
        description="Remove server currency from a member's balance",
    )
    @app_commands.describe(
        member="The member from whom you want to remove currency",
        starry_meal="The amount of starry meal to remove",
        fry_points="The amount of fry points to remove",
    )
    async def balance_remove(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        starry_meal: int = None,
        fry_points: int = None,
    ):
        slash_cmd_name = "balance remove"
        await run_command_safe(
            command_func=remove_balance_func,
            slash_cmd_name=slash_cmd_name,
            bot=self.bot,
            interaction=interaction,
            member=member,
            starry_meal=starry_meal,
            fry_points=fry_points,
        )

    balance_remove.extras = {"category": "Staff"}

    # 🌐───────────────────────────────────────
    # [🌐 COMMAND] /balance reset
    # ───────────────────────────────────────
    @balance_group.command(
        name="reset",
        description="Resets everyone's server currency balances",
    )
    async def balance_reset(
        self,
        interaction: discord.Interaction,
    ):
        slash_cmd_name = "balance reset"
        await run_command_safe(
            command_func=reset_all_balances_func,
            slash_cmd_name=slash_cmd_name,
            bot=self.bot,
            interaction=interaction,
        )

    balance_reset.extras = {"category": "Staff"}

    # 🌐───────────────────────────────────────
    # [🌐 COMMAND] /balance leaderboard
    # ───────────────────────────────────────
    @balance_group.command(
        name="leaderboard",
        description="Show the balance leaderboard for the server currency",

    )
    @app_commands.describe(
        type="The type of leaderboard to show.",
    )
    async def balance_leaderboard(
        self,
        interaction: discord.Interaction,
        type: Literal["All", "Starry Meal", "Fry Points"] = "all",
    ):
        slash_cmd_name = "balance leaderboard"
        await run_command_safe(
            command_func=balance_leaderboard_func,
            slash_cmd_name=slash_cmd_name,
            bot=self.bot,
            interaction=interaction,
            type=type,
        )

    balance_leaderboard.extras = {"category": "Public"}

    # 🌐───────────────────────────────────────
    # [🌐 COMMAND] /balance give
    # ───────────────────────────────────────
    @balance_group.command(
        name="give",
        description="Give another member your server currency balance, with 10% tax applied",
    )
    @app_commands.describe(
        receiver="The member to whom you want to give currency",
        amount="The amount of currency to give (Mimimum 10)",
    )
    async def balance_give(
        self,
        interaction: discord.Interaction,
        receiver: discord.Member,
        amount: int,
    ):
        slash_cmd_name = "balance give"
        await run_command_safe(
            command_func=give_balance_func,
            slash_cmd_name=slash_cmd_name,
            bot=self.bot,
            interaction=interaction,
            receiver=receiver,
            amount=amount,
        )

    balance_give.extras = {"category": "Public"}


async def setup(bot: commands.Bot):
    await bot.add_cog(ServerCurrencyCommandGroup(bot))

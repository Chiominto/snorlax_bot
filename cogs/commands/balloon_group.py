from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands

from utils.functions.command_safe import run_command_safe
from group_command_func.balloon import *
from utils.db.balloon_prizes_db import balloon_name_autocomplete
from utils.cache.pokemon_cache import pokemon_autocomplete

# 💠────────────────────────────────────────────
# [🟣 COG] Balloon Commands Group Cog
# ─────────────────────────────────────────────
class BalloonCommandGroup(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    balloon_group = app_commands.Group(
        name="balloon",
        description="Balloon related commands for managing balloon prizes",
    )

    # 🌐───────────────────────────────────────
    # [🌐 COMMAND] /balloon add
    # ───────────────────────────────────────
    @balloon_group.command(
        name="add",
        description="Add an item to a balloon (Staff only)",
    )
    @app_commands.autocomplete(balloon_name=balloon_name_autocomplete)
    @app_commands.autocomplete(item_name=pokemon_autocomplete)
    @app_commands.describe(
        balloon_name="The name of the balloon to which you want to add an item",
        item_name="The name of the item you want to add to the balloon",
        stock="The stock of the item to add (default is 1)",
    )
    async def balloon_add(
        self,
        interaction: discord.Interaction,
        balloon_name: str,
        item_name: str,
        stock: int = 1,
    ):
        slash_cmd_name = "balloon add"
        await run_command_safe(
            command_func=add_item_func,
            slash_cmd_name=slash_cmd_name,
            bot=self.bot,
            interaction=interaction,
            balloon_name=balloon_name,
            item_name=item_name,
            stock=stock,
        )
    balloon_add.extras = {"category": "Staff"}


    # 🌐───────────────────────────────────────
    # [🌐 COMMAND] /balloon multi-add
    # ───────────────────────────────────────
    @balloon_group.command(
        name="multi-add",
        description="Add multiple items to a balloon at once (Staff only)",
    )
    @app_commands.autocomplete(balloon_name=balloon_name_autocomplete)
    @app_commands.autocomplete(item_1=pokemon_autocomplete)
    @app_commands.autocomplete(item_2=pokemon_autocomplete)
    @app_commands.autocomplete(item_3=pokemon_autocomplete)
    @app_commands.autocomplete(item_4=pokemon_autocomplete)
    @app_commands.autocomplete(item_5=pokemon_autocomplete)
    @app_commands.autocomplete(item_6=pokemon_autocomplete)
    @app_commands.autocomplete(item_7=pokemon_autocomplete)
    @app_commands.autocomplete(item_8=pokemon_autocomplete)
    @app_commands.autocomplete(item_9=pokemon_autocomplete)
    @app_commands.autocomplete(item_10=pokemon_autocomplete)

    @app_commands.describe(
        balloon_name="The name of the balloon to which you want to add items",
        item_1="The first item to add to the balloon",
        item_2="The second item to add to the balloon (optional)",
        item_3="The third item to add to the balloon (optional)",
        item_4="The fourth item to add to the balloon (optional)",
        item_5="The fifth item to add to the balloon (optional)",
        item_6="The sixth item to add to the balloon (optional)",
        item_7="The seventh item to add to the balloon (optional)",
        item_8="The eighth item to add to the balloon (optional)",
        item_9="The ninth item to add to the balloon (optional)",
        item_10="The tenth item to add to the balloon (optional)",
    )
    async def balloon_multi_add(
        self,
        interaction: discord.Interaction,
        balloon_name: str,
        item_1: str,
        item_2: str = None,
        item_3: str = None,
        item_4: str = None,
        item_5: str = None,
        item_6: str = None,
        item_7: str = None,
        item_8: str = None,
        item_9: str = None,
        item_10: str = None,
    ):
        slash_cmd_name = "balloon multi-add"
        await run_command_safe(
            command_func=multi_add_item_func,
            slash_cmd_name=slash_cmd_name,
            bot=self.bot,
            interaction=interaction,
            balloon_name=balloon_name,
            item_1=item_1,
            item_2=item_2,
            item_3=item_3,
            item_4=item_4,
            item_5=item_5,
            item_6=item_6,
            item_7=item_7,
            item_8=item_8,
            item_9=item_9,
            item_10=item_10,
        )
    balloon_multi_add.extras = {"category": "Staff"}

    # 🌐───────────────────────────────────────
    # [🌐 COMMAND] /balloon remove
    # ───────────────────────────────────────
    @balloon_group.command(
        name="remove",
        description="Remove an item from a balloon (Staff only)",
    )
    @app_commands.autocomplete(balloon_name=balloon_name_autocomplete)
    @app_commands.describe(
        balloon_name="The name of the balloon from which you want to remove an item",
        item_name="The name of the item you want to remove from the balloon",
    )
    async def balloon_remove(
        self,
        interaction: discord.Interaction,
        balloon_name: str,
        item_name: str,
    ):
        slash_cmd_name = "balloon remove"
        await run_command_safe(
            command_func=remove_item_func,
            slash_cmd_name=slash_cmd_name,
            bot=self.bot,
            interaction=interaction,
            balloon_name=balloon_name,
            item_name=item_name,
        )
    balloon_remove.extras = {"category": "Staff"}

    # 🌐───────────────────────────────────────
    # [🌐 COMMAND] /balloon list
    # ───────────────────────────────────────
    @balloon_group.command(
        name="list",
        description="List all items in a balloon",
    )
    async def balloon_list(
        self,
        interaction: discord.Interaction,
    ):
        slash_cmd_name = "balloon list"
        await run_command_safe(
            command_func=list_item_func,
            slash_cmd_name=slash_cmd_name,
            bot=self.bot,
            interaction=interaction,
        )
    balloon_list.extras = {"category": "Staff"}

async def setup(bot: commands.Bot):
    await bot.add_cog(BalloonCommandGroup(bot))

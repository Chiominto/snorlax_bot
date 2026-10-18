from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands

from utils.cache.pokemon_cache import pokemon_autocomplete
from utils.db.server_shop_db import shop_item_autocomplete
from utils.functions.command_safe import run_command_safe
from group_command_func.server_shop import *


# 💠────────────────────────────────────────────
# [🟣 COG] Shop Command Group Cog
# ─────────────────────────────────────────────
class ShopCommandGroup(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    shop_group = app_commands.Group(
        name="shop",
        description="Commands related to the server shop",
    )

    # 🌐───────────────────────────────────────
    # [🌐 COMMAND] /shop add
    # ───────────────────────────────────────
    @shop_group.command(
        name="add",
        description="Add an item to the server shop",
    )
    @app_commands.autocomplete(item_name=pokemon_autocomplete)  # 👈 attach autocomplete
    @app_commands.describe(
        item_name="The name of the item to add",
        price="The price of the item in server currency",
        stock="The stock quantity of the item",
        description="A description of the item",
        image_link="An optional image link for the item",
    )
    async def shop_add_item(
        self,
        interaction: discord.Interaction,
        item_name: str,
        price: int,
        stock: int,
        description: str = None,
        image_link: str = None,
    ):
        slash_cmd_name = "shop add"
        await run_command_safe(
            command_func=add_item_func,
            slash_cmd_name=slash_cmd_name,
            bot=self.bot,
            interaction=interaction,
            item_name=item_name,
            price=price,
            stock=stock,
            description=description,
            image_link=image_link,
        )

    shop_add_item.extras = {"category": "Staff"}

    # 🌐───────────────────────────────────────
    # [🌐 COMMAND] /shop buy
    # ───────────────────────────────────────
    @shop_group.command(
        name="buy",
        description="Buy an item from the server shop",
    )
    @app_commands.autocomplete(
        item_name=shop_item_autocomplete
    )  # 👈 attach autocomplete
    @app_commands.describe(
        item_name="The name of the item to buy",
        amount="The amount of the item to buy",
    )
    async def shop_buy_item(
        self,
        interaction: discord.Interaction,
        item_name: str,
        amount: int = 1,
    ):
        slash_cmd_name = "shop buy"
        await run_command_safe(
            command_func=buy_item_func,
            slash_cmd_name=slash_cmd_name,
            bot=self.bot,
            interaction=interaction,
            item_name=item_name,
            amount=amount,
        )

    shop_buy_item.extras = {"category": "Public"}

    # 🌐───────────────────────────────────────
    # [🌐 COMMAND] /shop view
    # ───────────────────────────────────────
    @shop_group.command(
        name="view",
        description="View an item or the server shop",
    )
    @app_commands.autocomplete(
        item_name=shop_item_autocomplete
    )  # 👈 attach autocomplete
    @app_commands.describe(
        item_name="The name of the item to view (leave blank to view all items)",
    )
    async def shop_view_item(
        self,
        interaction: discord.Interaction,
        item_name: str = None,
    ):
        slash_cmd_name = "shop view"
        await run_command_safe(
            command_func=shop_view_func,
            slash_cmd_name=slash_cmd_name,
            bot=self.bot,
            interaction=interaction,
            item_name=item_name,
        )

    shop_view_item.extras = {"category": "Public"}

    # 🌐───────────────────────────────────────
    # [🌐 COMMAND] /shop edit
    # ───────────────────────────────────────
    @shop_group.command(
        name="edit",
        description="Edit an existing item in the server shop",
    )
    @app_commands.autocomplete(
        item_name=shop_item_autocomplete
    )  # 👈 attach autocomplete
    @app_commands.describe(
        item_name="The name of the item to edit",
        new_price="The new price of the item",
        new_stock="The new stock quantity of the item",
        new_description="The new description of the item",
        new_image_link="The new image link for the item",
    )
    async def shop_edit_item(
        self,
        interaction: discord.Interaction,
        item_name: str,
        new_price: int = None,
        new_stock: int = None,
        new_description: str = None,
        new_image_link: str = None,
    ):
        slash_cmd_name = "shop edit"
        await run_command_safe(
            command_func=edit_item_func,
            slash_cmd_name=slash_cmd_name,
            bot=self.bot,
            interaction=interaction,
            item_name=item_name,
            new_price=new_price,
            new_stock=new_stock,
            new_description=new_description,
            new_image_link=new_image_link,
        )

    shop_edit_item.extras = {"category": "Staff"}

    # 🌐───────────────────────────────────────
    # [🌐 COMMAND] /shop remove
    # ───────────────────────────────────────
    @shop_group.command(
        name="remove",
        description="Remove an item from the server shop",
    )
    @app_commands.autocomplete(
        item_name=shop_item_autocomplete
    )  # 👈 attach autocomplete
    @app_commands.describe(
        item_name="The name of the item to remove",
    )
    async def shop_remove_item(
        self,
        interaction: discord.Interaction,
        item_name: str,
    ):
        slash_cmd_name = "shop remove"
        await run_command_safe(
            command_func=remove_item_func,
            slash_cmd_name=slash_cmd_name,
            bot=self.bot,
            interaction=interaction,
            item_name=item_name,
        )

    shop_remove_item.extras = {"category": "Staff"}

    # 🌐───────────────────────────────────────
    # [🌐 COMMAND] /shop clear
    # ───────────────────────────────────────
    @shop_group.command(
        name="clear",
        description="Clear all items from the server shop",
    )
    async def shop_clear_items(
        self,
        interaction: discord.Interaction,
    ):
        slash_cmd_name = "shop clear"
        await run_command_safe(
            command_func=shop_clear_func,
            slash_cmd_name=slash_cmd_name,
            bot=self.bot,
            interaction=interaction,
        )

    shop_clear_items.extras = {"category": "Staff"}


async def setup(bot: commands.Bot):
    await bot.add_cog(ShopCommandGroup(bot))


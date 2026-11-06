from datetime import datetime

import discord
from discord.ext import commands
from discord.ui import Button, View

from constants.celestial_constants import (
    CELESTIAL_ROLES,
    CELESTIAL_SERVER_ID,
    CELESTIAL_TEXT_CHANNELS,
    KHY_USER_ID
)
from constants.server_currency import CURRENCY_EMOJI, CURRENCY_NAME, SHOP_COLOR
from utils.cache.cache_list import server_shop_cache
from utils.db.server_shop_db import format_item_name
from utils.functions.pretty_defer import pretty_defer
from utils.functions.role_checks import *
from utils.functions.webhook_func import send_webhook_log
from utils.logs.pretty_log import pretty_log
from utils.functions.burger_shop import check_burger_shop
from .buy import fetch_dex, is_shop_closed, is_shop_opened


class Shop_Paginator(View):
    def __init__(self, bot, user, items, per_page=10, timeout=120):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.user = user
        self.items = items
        self.per_page = per_page
        self.page = 0
        self.max_page = (len(items) - 1) // per_page
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
        start = self.page * self.per_page
        end = start + self.per_page
        page_items = self.items[start:end]

        title = "Infusion Server Shop"
        embed = discord.Embed(
            title=title,
            color=SHOP_COLOR,
            timestamp=datetime.now(),
        )
        for idx, item in enumerate(page_items):
            number = idx + 1 + start
            item_id = item.get("item_id", 0)
            item_name = item.get("item_name", "Unknown Item")
            price = item.get("price", 0)
            stock = item.get("stock", 0)
            stock_display = "Unlimited" if stock == -1 else str(stock)
            desc_line = item.get("description")
            dex = item.get("dex")
            if not dex or dex == "N/A":
                dex = await fetch_dex(
                    bot=self.bot,
                    item_name=item_name,
                    item_id=item_id,
                )
            if dex and dex != "N/A":
                has_dex = True
            else:
                has_dex = False

            item_name = format_item_name(item_name)
            item_name = f"{item_name} (Dex: #{dex})" if has_dex else item_name
            if desc_line:
                desc_line_str = f"\n> - Description: {desc_line}"
            else:
                desc_line_str = ""

            embed.add_field(
                name=f"{number}. {item_name}",
                value=f"> - ID: {item_id}\n> - Price: {price} {CURRENCY_EMOJI}\n> - Stock: {stock_display}{desc_line_str}",
                inline=False,
            )
        total_items = len(self.items)
        guild = self.bot.get_guild(CELESTIAL_SERVER_ID)
        embed.set_footer(
            text=f"Page {self.page + 1}/{self.max_page + 1} | Total Items: {total_items}",
            icon_url=guild.icon.url if guild else None,
        )
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


async def shop_view_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    item_name: str = None,
):
    """
    View an item or the server shop.
    """
    # Determine if shop is currently ongoing, only staff can bypass this check
    if not await check_burger_shop(interaction):
        return

    try:
        item_str = "All items"
        all_items = True
        if item_name:
            item_str = item_name
            all_items = False
        # Defer the interaction to allow more time for processing
        loader = await pretty_defer(
            interaction=interaction,
            content=f"Fetching details for {item_str}...",
            ephemeral=False,
        )
        if not all_items:
            # Check if item exists
            from utils.cache.server_shop_cache import fetch_item_id_by_name

            item_id = fetch_item_id_by_name(item_name)
            if not item_id:
                await loader.error(
                    f"No item with the name '{item_name}' exists in the server shop."
                )
                return

            # Get item details
            item_info = server_shop_cache.get(item_id)
            if not item_info:
                await loader.error(
                    "Failed to retrieve item details from cache. Please try again later."
                )
                return
            price = item_info.get("price", 0)
            stock = item_info.get("stock", 0)
            description = item_info.get("description", "No description.")
            image_link = item_info.get("image_link")
            dex = item_info.get("dex")
            if not dex or dex == "N/A":
                dex = await fetch_dex(
                    bot=bot,
                    item_name=item_name,
                    item_id=item_id,
                )
            if dex and dex != "N/A":
                has_dex = True
            else:
                has_dex = False
            item_name = format_item_name(item_name)
            item_name = f"{item_name} (Dex: #{dex})" if has_dex else item_name
            # Create embed
            description_str = ""
            if description:
                description_str = f"> - **Description:** {description}\n"
            embed = discord.Embed(
                title=f"Infusion Server Shop",
                color=SHOP_COLOR,
                description=(
                    f"**Name:** {item_name}\n"
                    f"> - **ID:** {item_id}\n"
                    f"> - **Price:** {price} {CURRENCY_EMOJI}\n"
                    f"> - **Stock:** {stock}\n"
                    f"{description_str}"
                ),
                timestamp=datetime.now(),
            )
            embed.set_author(
                name=interaction.user.display_name,
                icon_url=interaction.user.display_avatar.url,
            )
            if image_link:
                embed.set_thumbnail(url=image_link)
            await loader.success(embed=embed, content="")
            return

        else:
            # Show all items in the shop
            from utils.cache.server_shop_cache import \
                fetch_all_shop_items_cache

            items = fetch_all_shop_items_cache()
            if not items:
                await loader.error("The server shop is currently empty.")
                return

            # Convert dict to list and include item_id in each item dict, then sort by price then name
            items_list = (
                [{**item, "item_id": item_id} for item_id, item in items.items()]
                if isinstance(items, dict)
                else items
            )
            items_list.sort(
                key=lambda x: (
                    x.get("price", float("inf")),
                    x.get("item_name", "").lower(),
                )
            )
            paginator = Shop_Paginator(
                bot=bot,
                user=interaction.user,
                items=items_list,
                per_page=10,
                timeout=120,
            )
            embed = await paginator.get_embed()
            sent_message = await loader.success(
                embed=embed,
                content="",
                view=paginator,
            )
            paginator.message = sent_message  # Store the sent message in the paginator
    except Exception as e:
        pretty_log(
            "error",
            f"Error in shop_view_func: {e}",
            label="Server Shop",
        )
        await interaction.followup.send(
            "An unexpected error occurred while fetching the server shop. Please try again later.",
            ephemeral=True,
        )
        return

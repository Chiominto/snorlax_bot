import random
from datetime import datetime
from types import CellType
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands

from constants.celestial_constants import (BURGER_SHOP_STAFF, CELESTIAL_ROLES,
                                           CELESTIAL_TEXT_CHANNELS)
from constants.server_currency import (BALLOON_POP_IMAGE, CURRENCY_EMOJI,
                                       CURRENCY_NAME, RAFFLE_TICKET_EMOJI,
                                       SHOP_COLOR, balloon_emoji_map,
                                       dart_balloon_map, dart_names)
from utils.cache.cache_list import server_currency_cache, server_shop_cache
from utils.cache.global_flags import TESTING_BURGER_SHOP_EVENT
from utils.db.balloon_prizes_db import (fetch_balloon_prizes_by_balloon,
                                        fetch_total_stock_for_balloon,
                                        remove_balloon_prize,
                                        update_balloon_prize_stock)
from utils.db.server_currency_db import update_currency
from utils.db.server_shop_db import (format_item_name, remove_item, update_dex,
                                     update_stock)
from utils.functions.pokemon_func import (get_dex_number_by_name,
                                          get_display_name)
from utils.functions.pretty_defer import pretty_defer
from utils.functions.role_checks import is_burger_shop_staff
from utils.functions.webhook_func import send_webhook, send_webhook_log
from utils.logs.debug_log import debug_log, enable_debug
from utils.logs.pretty_log import pretty_log

processing_dart_purchase = set()  # To track users currently purchasing
BOBA_USER_ID = 214920903887159296
BOBA_CHANNEL = 1117651671594569818
enable_debug(f"{__name__}.buy_item_func")
enable_debug(f"{__name__}.dart_purchase_handler")
enable_debug(f"{__name__}.process_balloon_pop_embed")
enable_debug(f"{__name__}.process_purchase")

def is_event_ongoing() -> bool:
    """
    Returns True if the current date is between April 1st, 2026 12:00 AM EST and May 1st, 2026 12:00 AM EST.
    """
    now = datetime.now(ZoneInfo("America/New_York"))
    event_start = datetime(2026, 4, 1, 0, 0, 0, tzinfo=ZoneInfo("America/New_York"))
    event_end = datetime(2026, 4, 30, 0, 0, 0, tzinfo=ZoneInfo("America/New_York"))
    return event_start <= now < event_end


def is_user_id_burger_shop_staff(user_id):
    return user_id in BURGER_SHOP_STAFF


async def dart_purchase_handler(
    bot: discord.Client,
    loader,
    dart_name: str,
    user: discord.Member,
    testing: bool = False,

):
    """Function to pop a balloon when a dart is purchased."""
    debug_log(
        f"Initiating dart purchase handler for dart '{dart_name}' with testing={testing}."
    )


    # Get balloon options based on dart type
    balloon_options = dart_balloon_map.get(dart_name.lower(), [])
    debug_log(f"Balloon options for dart '{dart_name}': {balloon_options}")

    if not balloon_options:
        pretty_log(
            "error",
            f"No balloon options found for dart '{dart_name}'. Cannot pop balloon.",
            label="Server Shop",
        )
        debug_log(
            f"No balloon options found for dart '{dart_name}'. Removing from processing set and returning error."
        )
        processing_dart_purchase.remove(dart_name)
        await loader.error(
            "An error occurred while processing your purchase. Please try again later."
        )
        return

    # Validate if the balloon still has stock before popping
    balloons_with_stock = []
    for balloon in balloon_options:
        total_stock = await fetch_total_stock_for_balloon(bot, balloon)
        debug_log(f"Total stock for balloon '{balloon}': {total_stock}")
        pretty_log(
            "debug",
            f"Total stock for balloon '{balloon}' is {total_stock}.",
            label="Server Shop",
        )
        if total_stock > 0:
            balloons_with_stock.append(balloon)
    debug_log(f"Balloons with stock for dart '{dart_name}': {balloons_with_stock}")
    if not balloons_with_stock:
        pretty_log(
            "warning",
            f"All balloon options for dart '{dart_name}' are out of stock. Cannot pop balloon.",
            label="Server Shop",
        )
        debug_log(
            f"All balloon options for dart '{dart_name}' are out of stock. Removing from processing set and returning error."
        )
        processing_dart_purchase.remove(dart_name)
        await loader.error(
            "All balloon options for this dart are currently out of stock. Please try again later."
        )
        return
    embed = discord.Embed(
        title="Choose a Balloon to Pop!",
        description="Select one of the balloons below to pop and reveal your prize!",
        color=SHOP_COLOR,
    )
    debug_log(
        f"Creating BalloonPopView for dart '{dart_name}' with balloons: {balloons_with_stock}"
    )
    view = BalloonPopView(
        balloon_options=balloons_with_stock,
        bot=bot,
        user=user,
        dart_name=dart_name,
        testing=testing,
    )
    debug_log(f"Sending loader.success for dart '{dart_name}'.")

    pop_message = await loader.success(content="", embed=embed, view=view)
    # Fetch the message object from the interaction and set it in the view
    try:
        pop_message = await loader.interaction.original_response()
        debug_log(f"dart_purchase_handler: pop_message fetched: {pop_message}")
        view.message = pop_message
        debug_log(f"dart_purchase_handler: view.message set to {view.message}")
    except Exception as e:
        debug_log(f"dart_purchase_handler: Failed to fetch/set view.message: {e}")


async def process_balloon_pop_embed(
    bot: discord.Client,
    user: discord.Member,
    dart_name: str,
    balloon_name: str,
    testing: bool,
    message: discord.Message = None,
):
    """Randomly selects a prize from the balloon and sends an embed to the user."""
    user_id = user.id
    user_name = user.name
    try:
        debug_log(
            f"process_balloon_pop_embed called for user '{getattr(user, 'id', user)}', dart '{dart_name}', balloon '{balloon_name}', testing={testing}, message='{getattr(message, 'id', message)}'."
        )
        pop_ballon_embed = discord.Embed(
            title=f"Popping the {balloon_name.title()}...",
            color=SHOP_COLOR,
        )
        pop_ballon_embed.set_image(url=BALLOON_POP_IMAGE)
        if message:
            await message.edit(embed=pop_ballon_embed, view=None)

        debug_log(f"Fetching prizes for balloon '{balloon_name}'...")
        prizes = await fetch_balloon_prizes_by_balloon(bot, balloon_name)
        debug_log(f"Fetched prizes: {prizes}")
        # Get a random prize from the list
        if not prizes:
            debug_log(f"No prizes found for balloon '{balloon_name}'. Aborting pop.")
            pretty_log(
                "error",
                f"No prizes found for balloon '{balloon_name}'. Cannot process balloon pop.",
                label="Server Shop",
            )
            processing_dart_purchase.remove(dart_name)
            return

        # Get a random prize from the list of prize dicts
        prize_info = random.choice(prizes)
        debug_log(f"Selected prize_info: {prize_info}")
        prize_name = prize_info.get("prize")
        image_link = prize_info.get("image_link")
        prize_stock = prize_info.get("stock", 0)
        debug_log(
            f"Prize name: {prize_name}, image_link: {image_link}, prize_stock: {prize_stock}"
        )

        # Remove the prize from the box in the database
        try:
            new_stock = prize_stock - 1
            debug_log(
                f"Updating/removing prize '{prize_name}' in DB. New stock: {new_stock}"
            )
            if new_stock > 0:
                await update_balloon_prize_stock(
                    bot=bot,
                    balloon_name=balloon_name,
                    prize=prize_name,
                    new_stock=new_stock,
                )
                pretty_log(
                    tag="info",
                    message=f"✅ Decreased stock of prize '{prize_name}' in box '{balloon_name}' to {new_stock} after opening.",
                    label="🎁 BOX PRIZE",
                )
            else:
                await remove_balloon_prize(
                    bot=bot, balloon_name=balloon_name, prize=prize_name
                )
                pretty_log(
                    tag="info",
                    message=f"✅ Successfully removed prize '{prize_name}' from box '{balloon_name}' after opening.",
                    label="🎁 BOX PRIZE",
                )
        except Exception as e:
            debug_log(f"Exception while updating/removing prize: {e}")
            pretty_log(
                tag="error",
                message=f"❌ Failed to remove prize '{prize_name}' from box '{balloon_name}' after opening. Error: {e}",
                label="🎁 BOX PRIZE",
            )
            processing_dart_purchase.remove(dart_name)
            error_message = f"⚠️ An error occurred while opening the box. Please try again later."
            return False, None, None, error_message

        # Prepare description for the prize
        prize_name_formatted = get_display_name(prize_name, dex=True)
        debug_log(f"Prize display name: {prize_name_formatted}")

        # Check if item exists
        from utils.cache.server_shop_cache import fetch_item_id_by_name

        item_id = fetch_item_id_by_name(dart_name)
        item_info = server_shop_cache.get(item_id)
        debug_log(f"Item info for dart '{dart_name}': {item_info}")
        price = item_info.get("price", 0) if item_info else None
        stock = item_info.get("stock", 0) if item_info else None
        user_balance_info = server_currency_cache.get(user_id, 0)
        if not isinstance(user_balance_info, dict):
            user_balance = 0
            user_raffle_tickets = 0
        else:
            user_balance = user_balance_info.get("currency", 0)
            user_raffle_tickets = user_balance_info.get("raffle_ticket", 0)
        debug_log(
            f"User: {user_name} (ID: {user_id}), balance: {user_balance}, raffle_tickets: {user_raffle_tickets}"
        )
        amount = 1  # can only purchase one dart at a time, so amount is always 1
        ballon_prize_desc = f"You popped a {balloon_name.title()} Balloon and got **{prize_name_formatted}**!"
        debug_log(
            f"Calling process_purchase for user '{user_name}' and dart '{dart_name}'..."
        )
        await process_purchase(
            bot=bot,
            user=user,
            item_name=dart_name,
            item_id=item_id,
            item_info=item_info,
            amount=amount,
            user_balance=user_balance,
            user_raffle_tickets=user_raffle_tickets,
            dart_description=ballon_prize_desc,
            balloon_prize_image_link=image_link,
            ballon_pop_message=message,
            dart_name=dart_name,
        )
    except Exception as e:
        debug_log(f"Exception in process_balloon_pop_embed: {e}")
        pretty_log(
            tag="error",
            message=f"❌ Exception in process_balloon_pop_embed for user '{getattr(user, 'id', user)}', dart '{dart_name}', balloon '{balloon_name}': {e}",
            label="🎁 BOX PRIZE",
        )
        processing_dart_purchase.remove(dart_name)
        error_message = f"⚠️ An error occurred while processing your balloon pop. Please try again later."
        return False, None, None, error_message


class BalloonButton(discord.ui.Button):
    def __init__(
        self,
        balloon_name,
        bot: discord.Client,
        user: discord.Member,
        dart_name: str,
        label: str,
        emoji: str,
        testing: bool,
        message: discord.Message,
    ):
        super().__init__(label=label, emoji=emoji, style=discord.ButtonStyle.primary)
        self.bot = bot
        self.balloon_name = balloon_name
        self.user = user
        self.dart_name = dart_name
        self.testing = testing
        self.message = message

    async def callback(self, interaction: discord.Interaction):
        from utils.logs.debug_log import debug_log, enable_debug

        # Restrict to only the user who bought the balloon
        if self.user is not None and interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "Only the user who bought this can pop the balloon!", ephemeral=True
            )
            debug_log(
                f"BalloonButton.callback: User {interaction.user} attempted to pop balloon but is not the buyer (buyer: {self.user})."
            )
            return

        debug_log(
            f"BalloonButton.callback triggered for balloon '{self.balloon_name}' and dart '{self.dart_name}' by user '{interaction.user}'."
        )
        embed = discord.Embed(
            title=f"Popping the {self.balloon_name.title()} Balloon...",
        )
        embed.set_image(url=BALLOON_POP_IMAGE)
        await interaction.response.edit_message(embed=embed, view=None)
        # Always use the user from the interaction, not self.user (which may be None)
        # Pass the up-to-date message from the parent view
        await process_balloon_pop_embed(
            self.bot,
            self.user,
            self.dart_name,
            self.balloon_name,
            self.testing,
            getattr(self.view, "message", None),
        )


class BalloonPopView(discord.ui.View):
    def __init__(
        self,
        balloon_options,
        bot: discord.Client,
        user: discord.Member,
        dart_name: str,
        testing: bool,
    ):
        super().__init__(timeout=60)  # View will timeout after 60 seconds
        self.bot = bot
        self.user = user
        self.dart_name = dart_name
        self.testing = testing
        self.message = None  # To store the message object after sending the embed

        for balloon in balloon_options:
            balloon_display_name = balloon.title()  # Capitalize for display
            balloon_emoji = balloon_emoji_map.get(balloon, "")
            self.add_item(
                BalloonButton(
                    bot=bot,
                    user=user,
                    dart_name=dart_name,
                    balloon_name=balloon,
                    label=balloon_display_name,
                    emoji=balloon_emoji,
                    testing=testing,
                    message=self.message,
                )
            )


async def fetch_dex(bot: discord.Client, item_name: str, item_id: str):
    """Fetch the Dex number for a given item name if it corresponds to a Pokémon."""
    dex_number = get_dex_number_by_name(item_name)
    if dex_number:
        await update_dex(
            bot=bot,
            item_id=item_id,
            dex=dex_number,
        )
        pretty_log(
            "info",
            f"Updated Dex number for item '{item_name}' (ID: {item_id}) to {dex_number}.",
            label="Server Shop",
        )
        return dex_number
    return None


def is_shop_opened():
    now = datetime.now(ZoneInfo("America/New_York"))
    shop_opening = datetime(
        year=2026,
        month=4,
        day=1,
        hour=0,
        minute=0,
        second=0,
        tzinfo=ZoneInfo("America/New_York"),
    )
    return now >= shop_opening


def is_shop_closed() -> bool:
    """
    Returns True if the shop is closed
    """
    now = datetime.now(ZoneInfo("America/New_York"))
    shop_closing = datetime(
        year=2026,
        month=5,
        day=1,
        hour=0,
        minute=0,
        second=0,
        tzinfo=ZoneInfo("America/New_York"),
    )
    return now >= shop_closing


async def process_purchase(
    bot: commands.Bot,
    user: discord.Member,
    item_name: str,
    item_id: int,
    item_info: dict,
    amount: int,
    user_balance: int,
    user_raffle_tickets: int,
    dart_description: str = None,
    balloon_prize_image_link: str = None,
    ballon_pop_message: discord.Message = None,
    dart_name: str = None,
):
    """
    Handle purchase logic: stock checks, balance updates, raffle tickets,
    logging, and embed creation.
    """
    user_id = getattr(user, "id", None)

    price = item_info.get("price", 0)
    stock = item_info.get("stock", 0)
    image_link = item_info.get("image_link")
    dex = item_info.get("dex", None)
    is_dart = item_name.lower() in [d.lower() for d in dart_names]

    # --- Validation ---
    debug_log(
        f"process_purchase: price={price}, stock={stock}, image_link={image_link}, dex={dex}, is_dart={is_dart}, user_balance={user_balance}, balloon_prize_image_link={balloon_prize_image_link}, ballon_pop_message='{getattr(ballon_pop_message, 'id', ballon_pop_message)}'"
    )
    if stock != -1 and amount > stock:
        debug_log(
            f"Insufficient stock for {item_name}. Requested: {amount}, Available: {stock}."
        )
        return (
            False,
            f"Insufficient stock for {item_name}. Requested: {amount}, Available: {stock}.",
            None,
        )
    if amount <= 0:
        debug_log(f"Invalid amount to buy: {amount}")
        return False, "The amount to buy must be at least 1.", None

    total_price = price * amount
    debug_log(f"Total price: {total_price}, user_balance: {user_balance}")
    if user_balance < total_price:
        debug_log(
            f"Not enough balance to buy {amount} {item_name}. User balance: {user_balance}, total price: {total_price}"
        )
        processing_dart_purchase.discard(dart_name)  # Ensure dart is removed from processing set on failure
        return (
            False,
            (
                f"You do not have enough {CURRENCY_NAME} to buy {amount} {item_name}. "
                f"Your balance: {user_balance} {CURRENCY_EMOJI}, "
                f"Total price: {total_price} {CURRENCY_EMOJI}."
            ),
            None,
        )

    # --- Balance Update ---
    new_balance = user_balance - total_price
    debug_log(f"Updating user balance to {new_balance}")
    await update_currency(bot=bot, user_id=user.id, currency=new_balance)


    # --- Item Name Formatting ---
    item_name_fmt = format_item_name(item_name)
    if dex and dex != "N/A":
        item_name_fmt = f"{item_name_fmt} (Dex: #{dex})"
    debug_log(f"item_name_fmt: {item_name_fmt}")

    # --- Stock Update ---
    if stock > 0:
        new_stock = stock - amount
        debug_log(f"Updating stock for item_id {item_id} to {new_stock}")
        """if not is_user_id_burger_shop_staff(
            user_id
        ):  # Don't update stock for staff (for testing purposes)"""
        await update_stock(bot=bot, item_id=item_id, stock=new_stock)
        if new_stock == 0 and not is_user_id_burger_shop_staff(
            user_id
        ):  # Remove item if out of stock (but not for staff)
            debug_log(f"Removing item_id {item_id} from shop (out of stock)")
            await remove_item(bot=bot, item_id=item_id)
            log_embed_title = f"{item_name_fmt} is Out of Stock"
        else:
            log_embed_title = f"Item Purchased: {item_name_fmt}"
    else:
        new_stock = stock
        log_embed_title = f"Item Purchased: {item_name_fmt}"
    debug_log(f"log_embed_title: {log_embed_title}")

    # --- Success Embed ---
    embed = discord.Embed(
        title="Purchase Successful",
        color=SHOP_COLOR,
        description=f"You have successfully purchased {amount} **{item_name_fmt}**!",
        timestamp=datetime.now(),
    )
    embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)

    embed.add_field(
        name="Total Price", value=f"{total_price} {CURRENCY_EMOJI}", inline=True
    )
    embed.add_field(
        name="New Balance", value=f"{new_balance} {CURRENCY_EMOJI}", inline=True
    )
    embed.add_field(name="Amount", value=str(amount), inline=True)


    if stock >= 0:
        embed.add_field(name="Remaining Stock", value=str(new_stock), inline=True)

    if is_dart and dart_description:
        embed.add_field(name="Balloon Prize", value=dart_description, inline=False)
    footer_text = "Please show this message to a staff member to claim your item."
    if is_dart and "rock" in dart_description.lower():
        footer_text = "Better luck next time!"

    embed.set_footer(text=footer_text)
    if image_link:
        embed.set_thumbnail(url=image_link)

    # --- Logging Embed ---
    log_embed = discord.Embed(
        title=log_embed_title,
        color=SHOP_COLOR,
        timestamp=datetime.now(),
    )
    log_embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)

    log_embed.add_field(name="Member", value=user.mention, inline=True)
    log_embed.add_field(name="Item", value=item_name_fmt, inline=True)
    log_embed.add_field(name="Amount", value=str(amount), inline=True)
    log_embed.add_field(
        name="Total Price", value=f"{total_price} {CURRENCY_EMOJI}", inline=True
    )
    log_embed.add_field(
        name="New Balance", value=f"{new_balance} {CURRENCY_EMOJI}", inline=True
    )
    log_embed.add_field(name="Remaining Stock", value=str(new_stock), inline=True)


    if is_dart and dart_description:
        log_embed.add_field(name="Balloon Prize", value=dart_description, inline=False)

    if is_dart and balloon_prize_image_link:
        log_embed.set_thumbnail(url=balloon_prize_image_link)
        embed.set_thumbnail(url=balloon_prize_image_link)
    else:
        if image_link:
            log_embed.set_thumbnail(url=image_link)

    if not is_user_id_burger_shop_staff(
        user_id
    ):  # Don't send webhook log for staff purchases (for testing purposes)
        await send_webhook_log(bot=bot, embed=log_embed)

    # --- Quest Notification ---
    if "quest" in item_name_fmt.lower():
        try:
            content = f"<@{BOBA_USER_ID}> {user.display_name} purchased a {item_name_fmt}. Please assist them!"
            channel = bot.get_channel(BOBA_CHANNEL)
            await channel.send(content=content, embed=log_embed)
        except Exception as e:
            pretty_log("error", f"Failed to notify Boba: {e}", label="Server Shop")

    if is_dart and ballon_pop_message:
        debug_log(
            f"Editing ballon_pop_message for user '{user.display_name}' with embed: {embed.to_dict()}"
        )
        # Edit the original purchase confirmation message to show the balloon pop embed and remove the view (buttons)
        try:
            await ballon_pop_message.edit(embed=embed, view=None)
            processing_dart_purchase.remove(dart_name)
            debug_log(
                f"Successfully edited ballon_pop_message for user '{user.display_name}'. Removed '{dart_name}' from processing set."
            )
        except Exception as e:
            debug_log(f"Exception while editing ballon_pop_message: {e}")
            pretty_log(
                "error",
                f"Failed to edit balloon pop message for user {user.display_name}: {e}",
                label="Server Shop",
            )
            processing_dart_purchase.remove(dart_name)
            debug_log(f"Removed '{dart_name}' from processing set due to exception.")

    # --- Offtopic Channel Notification ---
    offtopic_channel = bot.get_channel(CELESTIAL_TEXT_CHANNELS.burger_shop_log)
    if offtopic_channel and not is_user_id_burger_shop_staff(
        user_id
    ):  # Don't send off-topic notification for staff purchases (for testing purposes)
        await send_webhook(bot=bot, channel=offtopic_channel, embed=log_embed)

    return True, None, embed


async def buy_item_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    item_name: str,
    amount: int,
):
    """
    Buy an item from the server shop.
    """

    # Allow staff to access any time, members only if Jan 1st or later
    if not (is_shop_opened() or is_burger_shop_staff(interaction)):
        return await interaction.response.send_message(
            "The server shop is not yet open. Please wait for an update from the staff.",
            ephemeral=True,
        )

    # Close shop after Feb 15th and later
    if is_shop_closed() and not is_burger_shop_staff(interaction):
        return await interaction.response.send_message(
            "The server shop is currently closed. It will reopen at a later date. Please stay tuned for updates from the staff.",
            ephemeral=True,
        )

    # Defer the interaction to allow more time for processing
    loader = await pretty_defer(
        interaction=interaction,
        content="Processing your purchase...",
        ephemeral=False,
    )

    # Check if item exists
    from utils.cache.server_shop_cache import fetch_item_id_by_name

    item_id = fetch_item_id_by_name(item_name)
    if not item_id:
        await loader.error(
            f"No item with the name {item_name} exists in the server shop."
        )
        return

    # Get item details
    item_info = server_shop_cache.get(item_id)
    if not item_info:
        await loader.error(
            "Failed to retrieve item details from cache. Please try again later."
        )
        return

    # Get user details
    user = interaction.user
    user_id = user.id
    user_balance_info = server_currency_cache.get(user_id, 0)
    user_balance = user_balance_info.get("currency", 0)
    user_raffle_tickets = user_balance_info.get("raffle_ticket", 0)

    # Check if user has the probation role
    guild = interaction.guild
    probation_role = guild.get_role(CELESTIAL_ROLES.grounded)
    not_donated_role = guild.get_role(CELESTIAL_ROLES.coin_saver)
    if probation_role in user.roles or not_donated_role in user.roles:
        await loader.error(
            "You cannot purchase items while on probation. Please contact a staff member for more information."
        )
        return
    is_dart = item_name in dart_names

    # Delegate to reusable purchase processor
    if is_dart:
        # Check if balance is sufficient before proceeding with dart purchase flow
        price = item_info.get("price", 0)
        total_price = price * amount
        if user_balance < total_price:
            debug_log(
                f"Not enough balance to buy {amount} {item_name}. User balance: {user_balance}, total price: {total_price}"
            )
            await loader.error(
                (
                    f"You do not have enough {CURRENCY_NAME} to buy {amount} {item_name}. "
                    f"Your balance: {user_balance} {CURRENCY_EMOJI}, "
                    f"Total price: {total_price} {CURRENCY_EMOJI}."
                )
            )

            return
        if item_name in processing_dart_purchase:
            debug_log(
                f"Dart '{item_name}' is already being processed. Skipping to prevent race conditions."
            )
            await loader.error(
                "This dart is currently being processed. Please wait a moment and try again."
            )
            return
        debug_log(f"Adding '{item_name}' to processing_dart_purchase set.")
        processing_dart_purchase.add(item_name)
        await dart_purchase_handler(
            bot=bot,
            loader=loader,
            dart_name=item_name,
            user=user,
            testing=TESTING_BURGER_SHOP_EVENT,

        )
        return
    else:
        success, error_msg, embed = await process_purchase(
            bot=bot,
            user=user,
            item_name=item_name,
            item_id=item_id,
            item_info=item_info,
            amount=amount,
            user_balance=user_balance,
            user_raffle_tickets=user_raffle_tickets,
        )
        if not success:
            await loader.error(error_msg)
        else:
            await loader.success(content="", embed=embed)

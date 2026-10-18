import random
import string
from typing import List

import discord

from constants.paldea_galar_dict import rarity_meta
from constants.pokemons import *
from utils.logs.pretty_log import pretty_log

# SQL Script
"""CREATE TABLE server_shop (
id SERIAL PRIMARY KEY,
item_id VARCHAR(32),
item_name VARCHAR(100),
price INTEGER,
stock INTEGER,
description TEXT,
image_link TEXT
);"""

# Migration: add dex column if it doesn't exist
MIGRATION_SQL = """
ALTER TABLE server_shop ADD COLUMN IF NOT EXISTS dex TEXT;
"""

async def run_migrations(bot: discord.Client):
    """Run any pending schema migrations."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(MIGRATION_SQL)
            pretty_log("db", "server_shop migrations applied successfully.", bot=bot)
    except Exception as e:
        pretty_log("error", f"Failed to run server_shop migrations: {e}", bot=bot)

def generate_item_id(length=8):
    """Generate a random alphanumeric item_id of given length."""
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


async def fetch_item_by_name(bot: discord.Client, item_name: str) -> dict | None:
    """Fetch a shop item by name from the server_shop table."""

    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT item_id, item_name, price, stock, description, image_link, dex
                FROM server_shop
                WHERE item_name = $1
                """,
                item_name,
            )

            if row:
                pretty_log(
                    "db",
                    f"Fetched shop item: {item_name}",
                    bot=bot,
                )

                return {
                    "item_id": row["item_id"],
                    "item_name": row["item_name"],
                    "price": row["price"],
                    "stock": row["stock"],
                    "description": row["description"],
                    "image_link": row["image_link"],
                    "dex": row["dex"],
                }

            pretty_log(
                "db",
                f"No shop item found for item_name: {item_name}",
                bot=bot,
            )
            return None

    except Exception as e:
        pretty_log(
            "error",
            f"Failed to fetch shop item {item_name}: {e}",
            bot=bot,
        )
        return None

def format_item_name(item_name: str) -> str:
    """
    Format the item name for display.
    """
    LEGENDARY_ITEMS = ["keldeo-resolute", "zamazenta", "zygarde-10"]
    SUPERRARE_ITEMS = ["roaring-moon", "minior-blue", "gimmighoul"]
    UNCOMMON_ITEMS = ["toedscool", "lechonk", "pikachu"]
    COMMON_ITEMS = ["nymble", "shroodle", "tarountula", "lokix", "tadbulb"]
    RARE_ITEMS = [
        "grafaiai",
        "palafin",
        "azumarill",
        "gyarados",
    ]
    MEGA_ITEMS = ["mega mewtwo y"]

    if "coin" in item_name.lower() or "raffle ticket" in item_name.lower():
        return item_name  # No special formatting for currency items

    rarity = None
    lower_name = item_name.lower()
    if "shiny mega " in lower_name or "smega " in lower_name or "shiny mega-" in lower_name:
        rarity = "shiny mega"
        item_name = item_name.replace("Shiny Mega ", "").replace("SMega ", "").replace("Shiny Mega-", "").replace("SMega-", "")
    elif "shiny gigantamax" in lower_name or "shiny gigantamax-" in lower_name:
        rarity = "shiny gigantamax"
        item_name = item_name.replace("Shiny Gigantamax ", "").replace("Shiny Gigantamax-", "")

    elif "shiny " in lower_name:
        rarity = "shiny"
        item_name = item_name.replace("Shiny ", "")
    elif "golden mega " in lower_name or "gmega " in lower_name  or "golden mega-" in lower_name or "gmega-" in lower_name:
        rarity = "golden mega"
        item_name = item_name.replace("Golden Mega ", "").replace("GMega ", "").replace("Golden Mega-", "").replace("GMega-", "")

    elif "golden " in lower_name:
        rarity = "golden"
        item_name = item_name.replace("Golden ", "")
    elif lower_name in legendary_mons:
        rarity = "legendary"
    elif lower_name in superrare_mons:
        rarity = "superrare"
    elif lower_name in uncommon_mons:
        rarity = "uncommon"

    elif "gigantamax" in lower_name:
        rarity = "gigantamax"
        item_name = item_name.replace("Gigantamax ", "")

    elif lower_name in MEGA_ITEMS or "mega " in lower_name or "mega-" in lower_name:
        rarity = "mega"
        item_name = item_name.replace("Mega ", "").replace("Mega-", "")

    elif lower_name in rare_mons:
        rarity = "rare"
    elif lower_name in common_mons:
        rarity = "common"
    elif "uncommon " in lower_name:
        rarity = "uncommon"
        item_name = item_name.replace("Uncommon ", "")

    elif "common " in lower_name and not "1k common " in lower_name:
        rarity = "common"
        item_name = item_name.replace("Common ", "")
    elif "rare " in lower_name:
        rarity = "rare"
        item_name = item_name.replace("Rare ", "")

    rarity_emoji = rarity_meta.get(rarity, {}).get("emoji", "") if rarity else ""
    display_name = (
        f"{rarity_emoji} {item_name.title()}" if rarity_emoji else item_name.title()
    )
    if "1k common " in lower_name:
        rarity_emoji = rarity_meta.get("common", {}).get("emoji", "")
        item_name = item_name.replace("Common ", "")
        display_name = (
            f"1k {rarity_emoji} {item_name.title()}"
            if rarity_emoji
            else f"1k {item_name.title()}"
        )
    return display_name


async def shop_item_autocomplete(
    interaction: discord.Interaction, current: str
) -> List[discord.app_commands.Choice[str]]:
    """
    Autocomplete for server shop items from cache.
    Choice.name = "Item Name"
    Choice.value = "item_name"
    Matches both names and item IDs.
    """
    from utils.cache.server_shop_cache import fetch_all_shop_items_cache

    try:
        items = fetch_all_shop_items_cache()
    except Exception as e:
        pretty_log(
            "db",
            f"Error fetching shop items for autocomplete - {e}",
        )
        return []

    current = (current or "").lower().strip()
    results: List[discord.app_commands.Choice[str]] = []

    for item_id, item in items.items():
        item_name = str(item.get("item_name", "Unnamed Item"))
        if (
            not current
            or current in item_name.lower()
            or current in str(item_id).lower()
        ):
            results.append(discord.app_commands.Choice(name=item_name, value=item_name))
        if len(results) >= 25:
            break

    if not results:
        results.append(discord.app_commands.Choice(name="No matches found", value=""))

    return results
from typing import List


# Fetch all shop items
async def fetch_all_shop_items(bot: discord.Client) -> List[dict]:
    """Fetch all shop items from the server_shop table."""

    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT item_id, item_name, price, stock, description, image_link, dex
                FROM server_shop
                """
            )

            items = []

            for row in rows:
                items.append({
                    "item_id": row["item_id"],
                    "item_name": row["item_name"],
                    "price": row["price"],
                    "stock": row["stock"],
                    "description": row["description"],
                    "image_link": row["image_link"],
                    "dex": row["dex"],
                })

            pretty_log(
                "db",
                f"Fetched {len(items)} shop items",
                bot=bot,
            )

            return items

    except Exception as e:
        pretty_log(
            "error",
            f"Failed to fetch all shop items: {e}",
            bot=bot,
        )
        return []

async def upsert_item(
    bot: discord.Client,
    item_name: str,
    price: int,
    stock: int,
    description: str,
    image_link: str,
    dex: str = None,
):
    """
    Insert or update an item by name in the server_shop table.
    If the item already exists (by name), update its price and stock.
    If not, insert a new item with a generated item_id.
    Returns the item_id used.
    """

    try:
        async with bot.pg_pool.acquire() as conn:
            # Check if item exists
            result = await conn.fetchrow(
                """
                SELECT item_id
                FROM server_shop
                WHERE item_name = $1
                """,
                item_name,
            )

            if result:
                # Item exists, update it
                item_id = result["item_id"]

                await conn.execute(
                    """
                    UPDATE server_shop
                    SET price = $1,
                        stock = $2,
                        description = $3,
                        image_link = $4,
                        dex = $5
                    WHERE item_id = $6
                    """,
                    price,
                    stock,
                    description,
                    image_link,
                    dex,
                    item_id,
                )

                pretty_log(
                    "db",
                    f"Updated shop item '{item_name}' (ID: {item_id}) in database.",
                    bot=bot,
                )

                from utils.cache.server_shop_cache import \
                    update_shop_item_in_cache

                update_shop_item_in_cache(
                    item_id,
                    item_name,
                    price,
                    stock,
                    description,
                    image_link,
                    dex,
                )

            else:
                # Item does not exist, insert new
                item_id = generate_item_id(length=12)

                await conn.execute(
                    """
                    INSERT INTO server_shop (
                        item_id,
                        item_name,
                        price,
                        stock,
                        description,
                        image_link,
                        dex
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                    item_id,
                    item_name,
                    price,
                    stock,
                    description,
                    image_link,
                    dex,
                )

                pretty_log(
                    "db",
                    f"Inserted new shop item '{item_name}' (ID: {item_id}) into database.",
                    bot=bot,
                )

            from utils.cache.server_shop_cache import upsert_shop_item

            upsert_shop_item(
                item_id,
                item_name,
                price,
                stock,
                description,
                image_link,
                dex,
            )

            return item_id

    except Exception as e:
        pretty_log(
            "error",
            f"Failed to upsert shop item '{item_name}': {e}",
            bot=bot,
        )
        return None

async def update_dex(
    bot: discord.Client,
    item_id: str,
    dex: str,
):
    """Update the dex number of an item in the server_shop table by item_id."""

    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE server_shop
                SET dex = $1
                WHERE item_id = $2
                """,
                dex,
                item_id,
            )

            pretty_log(
                "db",
                f"Updated dex for shop item with ID: {item_id} to {dex} in database.",
                bot=bot,
            )

            # Update cache as well
            from utils.cache.server_shop_cache import update_dex_in_shop_cache

            update_dex_in_shop_cache(item_id, dex)

            return True

    except Exception as e:
        pretty_log(
            "error",
            f"Failed to update dex for shop item {item_id}: {e}",
            bot=bot,
        )
        return False
async def update_price(
    bot: discord.Client,
    item_id: str,
    price: int,
):
    """Update the price of an item in the server_shop table by item_id."""

    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE server_shop
                SET price = $1
                WHERE item_id = $2
                """,
                price,
                item_id,
            )

            pretty_log(
                "db",
                f"Updated price for shop item with ID: {item_id} to {price} in database.",
                bot=bot,
            )

            # Update cache as well
            from utils.cache.server_shop_cache import update_shop_item_price

            update_shop_item_price(item_id, price)

            return True

    except Exception as e:
        pretty_log(
            "error",
            f"Failed to update price for shop item {item_id}: {e}",
            bot=bot,
        )
        return False

async def update_stock(
    bot: discord.Client,
    item_id: str,
    stock: int,
):
    """Update the stock of an item in the server_shop table by item_id."""

    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE server_shop
                SET stock = $1
                WHERE item_id = $2
                """,
                stock,
                item_id,
            )

            pretty_log(
                "db",
                f"Updated stock for shop item with ID: {item_id} to {stock} in database.",
                bot=bot,
            )

            # Update cache as well
            from utils.cache.server_shop_cache import update_shop_item_stock

            update_shop_item_stock(item_id, stock)

            return True

    except Exception as e:
        pretty_log(
            "error",
            f"Failed to update stock for shop item {item_id}: {e}",
            bot=bot,
        )
        return False

async def update_item(
    bot: discord.Client,
    item_id: str,
    item_name: str = None,
    price: int = None,
    stock: int = None,
    description: str = None,
    image_link: str = None,
):
    """
    Update multiple fields of an item in the server_shop table by item_id.
    """

    try:
        async with bot.pg_pool.acquire() as conn:
            fields = []
            values = []

            if item_name is not None:
                fields.append(f"item_name = ${len(values) + 1}")
                values.append(item_name)

            if price is not None:
                fields.append(f"price = ${len(values) + 1}")
                values.append(price)

            if stock is not None:
                fields.append(f"stock = ${len(values) + 1}")
                values.append(stock)

            if description is not None:
                fields.append(f"description = ${len(values) + 1}")
                values.append(description)

            if image_link is not None:
                fields.append(f"image_link = ${len(values) + 1}")
                values.append(image_link)

            if not fields:
                pretty_log(
                    "db",
                    f"No fields to update for shop item with ID: {item_id}.",
                    bot=bot,
                )
                return

            # item_id gets the next parameter number
            values.append(item_id)
            item_id_param = len(values)

            query = f"""
                UPDATE server_shop
                SET {", ".join(fields)}
                WHERE item_id = ${item_id_param}
            """

            await conn.execute(query, *values)

            pretty_log(
                "db",
                f"Updated shop item with ID: {item_id} in database.",
                bot=bot,
            )

            # Update cache as well
            from utils.cache.server_shop_cache import update_shop_item_in_cache

            update_shop_item_in_cache(
                item_id,
                item_name,
                price,
                stock,
                description,
                image_link,
            )

    except Exception as e:
        pretty_log(
            "error",
            f"Error updating shop item with ID: {item_id} - {e}",
            bot=bot,
        )

async def remove_item(
    bot: discord.Client,
    item_id: str,
):
    """Remove an item from the server_shop table by item_id."""

    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                DELETE FROM server_shop
                WHERE item_id = $1
                """,
                item_id,
            )

            pretty_log(
                "db",
                f"Removed shop item with ID: {item_id} from database.",
                bot=bot,
            )

            # Remove from cache as well
            from utils.cache.server_shop_cache import remove_shop_item

            remove_shop_item(item_id)

            return True

    except Exception as e:
        pretty_log(
            "error",
            f"Failed to remove shop item with ID {item_id}: {e}",
            bot=bot,
        )
        return False

async def remove_all_items(bot: discord.Client):
    """Remove all items from the server_shop table."""

    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                DELETE FROM server_shop
                """
            )

            pretty_log(
                "db",
                "Removed all shop items from database.",
                bot=bot,
            )

            # Clear cache as well
            from utils.cache.cache_list import server_shop_cache

            server_shop_cache.clear()

            pretty_log(
                "cache",
                "Cleared server shop cache.",
                bot=bot,
            )

            return True

    except Exception as e:
        pretty_log(
            "error",
            f"Failed to remove all shop items: {e}",
            bot=bot,
        )
        return False

async def fetch_raffle_tickets(bot: discord.Client) -> dict | None:
    """Fetch the raffle tickets row from the server_shop table."""

    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT item_id, item_name, price, stock, description, image_link, dex
                FROM server_shop
                WHERE item_name = $1
                """,
                "Raffle Ticket",
            )

            if row:
                return {
                    "item_id": row["item_id"],
                    "item_name": row["item_name"],
                    "price": row["price"],
                    "stock": row["stock"],
                    "description": row["description"],
                    "image_link": row["image_link"],
                    "dex": row["dex"],
                }

            return None

    except Exception as e:
        pretty_log(
            "error",
            f"Failed to fetch raffle tickets: {e}",
            bot=bot,
        )
        return None

async def reset_raffle_ticket_stock(bot: discord.Client):
    """Reset the stock of raffle tickets to 5, upserting if not present."""

    item_name = "Raffle Ticket"
    price = 5
    stock = 5
    description = (
        "Grants one entry into an end-of-month raffle for a rare, high-value "
        "Golden Pokémon. Stock is strictly limited to 5 per week."
    )
    image_link = (
        "https://media.discordapp.net/attachments/"
        "1431448536049782915/1457990387665735755/"
        "image-removebg-preview_2.png"
        "?ex=695e02dc&is=695cb15c&hm="
        "d70cc095d03317092bed3ffeca77b292bd9277459554d4235c141c8345c5304a"
        "&=&format=webp&quality=lossless&width=574&height=383"
    )

    # Use upsert_item to ensure the row exists and is updated
    await upsert_item(
        bot,
        item_name=item_name,
        price=price,
        stock=stock,
        description=description,
        image_link=image_link,
    )
import discord

from utils.cache.cache_list import server_shop_cache
from utils.db.server_shop_db import fetch_all_shop_items
from utils.logs.pretty_log import pretty_log



# Load server shop cache
async def load_server_shop_cache(bot: discord.Client):
    pretty_log("info", "Loading server shop cache...")
    data = await fetch_all_shop_items(bot)
    server_shop_cache.clear()
    for row in data:
        item_id = row["item_id"]
        server_shop_cache[item_id] = {
            "item_name": row["item_name"],
            "price": row["price"],
            "stock": row["stock"],
            "description": row["description"],
            "image_link": row["image_link"],
            "dex": row["dex"],
        }
    pretty_log(
        "cache",
        f"Loaded server shop cache with {len(server_shop_cache)} items.",
    )
    return server_shop_cache


def update_dex_in_shop_cache(item_id: str, dex: str):
    """Update dex number in server shop cache."""
    if item_id in server_shop_cache:
        item_name = server_shop_cache[item_id]["item_name"]
        server_shop_cache[item_id]["dex"] = dex
        pretty_log(
            "cache",
            f"Updated dex cache for {item_name} (ID: {item_id}) to {dex}.",
        )


def fetch_all_shop_items_cache():
    """Fetch all shop items from cache."""
    return server_shop_cache


def upsert_shop_item(
    item_id: str,
    item_name: str,
    price: int,
    stock: int,
    description: str,
    image_link: str,
    dex: str = None,
):
    """Insert or update server shop cache entry."""
    server_shop_cache[item_id] = {
        "item_name": item_name,
        "price": price,
        "stock": stock,
        "description": description,
        "image_link": image_link,
        "dex": dex,
    }
    pretty_log(
        "cache",
        f"Upserted shop item cache for {item_name} (ID: {item_id}) with price {price} and stock {stock}.",
    )


def update_shop_item_stock(item_id: str, stock: int):
    """Update stock in server shop cache."""
    if item_id in server_shop_cache:
        item_name = server_shop_cache[item_id]["item_name"]
        server_shop_cache[item_id]["stock"] = stock
        pretty_log(
            "cache",
            f"Updated stock cache for {item_name} (ID: {item_id}) to {stock}.",
        )


def update_shop_item_price(item_id: str, price: int):
    """Update price in server shop cache."""
    if item_id in server_shop_cache:
        item_name = server_shop_cache[item_id]["item_name"]
        server_shop_cache[item_id]["price"] = price
        pretty_log(
            "cache",
            f"Updated price cache for {item_name} (ID: {item_id}) to {price}.",
        )


def remove_shop_item(item_id: str):
    """Remove server shop cache entry."""
    if item_id in server_shop_cache:
        item_name = server_shop_cache[item_id]["item_name"]
        del server_shop_cache[item_id]
        pretty_log(
            "cache",
            f"Removed shop item cache for {item_name} (ID: {item_id}).",
        )


def update_shop_item_in_cache(
    item_id: str,
    item_name: str = None,
    price: int = None,
    stock: int = None,
    description: str = None,
    image_link: str = None,
):
    """Update multiple fields of a server shop item in cache."""
    if item_id in server_shop_cache:
        if item_name is not None:
            server_shop_cache[item_id]["item_name"] = item_name
        if price is not None:
            server_shop_cache[item_id]["price"] = price
        if stock is not None:
            server_shop_cache[item_id]["stock"] = stock
        if description is not None:
            server_shop_cache[item_id]["description"] = description

        if image_link is not None:
            server_shop_cache[item_id]["image_link"] = image_link
        pretty_log(
            "cache",
            f"Updated shop item cache for {item_id} with provided fields.",
        )


def fetch_item_id_by_name(item_name: str) -> str | None:
    """Fetch item_id from server shop cache by item_name."""
    for item_id, item_data in server_shop_cache.items():
        if item_data["item_name"] == item_name:
            return item_id
    return None


def fetch_shop_item(item_id: str) -> dict | None:
    """Fetch shop item data from cache by item_id."""
    return server_shop_cache.get(item_id, None)

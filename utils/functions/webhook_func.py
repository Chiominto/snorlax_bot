import discord

from utils.cache.cache_list import webhook_url_cache
from utils.cache.webhook_url_cache import (
    fetch_webhook_url_from_cache,
    upsert_webhook_url_into_cache,
)
from utils.db.webhook_db_url import (
    fetch_webhook_url,
    remove_webhook_url,
    upsert_webhook_url,
)
from utils.logs.pretty_log import pretty_log


async def create_webhook_func(
    bot, channel: discord.TextChannel, name: str
) -> str | None:
    webhook = None
    try:
        avatar_bytes = await bot.user.avatar.read() if bot.user.avatar else None
        webhook = await channel.create_webhook(name=name, avatar=avatar_bytes)
        pretty_log(
            "info",
            f"Webhook '{name}' created in channel '{channel.name}' (ID: {channel.id})",
        )
        # Store the webhook URL in the database
        await upsert_webhook_url(bot, channel, webhook.url)

    except Exception as e:
        pretty_log(
            "error",
            f"Failed to create webhook in channel '{channel.name}': {e}",
        )
    return webhook.url if webhook else None


def _get_webhook_name(channel_name: str) -> str:
    lowered_channel_name = channel_name.lower()
    if "log" in lowered_channel_name:
        return "Snorlax Logs 💤"
    if "snipe" in lowered_channel_name:
        return "Snorlax Snipes 💤"
    return "Snorlax 💤"


def _normalize_cached_webhook_row(
    channel: discord.TextChannel,
    webhook_url_row: dict[str, str] | str | None,
) -> dict[str, str] | None:
    if webhook_url_row is None:
        return None
    if isinstance(webhook_url_row, str):
        return {
            "channel_name": channel.name,
            "url": webhook_url_row,
        }
    return webhook_url_row


async def get_webhook_url(
    bot: discord.Client,
    channel: discord.TextChannel,
) -> str | None:
    bot_id = bot.user.id
    channel_id = channel.id
    key = (bot_id, channel_id)

    cached_row = _normalize_cached_webhook_row(
        channel,
        fetch_webhook_url_from_cache(bot_id, channel_id),
    )
    if cached_row:
        webhook_url_cache[key] = cached_row
        return cached_row["url"]

    db_row = await fetch_webhook_url(bot, channel)
    if db_row:
        normalized_row = {
            "channel_name": db_row["channel_name"],
            "url": db_row["url"],
        }
        webhook_url_cache[key] = normalized_row
        return normalized_row["url"]

    webhook_url = await create_webhook_func(
        bot, channel, _get_webhook_name(channel.name)
    )
    if not webhook_url:
        return None

    upsert_webhook_url_into_cache(
        bot_id=bot_id,
        channel_id=channel_id,
        channel_name=channel.name,
        url=webhook_url,
    )
    return webhook_url


async def _send_with_webhook_url(
    bot: discord.Client,
    webhook_url: str,
    content: str = None,
    embed: discord.Embed = None,
):
    webhook = discord.Webhook.from_url(webhook_url, client=bot)
    await webhook.send(content=content, embed=embed, wait=True)


async def send_webhook(
    bot: discord.Client,
    channel: discord.TextChannel,
    content: str = None,
    embed: discord.Embed = None,
):
    webhook_url = await get_webhook_url(bot, channel)
    if not webhook_url:
        pretty_log(
            tag="info",
            message=f"⚠️ Falling back to direct channel send for channel '{channel.name}' (ID: {channel.id}) due to webhook lookup/creation failure",
            label="🌐 WEBHOOK SEND",
        )
        await channel.send(content=content, embed=embed)
        return

    try:
        await _send_with_webhook_url(bot, webhook_url, content=content, embed=embed)
        return
    except (ValueError, discord.NotFound, discord.Forbidden) as e:
        pretty_log(
            tag="error",
            message=f"⚠️ Stale webhook URL detected for channel '{channel.name}' (ID: {channel.id}): {e}",
            label="🌐 WEBHOOK SEND",
        )
        await remove_webhook_url(bot, channel)
    except discord.HTTPException:
        raise

    refreshed_webhook_url = await get_webhook_url(bot, channel)
    if not refreshed_webhook_url:
        pretty_log(
            tag="info",
            message=f"⚠️ Falling back to direct channel send for channel '{channel.name}' (ID: {channel.id}) after webhook reset failure",
            label="🌐 WEBHOOK SEND",
        )
        await channel.send(content=content, embed=embed)
        return

    try:
        await _send_with_webhook_url(
            bot,
            refreshed_webhook_url,
            content=content,
            embed=embed,
        )
    except (ValueError, discord.NotFound, discord.Forbidden) as e:
        pretty_log(
            tag="error",
            message=f"⚠️ Refreshed webhook send failed for channel '{channel.name}' (ID: {channel.id}): {e}",
            label="🌐 WEBHOOK SEND",
        )
        await channel.send(content=content, embed=embed)

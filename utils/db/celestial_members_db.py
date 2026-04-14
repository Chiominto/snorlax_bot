import time

import discord

from utils.logs.pretty_log import pretty_log

# SQL SCRIPT
"""CREATE TABLE celestial_members (
    user_id BIGINT PRIMARY KEY,
    user_name TEXT,
    pokemeow_name TEXT,
    channel_id BIGINT,
    actual_perks TEXT,
    clan_bank_donation BIGINT DEFAULT 0,
    clan_treasury_donation BIGINT DEFAULT 0,
    date_joined BIGINT
);
"""
async def fetch_all_celestial_members(bot: discord.Client):
    """Fetch all celestial members from the database."""
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT user_id, user_name, pokemeow_name, channel_id, actual_perks, clan_bank_donation, clan_treasury_donation, date_joined
                FROM celestial_members
                """
            )
            members = [
                {
                    "user_id": row["user_id"],
                    "user_name": row["user_name"],
                    "pokemeow_name": row["pokemeow_name"],
                    "channel_id": row["channel_id"],
                    "actual_perks": row["actual_perks"],
                    "clan_bank_donation": row["clan_bank_donation"],
                    "clan_treasury_donation": row["clan_treasury_donation"],
                    "date_joined": row["date_joined"],
                }
                for row in rows
            ]
            pretty_log(
                message=f"✅ Fetched {len(members)} celestial members from the database.",
                tag="db",
            )
            return members, None
    except Exception as e:
        pretty_log(
            message=f"❌ Failed to fetch celestial members: {e}",
            tag="error",
            include_trace=True,
        )
        return [], str(e)

async def fetch_celestial_member(bot: discord.Client, user_id: int):
    """Fetch a single celestial member by user ID."""
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT user_id, user_name, pokemeow_name, channel_id, actual_perks, clan_bank_donation, clan_treasury_donation, date_joined
                FROM celestial_members
                WHERE user_id = $1
                """,
                user_id,
            )
            if row:
                member = {
                    "user_id": row["user_id"],
                    "user_name": row["user_name"],
                    "pokemeow_name": row["pokemeow_name"],
                    "channel_id": row["channel_id"],
                    "actual_perks": row["actual_perks"],
                    "clan_bank_donation": row["clan_bank_donation"],
                    "clan_treasury_donation": row["clan_treasury_donation"],
                    "date_joined": row["date_joined"],
                }
                pretty_log(
                    message=f"✅ Fetched celestial member: {member['user_name']} (ID: {member['user_id']})",
                    tag="db",
                )
                return member
            else:
                pretty_log(
                    message=f"⚠️ Celestial member with ID {user_id} not found.",
                    tag="db",
                )
                return None
    except Exception as e:
        pretty_log(
            message=f"❌ Failed to fetch celestial member with ID {user_id}: {e}",
            tag="error",
            include_trace=True,
        )
        return None

async def upsert_celestial_member(
    bot: discord.Client,
    user_id: int,
    user_name: str,
    pokemeow_name: str,
    channel_id: int,

):
    """Insert or update a celestial member in the database."""
    date_joined = int(time.time())
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO celestial_members (user_id, user_name, pokemeow_name, channel_id, date_joined)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (user_id) DO UPDATE
                SET user_name = EXCLUDED.user_name,
                    pokemeow_name = EXCLUDED.pokemeow_name,
                    channel_id = EXCLUDED.channel_id
                """,
                user_id,
                user_name,
                pokemeow_name,
                channel_id,
                date_joined,
            )

            from utils.cache.celestial_members_cache import \
                upsert_celestial_member_cache
            upsert_celestial_member_cache(
                user_id,
                user_name,
                pokemeow_name,
                channel_id,
                actual_perks="",
                clan_bank_donation=0,
                clan_treasury_donation=0,
                date_joined=date_joined,
            )
            pretty_log(
                message=f"✅ Upserted celestial member: {user_name} (ID: {user_id})",
                tag="db",
            )

            return None
    except Exception as e:
        pretty_log(
            message=f"❌ Failed to upsert celestial member: {user_name} (ID: {user_id}): {e}",
            tag="error",
            include_trace=True,
        )
        error_message = f"Failed to upsert celestial member: {user_name} (ID: {user_id}): {e}"
        return error_message

async def update_actual_perks(
    bot: discord.Client,
    user_id: int,
    actual_perks: str,
):
    """Update the actual perks of a celestial member."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE celestial_members
                SET actual_perks = $1
                WHERE user_id = $2
                """,
                actual_perks,
                user_id,
            )
            pretty_log(
                message=f"✅ Updated actual perks for celestial member ID: {user_id}, Perks: {actual_perks}",
                tag="db",
            )
            # Update the cache as well
            from utils.cache.celestial_members_cache import \
                update_actual_perks_cache

            update_actual_perks_cache(user_id, actual_perks)

            return None
    except Exception as e:
        pretty_log(
            message=f"❌ Failed to update actual perks for celestial member ID: {user_id}: {e}",
            tag="error",
            include_trace=True,
        )
        error_message = f"Failed to update actual perks for celestial member ID: {user_id}: {e}"
        return error_message


async def update_pokemeow_name(
    bot: discord.Client,
    user_id: int,
    pokemeow_name: str,
):
    """Update the PokéMeow name of a celestial member."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE celestial_members
                SET pokemeow_name = $1
                WHERE user_id = $2
                """,
                pokemeow_name,
                user_id,
            )
            pretty_log(
                message=f"✅ Updated PokéMeow name for celestial member ID: {user_id}, New Name: {pokemeow_name}",
                tag="db",
            )

            # Update the cache as well
            from utils.cache.celestial_members_cache import \
                update_pokemeow_name_cache
            update_pokemeow_name_cache(user_id, pokemeow_name)

            return None
    except Exception as e:
        pretty_log(
            message=f"❌ Failed to update PokéMeow name for celestial member ID: {user_id}: {e}",
            tag="error",
            include_trace=True,
        )
        error_message = f"Failed to update PokéMeow name for celestial member ID: {user_id}: {e}"
        return error_message


async def update_channel_id(
    bot: discord.Client,
    user_id: int,
    channel_id: int,
):
    """Update the channel ID of a celestial member."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE celestial_members
                SET channel_id = $1
                WHERE user_id = $2
                """,
                channel_id,
                user_id,
            )
            pretty_log(
                message=f"✅ Updated channel ID for celestial member ID: {user_id}, New Channel ID: {channel_id}",
                tag="db",
            )
            # Update the cache as well
            from utils.cache.celestial_members_cache import \
                update_channel_id_cache
            update_channel_id_cache(user_id, channel_id)
            return None
    except Exception as e:
        pretty_log(
            message=f"❌ Failed to update channel ID for celestial member ID: {user_id}: {e}",
            tag="error",
            include_trace=True,
        )
        error_message = f"Failed to update channel ID for celestial member ID: {user_id}: {e}"
        return error_message

async def update_clan_bank_donation(
    bot: discord.Client,
    user_id: int,
    donation_amount: int,
):
    """Update the clan bank donation amount for a celestial member."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE celestial_members
                SET clan_bank_donation = clan_bank_donation + $1
                WHERE user_id = $2
                """,
                donation_amount,
                user_id,
            )
            pretty_log(
                message=f"✅ Updated clan bank donation for celestial member ID: {user_id}, Donation Amount: {donation_amount}",
                tag="db",
            )
            # Update the cache as well
            from utils.cache.celestial_members_cache import \
                update_clan_bank_donation_cache
            update_clan_bank_donation_cache(user_id, donation_amount)
            return None
    except Exception as e:
        pretty_log(
            message=f"❌ Failed to update clan bank donation for celestial member ID: {user_id}: {e}",
            tag="error",
            include_trace=True,
        )
        error_message = f"Failed to update clan bank donation for celestial member ID: {user_id}: {e}"
        return error_message

async def update_clan_treasury_donation(
    bot: discord.Client,
    user_id: int,
    donation_amount: int,
):
    """Update the clan treasury donation amount for a celestial member."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE celestial_members
                SET clan_treasury_donation = clan_treasury_donation + $1
                WHERE user_id = $2
                """,
                donation_amount,
                user_id,
            )
            pretty_log(
                message=f"✅ Updated clan treasury donation for celestial member ID: {user_id}, Donation Amount: {donation_amount}",
                tag="db",
            )
            # Update the cache as well
            from utils.cache.celestial_members_cache import \
                update_clan_treasury_donation_cache
            update_clan_treasury_donation_cache(user_id, donation_amount)
            return None
    except Exception as e:
        pretty_log(
            message=f"❌ Failed to update clan treasury donation for celestial member ID: {user_id}: {e}",
            tag="error",
            include_trace=True,
        )
        error_message = f"Failed to update clan treasury donation for celestial member ID: {user_id}: {e}"
        return error_message

async def remove_celestial_member(
    bot: discord.Client,
    user_id: int,
):
    """Remove a celestial member from the database."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                DELETE FROM celestial_members
                WHERE user_id = $1
                """,
                user_id,
            )
            pretty_log(
                message=f"✅ Removed celestial member ID: {user_id} from the database.",
                tag="db",
            )
            # Remove from cache as well
            from utils.cache.celestial_members_cache import \
                remove_celestial_member_cache
            remove_celestial_member_cache(user_id)

            return None
    except Exception as e:
        pretty_log(
            message=f"❌ Failed to remove celestial member ID: {user_id} from the database: {e}",
            tag="error",
            include_trace=True,
        )
        error_message = f"Failed to remove celestial member ID: {user_id} from the database: {e}"
        return error_message


    except Exception as e:
        pretty_log(
            message=f"❌ Failed to remove celestial member ID: {user_id} from the database: {e}",
            tag="error",
            include_trace=True,
        )
        error_message = f"Failed to remove celestial member ID: {user_id} from the database: {e}"
        return error_message

async def fetch_member_channel_id(bot: discord.Client, user_id: int):
    """Fetch the channel ID associated with a celestial member."""
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT channel_id
                FROM celestial_members
                WHERE user_id = $1
                """,
                user_id,
            )
            if row:
                channel_id = row["channel_id"]
                pretty_log(
                    message=f"✅ Fetched channel ID for celestial member ID: {user_id}, Channel ID: {channel_id}",
                    tag="db",
                )
                return channel_id
            else:
                pretty_log(
                    message=f"⚠️ Celestial member with ID {user_id} not found when fetching channel ID.",
                    tag="db",
                )
                return None
    except Exception as e:
        pretty_log(
            message=f"❌ Failed to fetch channel ID for celestial member ID: {user_id}: {e}",
            tag="error",
            include_trace=True,
        )
        return None
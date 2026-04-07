import asyncio
import os

import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv

from utils.cache.central_cache_loader import load_all_cache
from utils.cache.cache_list import clear_processed_ids_cache
from utils.db.get_pg_pool import get_pg_pool
from utils.logs.pretty_log import pretty_log, set_bot

# ---- Intents / Bot ----
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
set_bot(bot)


# 🟣────────────────────────────────────────────
#         ⚡ Hourly Cache Refresh Task ⚡
# 🟣────────────────────────────────────────────
@tasks.loop(hours=1)

async def refresh_all_caches():
    if not hasattr(refresh_all_caches, "_has_run"):
        refresh_all_caches._has_run = True
        return  # Skip the first run
    await load_all_cache(bot)
    clear_processed_ids_cache()


# 🟣────────────────────────────────────────────
#         ⚡ Load Cogs ⚡
# 🟣────────────────────────────────────────────
async def load_extensions():
    """
    Dynamically load all Python files in the 'cogs' folder (ignores __pycache__).
    Logs loaded cogs with pretty_log and errors if loading fails.
    """
    loaded_cogs = []
    for root, dirs, files in os.walk("cogs"):
        # Skip __pycache__ folders
        dirs[:] = [d for d in dirs if d != "__pycache__"]

        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                # Skip pokemons.py specifically in the cogs folder
                if root == "cogs" and file == "pokemons.py":
                    continue
                module_path = (
                    os.path.join(root, file).replace(os.sep, ".").replace(".py", "")
                )
                try:
                    await bot.load_extension(module_path)
                    loaded_cogs.append(module_path)
                except Exception as e:
                    pretty_log(
                        message=f"❌ Failed to load cog: {module_path}\n{e}",
                        tag="error",
                    )
    _loaded_count = len(loaded_cogs)
    pretty_log("ready", f"✅ Loaded { _loaded_count} cogs")


# 🟣────────────────────────────────────────────
#         ⚡ On Ready ⚡
# 🟣────────────────────────────────────────────
@bot.event
async def on_ready():
    # Guard for type checker: bot.user may be Optional
    user = bot.user
    if user is None:
        pretty_log("info", "Bot is online (user not yet cached).")
    else:
        pretty_log("info", f"Bot online as {user} (ID: {user.id})")

    # Sync commands
    try:
        await bot.tree.sync()
        slash_count = len(bot.tree.get_commands())
        pretty_log("info", f"{slash_count} slash commands synced globally.")
    except Exception as e:
        pretty_log("error", f"Slash sync commands failed: {e}")

    # Start the hourly cache refresh task
    if not refresh_all_caches.is_running():
        refresh_all_caches.start()
        pretty_log(message="✅ Started hourly cache refresh task", tag="ready")

    # Load caches immediately before checklist
    from utils.cache.central_cache_loader import load_all_cache

    await load_all_cache(bot)


# 🟣────────────────────────────────────────────
#         ⚡ Main ⚡
# 🟣────────────────────────────────────────────
async def main():
    # Load extensions
    await load_extensions()

    # Intialize the database pool
    try:
        bot.pg_pool = await get_pg_pool()
        pretty_log(message="✅ PostgreSQL connection pool established", tag="ready")
    except Exception as e:
        pretty_log(
            tag="critical",
            message=f"Failed to initialize database pool: {e}",
            include_trace=True,
        )
        return  # Exit if DB connection fails

    load_dotenv()
    pretty_log("ready", "snorlax Bot is starting...")

    retry_delay = 5
    while True:
        try:
            await bot.start(os.getenv("DISCORD_TOKEN"))
        except KeyboardInterrupt:
            pretty_log("ready", "Shutting down snorlax Bot...")
            break
        except Exception as e:
            pretty_log("error", f"Bot crashed: {e}", include_trace=True)
            pretty_log(
                "ready", f"Restarting snorlax Bot in {retry_delay} seconds..."
            )
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 60)


# ❀───────────────────────────────❀
#       💖  Entry Point 💖
# ❀───────────────────────────────❀
if __name__ == "__main__":
    asyncio.run(main())

import traceback
from datetime import datetime

import discord
from discord.ext import commands

CC_ERROR_LOGS_CHANNEL_ID = 1444997181244444672
# -------------------- 🧩 Global Bot Reference --------------------
from typing import Optional

BOT_INSTANCE: Optional[commands.Bot] = None


def set_bot(bot: commands.Bot):
    """Set the global bot instance for automatic logging."""
    global BOT_INSTANCE
    BOT_INSTANCE = bot

# -------------------- 🧩 Log Tags --------------------
TAGS = {
    "info": "😴 INFO",  # Snorlax sleeping (default/info)
    "db": "🍩 DB",  # Donut (Snorlax loves food)
    "cmd": "🍚 CMD",  # Rice bowl (food command)
    "ready": "🛌 READY",  # Bed (Snorlax wakes/rests)
    "error": "💤 ERROR",  # Sleep bubble (Snorlax dozing off = error)
    "warn": "🍃 WARN",  # Leaf (Snorlax in nature, caution)
    "critical": "💥 CRITICAL",  # Explosion (Snorlax startled)
    "skip": "🛑 SKIP",  # Stop sign (Snorlax blocks the way)
    "sent": "📦 SENT",  # Box (Snorlax stores items)
    "debug": "🐾 DEBUG",  # Paw prints (Snorlax steps)
    "success": "🌟 SUCCESS",  # Star (Snorlax triumph)
    "cache": "🥛 CACHE",  # Milk bottle (Snorlax refresh)
    "schedule": "⏰ SCHEDULE",  # Alarm clock (Snorlax wakes up)
    "snipe": "🧺 SNIPE",
}

# -------------------- 🎨 Snorlax ANSI Colors --------------------
COLOR_SNORLAX_BLUE = "\033[38;2;25;45;65m"  # Deep navy (Snorlax body)
COLOR_SNORLAX_CREAM = "\033[38;2;235;225;200m"  # Belly cream
COLOR_SNORLAX_GREEN = "\033[38;2;90;120;90m"  # Muted green accent
COLOR_SNORLAX_BROWN = "\033[38;2;150;100;70m"  # Warm brown
COLOR_RESET = "\033[0m"

MAIN_COLORS = {
    "info": COLOR_SNORLAX_CREAM,  # Default logs
    "warn": COLOR_SNORLAX_GREEN,  # Warnings
    "error": COLOR_SNORLAX_BLUE,  # Errors
    "critical": COLOR_SNORLAX_BROWN,  # Critical
    "reset": COLOR_RESET,
}

# -------------------- ⚠️ Critical Logs Channel --------------------
CRITICAL_LOG_CHANNEL_ID = (
    1444997181244444672  # CC Error Logs
)
CRITICAL_LOG_CHANNEL_LIST = [
    1410202143570530375,  # Ghouldengo Bot Logs
    CC_ERROR_LOGS_CHANNEL_ID,
    1375702774771093697,
]


# -------------------- 🌟 Pretty Log --------------------
def pretty_log(
    tag: str = "info",
    message: str = "",
    *,
    label: str = None,
    bot: commands.Bot = None,
    include_trace: bool = True,
):
    """
    Prints a colored log for Shuckle-themed bots with timestamp and emoji.
    Sends critical/error/warn messages to Discord if bot is set.
    """
    prefix = TAGS.get(tag) if tag else ""
    prefix_part = f"[{prefix}] " if prefix else ""
    label_str = f"[{label}] " if label else ""

    # Choose color based on tag
    color = MAIN_COLORS["info"]  # info/default (was blue, now shuckle white)
    if tag in ("warn",):
        color = MAIN_COLORS["warn"]
    elif tag in ("error",):
        color = MAIN_COLORS["critical"]
    elif tag in ("critical",):
        color = MAIN_COLORS["critical"]

    now = datetime.now().strftime("%H:%M:%S")
    log_message = f"{color}[{now}] {prefix_part}{label_str}{message}{COLOR_RESET}"
    print(log_message)

    # Optionally print traceback
    if include_trace and tag in ("error", "critical"):
        traceback.print_exc()

    # Send to all Discord channels in the list if bot available
    bot_to_use = bot or BOT_INSTANCE
    if bot_to_use and tag in ("critical", "error", "warn"):
        for channel_id in CRITICAL_LOG_CHANNEL_LIST:
            try:
                channel = bot_to_use.get_channel(channel_id)
                if channel:
                    full_message = f"{prefix_part}{label_str}{message}"
                    if include_trace and tag in ("error", "critical"):
                        full_message += f"\n```py\n{traceback.format_exc()}```"
                    if len(full_message) > 2000:
                        full_message = full_message[:1997] + "..."
                    bot_to_use.loop.create_task(channel.send(full_message))
            except Exception:
                print(
                    f"{COLOR_SNORLAX_BROWN}[❌ ERROR] Failed to send log to Discord channel {channel_id}{COLOR_RESET}"
                )
                traceback.print_exc()


# -------------------- 🌸 UI Error Logger --------------------
def log_ui_error(
    *,
    error: Exception,
    interaction: discord.Interaction = None,
    label: str = "UI",
    bot: commands.Bot = None,
    include_trace: bool = True,
):
    """Logs UI errors with automatic Discord reporting."""
    location_info = ""
    if interaction:
        user = interaction.user
        location_info = f"User: {user} ({user.id}) | Channel: {interaction.channel} ({interaction.channel_id})"

    error_message = f"UI error occurred. {location_info}".strip()
    now = datetime.now().strftime("%H:%M:%S")

    print(
        f"{COLOR_SNORLAX_BROWN}[{now}] [💥 CRITICAL] {label} error: {error_message}{COLOR_RESET}"
    )
    if include_trace:
        traceback.print_exception(type(error), error, error.__traceback__)

    bot_to_use = bot or BOT_INSTANCE

    pretty_log(
        "error",
        error_message,
        label=label,
        bot=bot_to_use,
        include_trace=include_trace,
    )

    if bot_to_use:
        for channel_id in CRITICAL_LOG_CHANNEL_LIST:
            try:
                channel = bot_to_use.get_channel(channel_id)
                if channel:
                    embed = discord.Embed(
                        title=f"⚠️ UI Error Logged [{label}]",
                        description=f"{location_info or '*No interaction data*'}",
                        color=0x88DFFF,  # Ghouldengo cyan
                    )
                    if include_trace:
                        trace_text = "".join(
                            traceback.format_exception(
                                type(error), error, error.__traceback__
                            )
                        )
                        if len(trace_text) > 1000:
                            trace_text = trace_text[:1000] + "..."
                        embed.add_field(
                            name="Traceback",
                            value=f"```py\n{trace_text}```",
                            inline=False,
                        )
                    bot_to_use.loop.create_task(channel.send(embed=embed))
            except Exception:
                print(
                    f"{COLOR_SNORLAX_BROWN}[❌ ERROR] Failed to send UI error to bot channel {channel_id}{COLOR_RESET}"
                )
                traceback.print_exc()

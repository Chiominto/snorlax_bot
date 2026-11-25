import logging
import re
from contextvars import ContextVar
from urllib.parse import urlsplit

import discord

from utils.logs.pretty_log import pretty_log

_current_command = ContextVar("discord_rate_limit_command", default=None)
_RAY_ID_PATTERN = re.compile(r"Ray ID:\s*([a-f0-9]+)", re.IGNORECASE)


def _command_name_from_interaction(interaction: discord.Interaction) -> str | None:
    command = getattr(interaction, "command", None)
    if command:
        qualified_name = getattr(command, "qualified_name", None)
        if qualified_name:
            return qualified_name

    data = getattr(interaction, "data", None)
    if not isinstance(data, dict):
        return None

    names = [data["name"]] if data.get("name") else []
    options = data.get("options", [])
    while isinstance(options, list):
        subcommand = next(
            (
                option
                for option in options
                if isinstance(option, dict) and option.get("type") in (1, 2)
            ),
            None,
        )
        if not subcommand:
            break
        names.append(subcommand["name"])
        options = subcommand.get("options", [])

    return " ".join(names) or None


def set_interaction_command_context(interaction: discord.Interaction) -> None:
    command_name = _command_name_from_interaction(interaction)
    _current_command.set(f"/{command_name}" if command_name else "app interaction")


def log_interaction_rate_limit(
    interaction: discord.Interaction,
    error: Exception,
    *,
    stage: str,
) -> bool:
    if not isinstance(error, discord.HTTPException) or error.status != 429:
        return False

    command_name = _command_name_from_interaction(interaction)
    context = f"/{command_name}" if command_name else _current_command.get()
    context = context or "unknown/background request"
    response = getattr(error, "response", None)
    headers = getattr(response, "headers", {}) or {}
    retry_after = headers.get("Retry-After")
    response_text = getattr(error, "text", "") or ""
    ray_match = _RAY_ID_PATTERN.search(response_text)
    cloudflare_match = re.search(r"Error\s+1015", response_text, re.IGNORECASE)

    details = [
        f"HTTP 429 at {stage}",
        f"command={context}",
        f"status={error.status}",
        f"code={error.code}",
    ]
    if cloudflare_match:
        details.append("source=Cloudflare 1015")
    if retry_after:
        details.append(f"retry_after={retry_after}s")
    if ray_match:
        details.append(f"ray_id={ray_match.group(1)}")

    pretty_log("info", "; ".join(details), label="Discord Rate Limit")
    return True


def _safe_route(url: str) -> str:
    path = urlsplit(url).path
    path = re.sub(
        r"/(interactions|webhooks)/\d+/[^/]+",
        r"/\1/:id/:token",
        path,
    )
    return re.sub(r"/\d+(?=/|$)", "/:id", path)


class DiscordRateLimitLogHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = record.getMessage()
            if "responded with 429" not in message and "Global rate limit has been hit" not in message:
                return

            args = record.args if isinstance(record.args, tuple) else ()
            method = str(args[0]) if len(args) >= 2 else "HTTP"
            route = _safe_route(str(args[1])) if len(args) >= 2 else "global limit"
            retry_after = args[2] if len(args) >= 3 else None
            context = _current_command.get() or "unknown/background request"

            details = [f"{method} {route}", f"command={context}"]
            if retry_after is not None:
                details.append(f"retry_after={retry_after}s")
            summary = "; ".join(details)

            pretty_log("info", summary, label="Discord API Rate Limit")

            # discord.py's warning includes the raw URL, which may contain a
            # webhook or interaction token. Replace it before other handlers see it.
            record.msg = summary
            record.args = ()
            record.levelno = logging.DEBUG
            record.levelname = "DEBUG"
        except Exception:
            self.handleError(record)


def install_discord_rate_limit_logging() -> None:
    logger = logging.getLogger("discord.http")
    if not any(
        isinstance(handler, DiscordRateLimitLogHandler)
        for handler in logger.handlers
    ):
        handler = DiscordRateLimitLogHandler()
        handler.setLevel(logging.WARNING)
        logger.addHandler(handler)


class RateLimitCommandTree(discord.app_commands.CommandTree):
    async def interaction_check(self, interaction: discord.Interaction, /) -> bool:
        set_interaction_command_context(interaction)
        return await super().interaction_check(interaction)

import logging
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import discord

from utils.logs.discord_rate_limit import (
    DiscordRateLimitLogHandler,
    log_interaction_rate_limit,
    set_interaction_command_context,
)


class DiscordRateLimitTests(unittest.TestCase):
    def test_http_logger_includes_command_and_redacts_interaction_token(self):
        set_interaction_command_context(
            SimpleNamespace(
                command=None,
                data={
                    "name": "shop",
                    "options": [{"name": "view", "type": 1, "options": []}],
                },
            )
        )
        record = logging.LogRecord(
            name="discord.http",
            level=logging.WARNING,
            pathname="discord/http.py",
            lineno=1,
            msg="%s %s responded with 429. Retrying in %.2f seconds.",
            args=(
                "POST",
                "https://discord.com/api/v10/interactions/123456789012345678/secret-token/callback",
                2.5,
            ),
            exc_info=None,
        )

        with patch("utils.logs.discord_rate_limit.pretty_log") as log:
            DiscordRateLimitLogHandler().emit(record)

        logged_message = log.call_args.args[1]
        self.assertIn("command=/shop view", logged_message)
        self.assertIn("/interactions/:id/:token/callback", logged_message)
        self.assertNotIn("secret-token", logged_message)
        self.assertEqual(record.levelno, logging.DEBUG)

    def test_cloudflare_429_logs_ray_id_without_response_body(self):
        interaction = SimpleNamespace(
            command=SimpleNamespace(qualified_name="shop view"),
            data={},
        )
        response = SimpleNamespace(
            status=429,
            reason="Too Many Requests",
            headers={"Retry-After": "30"},
        )
        error = discord.HTTPException(
            response,
            "Cloudflare Error 1015. Ray ID: a5fe5aeefc6a9cd0",
        )

        with patch("utils.logs.discord_rate_limit.pretty_log") as log:
            logged = log_interaction_rate_limit(
                interaction,
                error,
                stage="shop view defer",
            )

        self.assertTrue(logged)
        logged_message = log.call_args.args[1]
        self.assertIn("source=Cloudflare 1015", logged_message)
        self.assertIn("ray_id=a5fe5aeefc6a9cd0", logged_message)
        self.assertIn("retry_after=30s", logged_message)
        self.assertNotIn("Cloudflare Error 1015", logged_message)


if __name__ == "__main__":
    unittest.main()

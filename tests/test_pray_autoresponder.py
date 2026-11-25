import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from constants.celestial_constants import KHY_USER_ID
from utils.autoresponder import pray


class PrayAutoresponderTests(unittest.IsolatedAsyncioTestCase):
    async def test_blessing_without_meal_bonus_still_completes(self):
        user = SimpleNamespace(
            id=KHY_USER_ID,
            name="tester",
            display_name="tester",
            roles=[],
            display_avatar=SimpleNamespace(url="https://example.com/avatar.png"),
        )
        guild = SimpleNamespace(get_role=Mock(return_value=object()))
        bot = SimpleNamespace(get_guild=Mock(return_value=guild))
        message = SimpleNamespace(author=user, reply=AsyncMock())

        with (
            patch.object(
                pray,
                "fetch_user_server_cooldown_for_type",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch.object(pray.random, "random", return_value=0.1),
            patch.object(
                pray, "fetch_fry_points", new_callable=AsyncMock, return_value=None
            ),
            patch.object(
                pray, "handle_extra_meal_reward", new_callable=AsyncMock, return_value=0
            ),
            patch.object(pray, "upsert_user_fry_points", new_callable=AsyncMock) as upsert,
            patch.object(pray, "send_meal_log", new_callable=AsyncMock) as meal_log,
            patch.object(pray, "pretty_log"),
        ):
            await pray.handle_pray_autoresponder(bot, message)

        upsert.assert_awaited_once()
        message.reply.assert_awaited_once()
        meal_log.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()

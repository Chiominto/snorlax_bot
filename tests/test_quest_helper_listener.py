import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import discord

from cogs.events import on_message_create
from utils.listener_func import quest_helper_listener


class QuestHelperRoutingTests(unittest.IsolatedAsyncioTestCase):
    async def test_cupcake_completion_calls_listener(self):
        message = SimpleNamespace(
            guild=Mock(),
            content="",
            embeds=[
                discord.Embed(
                    description=(
                        "🧁 You ate a **cupcake** from **gothkittens**.\n"
                        "🗒️ **\\_\\.demon\\.\\_3** completed the quest "
                        "**Receive 1 🧁 from another player** and received: **3x** candy!"
                    )
                )
            ],
            author=SimpleNamespace(
                id=on_message_create.POKEMEOW_APPLICATION_ID, bot=True
            ),
            webhook_id=None,
            channel=SimpleNamespace(id=on_message_create.CELESTIAL_TEXT_CHANNELS.quest_help),
            id=1571545045327155352,
        )
        bot = Mock()
        cog = on_message_create.MessageCreateListener(bot)

        with (
            patch.object(on_message_create, "pretty_log"),
            patch.object(quest_helper_listener, "is_burger_shop_ongoing", return_value=False),
            patch.object(quest_helper_listener, "pretty_log") as listener_log,
        ):
            await cog.on_message(message)

        self.assertIn("event is not ongoing", listener_log.call_args.args[1])


class QuestHelperRewardTests(unittest.IsolatedAsyncioTestCase):
    async def test_existing_balance_is_incremented_for_helper(self):
        role = object()
        helper = Mock(spec=discord.Member)
        helper.id = 123
        helper.name = "gothkittens"
        helper.roles = [role]
        helper.mention = "<@123>"
        replied_message = Mock(spec=discord.Message)
        replied_message.author = helper
        replied_message.reply = AsyncMock()
        author = MagicMock()
        author.id = quest_helper_listener.POKEMEOW_APPLICATION_ID
        author.__str__.return_value = "PokéMeow#6691"
        message = SimpleNamespace(
            author=author,
            guild=SimpleNamespace(get_role=Mock(return_value=role)),
            channel=SimpleNamespace(id=quest_helper_listener.CELESTIAL_TEXT_CHANNELS.quest_help),
            reference=SimpleNamespace(resolved=replied_message),
        )
        bot = Mock()

        with (
            patch.object(quest_helper_listener, "is_burger_shop_ongoing", return_value=True),
            patch.object(quest_helper_listener, "randint", return_value=1),
            patch.object(quest_helper_listener, "server_currency_cache", {123: {"currency": 42}}),
            patch.object(quest_helper_listener, "update_currency", new_callable=AsyncMock) as update,
            patch.object(quest_helper_listener, "pretty_log"),
            patch.object(quest_helper_listener, "send_meal_log", new_callable=AsyncMock),
        ):
            await quest_helper_listener.quest_helper_listener(bot, message)

        update.assert_awaited_once_with(bot=bot, user_id=123, currency=43)
        replied_message.reply.assert_awaited_once()
        self.assertIn("<@123>", replied_message.reply.await_args.kwargs["content"])


if __name__ == "__main__":
    unittest.main()

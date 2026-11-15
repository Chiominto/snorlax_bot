import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import discord

from utils.listener_func import rarespawn_listener


class RareSpawnMemberTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        log_patch = patch.object(rarespawn_listener, "pretty_log")
        log_patch.start()
        self.addCleanup(log_patch.stop)
        self.role = object()
        self.member = Mock(spec=discord.Member)
        self.member.id = 123
        self.member.name = "_.demon._3"
        self.member.roles = [self.role]
        self.user = Mock(spec=discord.User)
        self.user.id = self.member.id
        self.guild = SimpleNamespace(
            get_member=Mock(return_value=None),
            fetch_member=AsyncMock(return_value=self.member),
            get_role=Mock(return_value=self.role),
        )
        self.before = SimpleNamespace(
            author="PokéMeow#6691", reference=None, interaction_metadata=None
        )
        embed = discord.Embed(
            color=rarespawn_listener.LEGENDARY_COLOR,
            description="You caught a **Landorus** with a Masterball!",
        )
        embed.set_author(name="Congratulations, _.demon._3!")
        self.after = SimpleNamespace(
            guild=self.guild,
            embeds=[embed],
            id=42,
            author="PokéMeow#6691",
            reference=None,
            interaction_metadata=None,
        )

    async def run_listener(self):
        with (
            patch.object(rarespawn_listener, "is_burger_shop_ongoing", return_value=True),
            patch.object(rarespawn_listener, "processed_rare_catches", set()),
            patch.object(rarespawn_listener, "add_points_to_member", new_callable=AsyncMock) as add_points,
        ):
            await rarespawn_listener.handle_rarespawn_catch(
                bot=Mock(), before_message=self.before, after_message=self.after
            )
            return add_points

    async def test_interaction_member_is_used_directly(self):
        self.before.interaction_metadata = SimpleNamespace(user=self.member)

        add_points = await self.run_listener()

        self.assertIs(add_points.await_args.kwargs["member"], self.member)
        self.guild.get_member.assert_not_called()
        self.guild.fetch_member.assert_not_awaited()

    async def test_before_interaction_user_resolves_cached_member(self):
        self.before.interaction_metadata = SimpleNamespace(user=self.user)
        self.guild.get_member.return_value = self.member

        add_points = await self.run_listener()

        self.assertIs(add_points.await_args.kwargs["member"], self.member)
        self.guild.fetch_member.assert_not_awaited()

    async def test_after_interaction_user_fetches_uncached_member(self):
        self.after.interaction_metadata = SimpleNamespace(user=self.user)

        add_points = await self.run_listener()

        self.assertIs(add_points.await_args.kwargs["member"], self.member)
        self.guild.fetch_member.assert_awaited_once_with(self.user.id)

    async def test_embed_username_fallback_fetches_uncached_member(self):
        with patch(
            "utils.cache.celestial_members_cache.fetch_user_id_by_user_name_or_pokemon_name_cache",
            return_value=self.member.id,
        ) as lookup:
            add_points = await self.run_listener()

        lookup.assert_called_once_with("_.demon._3")
        self.guild.fetch_member.assert_awaited_once_with(self.member.id)
        self.assertIs(add_points.await_args.kwargs["member"], self.member)

    async def test_failed_member_fetch_is_logged_and_not_awarded(self):
        self.before.interaction_metadata = SimpleNamespace(user=self.user)
        response = SimpleNamespace(status=404, reason="Not Found")
        self.guild.fetch_member.side_effect = discord.NotFound(response, "Unknown Member")

        with patch.object(rarespawn_listener, "pretty_log") as log:
            add_points = await self.run_listener()

        add_points.assert_not_awaited()
        self.assertTrue(
            any("Failed to fetch member 123" in call.args[1] for call in log.call_args_list)
        )


if __name__ == "__main__":
    unittest.main()

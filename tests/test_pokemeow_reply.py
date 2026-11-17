import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import discord

from utils.functions.pokemeow_reply import get_pokemeow_reply_or_interaction_member


class PokemeowReplyInteractionMemberTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.member = Mock(spec=discord.Member)
        self.member.id = 123
        self.user = Mock(spec=discord.User)
        self.user.id = self.member.id
        self.guild = SimpleNamespace(
            get_member=Mock(return_value=None),
            fetch_member=AsyncMock(return_value=self.member),
        )
        self.message = SimpleNamespace(
            author="PokéMeow#6691",
            reference=None,
            interaction_metadata=SimpleNamespace(user=self.user, member=None),
            guild=self.guild,
        )

    async def test_fetches_guild_member_for_interaction_user(self):
        member = await get_pokemeow_reply_or_interaction_member(self.message)

        self.assertIs(member, self.member)
        self.guild.get_member.assert_called_once_with(self.user.id)
        self.guild.fetch_member.assert_awaited_once_with(self.user.id)

    async def test_uses_cached_guild_member_for_interaction_user(self):
        self.guild.get_member.return_value = self.member

        member = await get_pokemeow_reply_or_interaction_member(self.message)

        self.assertIs(member, self.member)
        self.guild.get_member.assert_called_once_with(self.user.id)
        self.guild.fetch_member.assert_not_awaited()

    async def test_returns_none_for_interaction_without_guild(self):
        self.message.guild = None

        member = await get_pokemeow_reply_or_interaction_member(self.message)

        self.assertIsNone(member)


if __name__ == "__main__":
    unittest.main()

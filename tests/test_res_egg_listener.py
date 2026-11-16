import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import discord

from utils.listener_func import res_egg_listener
from utils.listener_func.res_egg_listener import get_res_egg_hatch_member


class ResEggMemberLookupTests(unittest.TestCase):
    def test_extracts_username_and_returns_guild_member(self):
        member = Mock()
        guild = Mock()
        guild.get_member_named.return_value = member
        message = SimpleNamespace(
            guild=guild,
            embeds=[
                SimpleNamespace(
                    author=SimpleNamespace(
                        name="👤 _.demon._3's Research Lab Hatch"
                    )
                )
            ],
        )

        result = get_res_egg_hatch_member(message)

        self.assertIs(result, member)
        guild.get_member_named.assert_called_once_with("_.demon._3")

    def test_returns_none_for_unrecognized_author(self):
        guild = Mock()
        message = SimpleNamespace(
            guild=guild,
            embeds=[SimpleNamespace(author=SimpleNamespace(name="No hatch here"))],
        )

        with patch.object(res_egg_listener, "pretty_log"):
            result = get_res_egg_hatch_member(message)

        self.assertIsNone(result)
        guild.get_member_named.assert_not_called()


class ResEggRewardTests(unittest.IsolatedAsyncioTestCase):
    async def test_research_lab_shiny_nymble_hatch_awards_two_points(self):
        role = Mock()
        member = Mock(spec=discord.Member)
        member.roles = [role]
        guild = Mock()
        guild.get_member_named.return_value = member
        guild.get_role.return_value = role
        embed = discord.Embed(
            description=(
                "**Red Egg** hatched in **Lab Incubator 2**!\n\n"
                "**Shiny Nymble**\n\n"
                "**Additional rewards**\n"
                "- **3x Egg**"
            )
        )
        embed.set_author(name="👤 _qntn_'s Research Lab Hatch")
        message = SimpleNamespace(
            id=1571222700716724226,
            guild=guild,
            embeds=[embed],
        )

        with (
            patch.object(res_egg_listener, "add_points_to_member", new_callable=AsyncMock) as add_points,
            patch.object(res_egg_listener, "pretty_log"),
        ):
            await res_egg_listener.handle_res_egg_hatch(Mock(), message)

        guild.get_member_named.assert_called_once_with("_qntn_")
        add_points.assert_awaited_once()
        self.assertEqual(add_points.await_args.kwargs["member"], member)
        self.assertEqual(add_points.await_args.kwargs["points"], 2)


if __name__ == "__main__":
    unittest.main()

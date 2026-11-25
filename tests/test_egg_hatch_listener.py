import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import discord

from utils.listener_func import egg_hatch_listener


class EggHatchRewardTests(unittest.IsolatedAsyncioTestCase):
    async def test_rewards_each_event_exclusive_in_multi_egg_hatch(self):
        role = object()
        member = Mock()
        member.roles = [role]
        guild = Mock()
        guild.get_role.return_value = role
        message = SimpleNamespace(
            id=123,
            content=(
                "han0maly_ just hatched ...\n"
                "- **Shiny Tadbulb**\n"
                "- **Scyther**\n"
                "- **Shiny Nymble**\n"
                "- You received an additional **13x** Pokeballs!"
            ),
            embeds=[discord.Embed()],
            guild=guild,
            channel=SimpleNamespace(name="egg-hatches"),
        )

        with (
            patch.object(egg_hatch_listener, "processed_egg_hatches", set()),
            patch.object(
                egg_hatch_listener,
                "get_pokemeow_reply_or_interaction_member",
                new_callable=AsyncMock,
                return_value=member,
            ),
            patch.object(
                egg_hatch_listener,
                "add_points_to_member",
                new_callable=AsyncMock,
            ) as add_points,
            patch.object(egg_hatch_listener, "pretty_log"),
            patch.object(egg_hatch_listener, "debug_log"),
        ):
            await egg_hatch_listener.egg_hatch_listener_func(Mock(), message)

        self.assertEqual(add_points.await_count, 2)
        self.assertEqual(
            [
                call.kwargs["display_pokemon_name"]
                for call in add_points.await_args_list
            ],
            [
                f"{egg_hatch_listener.rarity_meta['shiny']['emoji']} Tadbulb",
                f"{egg_hatch_listener.rarity_meta['shiny']['emoji']} Nymble",
            ],
        )
        self.assertTrue(
            all(call.kwargs["points"] == 2 for call in add_points.await_args_list)
        )

    def test_ignores_buddy_name_after_hatch_announcement(self):
        content = (
            "_.demon._ just hatched a Pancham! You have 262 eggs left.\n"
            "- **Shiny Tadbulb** gained 2,500 EXP!\n"
            "- Congratulations! Your **Shiny Tadbulb** is now level 68."
        )

        self.assertEqual(
            egg_hatch_listener.extract_event_hatches(content),
            [],
        )


if __name__ == "__main__":
    unittest.main()

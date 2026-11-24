import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from utils.listener_func.dex_listener import (
    dex_listener,
    extract_type_from_embed,
)


class DexListenerTests(unittest.IsolatedAsyncioTestCase):
    def test_extracts_single_and_dual_plain_types(self):
        self.assertEqual(
            extract_type_from_embed(
                {"fields": [{"name": "Type", "value": "Water"}]}
            ),
            "water",
        )
        self.assertEqual(
            extract_type_from_embed(
                {"fields": [{"name": "Type", "value": "Water / Dragon"}]}
            ),
            "water_dragon",
        )

    def test_extracts_types_from_pokemeow_emojis(self):
        embed = SimpleNamespace(
            fields=[
                SimpleNamespace(
                    name="Type",
                    value="<:poisontype:123> <:fairytype:456>",
                )
            ]
        )

        self.assertEqual(extract_type_from_embed(embed), "poison_fairy")

    async def test_persists_dex_details_including_type(self):
        embed = SimpleNamespace(
            author=SimpleNamespace(name="Fezandipiti #8164"),
            image=SimpleNamespace(url="https://example.com/fezandipiti.png"),
            fields=[
                SimpleNamespace(name="Rarity", value="<:Legendary:123>"),
                SimpleNamespace(
                    name="Type",
                    value="<:poisontype:456> <:fairytype:789>",
                ),
            ],
        )
        message = SimpleNamespace(embeds=[embed])
        update = AsyncMock()

        with (
            patch("utils.listener_func.dex_listener.update_pokemon_dex_info", update),
            patch("utils.listener_func.dex_listener.pretty_log"),
        ):
            await dex_listener(SimpleNamespace(), message)

        update.assert_awaited_once_with(
            SimpleNamespace(),
            "Fezandipiti",
            dex_number=8164,
            rarity="legendary",
            image_link="https://example.com/fezandipiti.png",
            pokemon_type="poison_fairy",
        )


if __name__ == "__main__":
    unittest.main()

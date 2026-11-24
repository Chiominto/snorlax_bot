import unittest
from unittest.mock import patch

from constants.paldea_galar_dict import rarity_meta
from utils.functions.pokemon_func import get_display_name, get_rarity


class PokemonDisplayNameTests(unittest.TestCase):
    def test_inline_dex_suffix_keeps_rarity_and_is_not_duplicated(self):
        display_name = get_display_name("Kabuto #9140", dex=True)

        self.assertEqual(
            display_name,
            f"{rarity_meta['uncommon']['emoji']} Kabuto #9140",
        )

    def test_inline_dex_suffix_keeps_shiny_emoji_without_duplicate(self):
        display_name = get_display_name("Shiny Alcremie #1869", dex=True)

        self.assertEqual(
            display_name,
            f"{rarity_meta['shiny']['emoji']} Alcremie #1869",
        )

    def test_mega_meganium_uses_mega_rarity_without_changing_base_form(self):
        mega_display_name = get_display_name("Mega Meganium #7314", dex=True)
        base_display_name = get_display_name("Meganium #7314", dex=True)

        self.assertEqual(
            mega_display_name,
            f"{rarity_meta['mega']['emoji']} Meganium #7314",
        )
        self.assertEqual(
            get_rarity("Mega Meganium"),
            "mega",
        )
        self.assertEqual(
            base_display_name,
            f"{rarity_meta['superrare']['emoji']} Meganium #7314",
        )
        self.assertEqual(get_rarity("Meganium"), "superrare")

    @patch("utils.functions.pokemon_func.get_dex_number_by_name", return_value=9140)
    def test_missing_inline_dex_suffix_uses_resolved_number(self, _get_dex_number):
        display_name = get_display_name("Kabuto", dex=True)

        self.assertEqual(
            display_name,
            f"{rarity_meta['uncommon']['emoji']} Kabuto #9140",
        )


if __name__ == "__main__":
    unittest.main()

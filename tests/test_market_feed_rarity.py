import unittest

from constants.paldea_galar_dict import Legendary_icon_url, rarity_meta
from utils.functions.market_feed_listener import (
    determine_rarity_from_name_and_author_icon,
)


class MarketFeedRarityTests(unittest.TestCase):
    def test_event_exclusive_color_uses_legendary_icon_rarity(self):
        rarity = determine_rarity_from_name_and_author_icon(
            "Kyurem-White",
            Legendary_icon_url,
            rarity_meta["event_exclusive"]["color"],
        )

        self.assertEqual(rarity, "legendary")

    def test_event_exclusive_color_uses_mega_name_prefix(self):
        rarity = determine_rarity_from_name_and_author_icon(
            "Mega Meganium",
            "",
            rarity_meta["event_exclusive"]["color"],
        )

        self.assertEqual(rarity, "mega")

    def test_base_meganium_is_not_mistaken_for_mega(self):
        rarity = determine_rarity_from_name_and_author_icon(
            "Meganium",
            "",
            rarity_meta["event_exclusive"]["color"],
        )

        self.assertEqual(rarity, "unknown")


if __name__ == "__main__":
    unittest.main()

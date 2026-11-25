import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from group_command_func.server_shop.view import shop_view_func


class ShopViewTests(unittest.IsolatedAsyncioTestCase):
    async def test_shop_view_defers_then_edits_original_response(self):
        sent_message = SimpleNamespace()
        interaction = SimpleNamespace(
            response=SimpleNamespace(defer=AsyncMock()),
            edit_original_response=AsyncMock(return_value=sent_message),
            followup=SimpleNamespace(send=AsyncMock()),
            user=SimpleNamespace(id=1),
        )
        bot = SimpleNamespace(get_guild=Mock(return_value=None))

        with (
            patch(
                "group_command_func.server_shop.view.check_burger_shop",
                new=AsyncMock(return_value=True),
            ),
            patch(
                "utils.cache.server_shop_cache.fetch_all_shop_items_cache",
                return_value={
                    "item-1": {
                        "item_name": "Potion",
                        "price": 10,
                        "stock": 1,
                        "dex": "N/A",
                    }
                },
            ),
            patch(
                "group_command_func.server_shop.view.Shop_Paginator.get_embed",
                new=AsyncMock(return_value=SimpleNamespace()),
            ),
        ):
            await shop_view_func(bot, interaction)

        interaction.response.defer.assert_awaited_once_with(
            ephemeral=False,
            thinking=True,
        )
        interaction.edit_original_response.assert_awaited_once()
        self.assertIs(
            interaction.edit_original_response.call_args.kwargs["view"].message,
            sent_message,
        )
        interaction.followup.send.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()

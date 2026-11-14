import unittest

from group_command_func.balloon.list_item import (
    FIELD_VALUE_LIMIT,
    MESSAGE_CHARACTER_LIMIT,
    MESSAGE_EMBED_LIMIT,
    _paginate_fields,
    _split_category_values,
)


class BalloonListItemTests(unittest.TestCase):
    def test_category_values_stay_within_discord_field_limit(self):
        items = ["Pikachu" * 150, "Eevee", "Snorlax"]

        values = _split_category_values(items, "✨ ")

        self.assertTrue(values)
        self.assertTrue(all(len(value) <= FIELD_VALUE_LIMIT for value in values))
        recovered_items = "".join(
            value[len("✨ ") :] for value in values
        ).split(", ")
        self.assertEqual(recovered_items, items)

    def test_fields_are_paginated_within_embed_and_message_limits(self):
        fields = [(f"Balloon {index}", "x" * 1000) for index in range(30)]

        pages = _paginate_fields(fields, total_count=30)

        self.assertGreater(len(pages), 1)
        self.assertEqual(
            sum(len(embed.fields) for page in pages for embed in page),
            len(fields),
        )
        for page in pages:
            self.assertLessEqual(len(page), MESSAGE_EMBED_LIMIT)
            self.assertLessEqual(sum(map(len, page)), MESSAGE_CHARACTER_LIMIT)
            for embed in page:
                self.assertLessEqual(len(embed.fields), 25)
                self.assertTrue(
                    all(
                        len(field.value) <= FIELD_VALUE_LIMIT
                        for field in embed.fields
                    )
                )


if __name__ == "__main__":
    unittest.main()

import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from utils.functions.pretty_defer import pretty_defer


class PrettyDeferTests(unittest.IsolatedAsyncioTestCase):
    def make_interaction(self, *, responded=False, original=None):
        async def send(**kwargs):
            if "view" in kwargs and kwargs["view"] is None:
                raise TypeError("view must not be None when sending")
            return SimpleNamespace(id=1)

        return SimpleNamespace(
            response=SimpleNamespace(
                is_done=lambda: responded,
                send_message=AsyncMock(side_effect=send),
            ),
            followup=SimpleNamespace(send=AsyncMock(side_effect=send)),
            channel=SimpleNamespace(send=AsyncMock(side_effect=send)),
            original_response=AsyncMock(
                return_value=original,
                side_effect=None if original else RuntimeError("no original response"),
            ),
        )

    async def test_initial_send_omits_none_view(self):
        interaction = self.make_interaction()
        await pretty_defer(interaction)
        self.assertNotIn("view", interaction.response.send_message.call_args.kwargs)

    async def test_initial_followup_omits_none_view(self):
        interaction = self.make_interaction(responded=True)
        await pretty_defer(interaction)
        self.assertNotIn("view", interaction.followup.send.call_args.kwargs)

    async def test_send_preserves_supplied_view(self):
        interaction = self.make_interaction()
        view = SimpleNamespace()
        await pretty_defer(interaction, view=view)
        self.assertIs(interaction.response.send_message.call_args.kwargs["view"], view)

    async def test_success_fallback_preserves_supplied_view(self):
        interaction = self.make_interaction()
        loader = await pretty_defer(interaction)
        view = SimpleNamespace()
        await loader.success(content="Done", view=view)
        self.assertIs(interaction.followup.send.call_args.kwargs["view"], view)

    async def test_success_and_edit_fallbacks_omit_none_view(self):
        for operation, ephemeral in (("success", True), ("success", False), ("edit", True)):
            with self.subTest(operation=operation, ephemeral=ephemeral):
                interaction = self.make_interaction()
                loader = await pretty_defer(interaction, ephemeral=ephemeral)
                await getattr(loader, operation)(content="Done")
                sender = interaction.followup.send if ephemeral else interaction.channel.send
                self.assertEqual(sender.await_count, 1)
                self.assertNotIn("view", sender.call_args.kwargs)

    async def test_success_edits_with_multiple_embeds(self):
        message = SimpleNamespace(id=1, edit=AsyncMock())
        interaction = self.make_interaction(original=message)
        loader = await pretty_defer(interaction)
        embeds = [SimpleNamespace(), SimpleNamespace()]

        await loader.success(content="", embeds=embeds)

        self.assertIs(message.edit.call_args.kwargs["embeds"], embeds)
        self.assertNotIn("embed", message.edit.call_args.kwargs)

    async def test_success_edit_can_clear_existing_view(self):
        message = SimpleNamespace(id=1, edit=AsyncMock())
        interaction = self.make_interaction(original=message)
        loader = await pretty_defer(interaction)
        await loader.success(content="Done")
        self.assertIsNone(message.edit.call_args.kwargs["view"])

    async def test_initial_send_failure_is_logged(self):
        interaction = self.make_interaction()
        interaction.response.send_message.side_effect = RuntimeError("send failed")
        with patch("utils.functions.pretty_defer.pretty_log") as log:
            await pretty_defer(interaction)
        self.assertIn("send failed", log.call_args.args[1])

    async def test_failed_edit_is_logged_before_fallback(self):
        message = SimpleNamespace(id=1, edit=AsyncMock(side_effect=RuntimeError("edit failed")))
        interaction = self.make_interaction(original=message)
        loader = await pretty_defer(interaction)
        with patch("utils.functions.pretty_defer.pretty_log") as log:
            await loader.success(content="Done")
        self.assertIn("edit failed", log.call_args.args[1])
        self.assertEqual(interaction.followup.send.await_count, 1)


if __name__ == "__main__":
    unittest.main()

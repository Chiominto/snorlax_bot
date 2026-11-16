import discord
from discord.ext import commands

from constants.celestial_constants import (
    CC_SERVER_ID,
    CELESTIAL_CATEGORIES,
    CELESTIAL_TEXT_CHANNELS,
    POKEMEOW_APPLICATION_ID,
)
from utils.autoresponder.pray import handle_pray_autoresponder
from utils.functions.market_feed_listener import process_market_feed_message
from utils.listener_func.autospawn_listener import as_spawn_ping
from utils.listener_func.dex_listener import dex_listener
from utils.listener_func.egg_hatch_listener import egg_hatch_listener_func
from utils.listener_func.quest_helper_listener import quest_helper_listener
from utils.listener_func.res_egg_listener import handle_res_egg_hatch
from utils.logs.pretty_log import pretty_log

MARKET_FEED_CHANNELS = {
    CELESTIAL_TEXT_CHANNELS.curs_feed,
    CELESTIAL_TEXT_CHANNELS.shiny_feed,
    CELESTIAL_TEXT_CHANNELS.golden_feed,
    CELESTIAL_TEXT_CHANNELS.legendmegagmax_feed,
}


def embed_has_field_name(embed, name_to_match: str) -> bool:
    """
    Returns True if any field name in the embed matches the given string.
    Returns False immediately if the embed has no fields.
    """
    if not hasattr(embed, "fields") or not embed.fields:
        return False
    for field in embed.fields:
        if field.name == name_to_match:
            return True
    return False


# 🟣────────────────────────────────────────────
#         💤 Message Create Listener Cog
# 🟣────────────────────────────────────────────
class MessageCreateListener(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 🟣────────────────────────────────────────────
    #         💤 Message Listener Event
    # 🟣────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):

        # ————————————————————————————————
        # 🏰 Guild Check — Route by server
        # ————————————————————————————————
        guild = message.guild
        if not guild:
            return  # Skip DMs

        # ————————————————————————————————
        # 💤 Message Variables
        # ————————————————————————————————
        content = message.content
        first_embed = message.embeds[0] if message.embeds else None
        first_embed_author = (
            first_embed.author.name if first_embed and first_embed.author else ""
        )
        first_embed_description = (
            first_embed.description if first_embed and first_embed.description else ""
        )
        first_embed_footer = (
            first_embed.footer.text if first_embed and first_embed.footer else ""
        )
        first_embed_title = (
            first_embed.title if first_embed and first_embed.title else ""
        )
        # ————————————————————————————————
        # 💤 Pray Listener
        # ————————————————————————————————
        if (
            content
            and content.lower().startswith("!pray")
            and message.channel.id == CELESTIAL_TEXT_CHANNELS.fries_shrine
        ):
            pretty_log(
                "info",
                f"Detected !pray command message: Message ID {message.id}",
                label="Pray Autoresponder",
            )
            await handle_pray_autoresponder(bot=self.bot, message=message)

        # ————————————————————————————————
        # 🏰 Ignore non-PokéMeow bot messages
        # ————————————————————————————————
        # 🚫 Ignore all bots except PokéMeow to prevent loops
        if (
            message.author.bot
            and message.author.id != POKEMEOW_APPLICATION_ID
            and not message.webhook_id
        ):
            return

        # ————————————————————————————————
        # 💤 Market Feeds Listener
        # ————————————————————————————————
        if message.channel.id in MARKET_FEED_CHANNELS:
            await process_market_feed_message(
                self.bot, message, market_category_id=CELESTIAL_CATEGORIES.MARKET
            )
        # ————————————————————————————————
        # 💤 Autospawn Listener
        # ————————————————————————————————
        if (
            message.channel.id == CELESTIAL_TEXT_CHANNELS.autospawn
            and message.author.id == POKEMEOW_APPLICATION_ID
        ):
            pretty_log(
                message=f"Autospawn detected",
                tag="info",
            )
            await as_spawn_ping(self.bot, message)

        # 🔧───────────────────────────────────────────────🔧
        # 🔧 Quest Helper Reward
        # 🔧───────────────────────────────────────────────🔧
        if first_embed and first_embed_description:
            if (
                first_embed_description
                and "completed the quest" in first_embed_description
                and "Receive 1" in first_embed_description
                and "from another player" in first_embed_description
            ):
                pretty_log(
                    "info",
                    f"Detected quest completion message for quest helper reward: Message ID {message.id}",
                    label="Quest Helper Listener",
                )
                await quest_helper_listener(bot=self.bot, message=message)

        # ————————————————————————————————
        # 🩵 DEX LISTENER
        # ————————————————————————————————
        if first_embed:
            if embed_has_field_name(first_embed, "Dex Number"):
                pretty_log(
                    "info",
                    f"Detected dex command embed with 'Dex Number' field. Triggering dex listener.",
                )
                await dex_listener(self.bot, message)

        # ————————————————————————————————
        # 🩵 EGG HATCH LISTENER
        # ————————————————————————————————
        if (
            message.embeds
            and message.embeds[0]
            and message.content
            and message.embeds[0].author
            and "hatched an Egg!" in (message.embeds[0].author.name or "")
            and "just hatched a" in message.content
        ):
            try:
                await egg_hatch_listener_func(bot=self.bot, message=message)
            except Exception as eh_e:
                pretty_log(
                    "error",
                    f"Egg hatch processing failed for message {message.id} in {message.channel.name}: {eh_e}",
                    source="egg_hatch_listener_func",
                )

        # ————————————————————————————————
        # 🩵 RESEARCH LAB EGG HATCH LISTENER
        # ————————————————————————————————
        if first_embed and "research lab hatch" in first_embed_author.lower():
            try:
                pretty_log(
                    "ready",
                    f"Processing Research Lab egg hatch from message ID {getattr(message, 'id', 'unknown')}",
                )
                await handle_res_egg_hatch(bot=self.bot, message=message)
                pretty_log(
                    "ready",
                    f"Successfully processed Research Lab egg hatch from message ID {getattr(message, 'id', 'unknown')}",
                )
            except Exception as e:
                pretty_log(
                    "critical",
                    f"Failed processing Research Lab egg hatch from message ID {getattr(message, 'id', 'unknown')}: {e}",
                )

# 🟣────────────────────────────────────────────
#         💤 Setup Function
# 🟣────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(MessageCreateListener(bot))

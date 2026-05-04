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
from utils.logs.pretty_log import pretty_log

MARKET_FEED_CHANNELS = {
    CELESTIAL_TEXT_CHANNELS.curs_feed,
    CELESTIAL_TEXT_CHANNELS.shiny_feed,
    CELESTIAL_TEXT_CHANNELS.golden_feed,
    CELESTIAL_TEXT_CHANNELS.legendmegagmax_feed,
}


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


# 🟣────────────────────────────────────────────
#         💤 Setup Function
# 🟣────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(MessageCreateListener(bot))

import discord
from discord.ext import commands

from constants.shellshuckle_constants import (
    CC_SERVER_ID,
    POKEMEOW_APPLICATION_ID,
    SHELLSHUCKLE_CATEGORIES,
    SHELLSHUCKLE_TEXT_CHANNELS,
)
from utils.functions.market_feed_listener import process_market_feed_message
from utils.logs.pretty_log import pretty_log

MARKET_FEED_CHANNELS = {
    SHELLSHUCKLE_TEXT_CHANNELS.curs_feed,
    SHELLSHUCKLE_TEXT_CHANNELS.shiny_feed,
    SHELLSHUCKLE_TEXT_CHANNELS.golden_feed,
    SHELLSHUCKLE_TEXT_CHANNELS.legendmegagmax_feed,
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
                self.bot, message, market_category_id=SHELLSHUCKLE_CATEGORIES.MARKET
            )


# 🟣────────────────────────────────────────────
#         💤 Setup Function
# 🟣────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(MessageCreateListener(bot))

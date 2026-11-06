import discord
from discord.ext import commands

from constants.celestial_constants import CC_SERVER_ID, POKEMEOW_APPLICATION_ID
from utils.functions.burger_shop import check_burger_shop
from utils.listener_func.rarespawn_listener import handle_rarespawn_catch
from utils.logs.pretty_log import pretty_log
from constants.paldea_galar_dict import rarity_meta
triggers = {
    "icon_unlock": "as your icon with `/battle set-icon",
}
FISHING_COLOR = 8900346
LOW_RARITY_COLORS = [
    rarity_meta["rare"]["color"],
    rarity_meta["superrare"]["color"],
    rarity_meta["common"]["color"],
    rarity_meta["uncommon"]["color"],
]
# 🟣────────────────────────────────────────────
#         💤 Message Edit Listener Cog
# 🟣────────────────────────────────────────────
class OnMessageEditCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 🟣────────────────────────────────────────────
    #         💤 Message Listener Event
    # 🟣────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):

        # ————————————————————————————————
        # 🏰 Guild Check — Route by server
        # ————————————————————————————————
        guild = after.guild
        if not guild:
            return  # Skip DMs

        # ————————————————————————————————
        # 💤 Message Variables
        # ————————————————————————————————
        content = after.content
        first_embed = after.embeds[0] if after.embeds else None
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
        first_embed_color = first_embed.color.value if first_embed and first_embed.color else None

        # ————————————————————————————————
        # 🏰 Ignore non-PokéMeow bot messages
        # ————————————————————————————————
        # 🚫 Ignore all bots except PokéMeow to prevent loops
        if (
            after.author.bot
            and after.author.id != POKEMEOW_APPLICATION_ID
            and not after.webhook_id
        ):
            return

        # 🔧───────────────────────────────────────────────🔧
        # 🔧    Rarespawn Handler
        # 🔧───────────────────────────────────────────────🔧
        if first_embed and first_embed_color not in LOW_RARITY_COLORS:
            if first_embed_description and "You caught" in first_embed_description:
                await handle_rarespawn_catch(
                    bot=self.bot,
                    before_message=before,
                    after_message=after,
                )

# 🟣────────────────────────────────────────────
#         💤 Setup Function
# 🟣────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(OnMessageEditCog(bot))

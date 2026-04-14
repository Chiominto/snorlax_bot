from utils.logs.pretty_log import pretty_log
# 🍩────────────────────────────────────────────
#        💤 Processed ids Cache
# 🍩────────────────────────────────────────────
processed_market_feed_message_ids = set()
processed_snipe_ids = set()
LIST_OF_PROCESSED_IDS = [
    processed_market_feed_message_ids,
    processed_snipe_ids,
]
def clear_processed_ids_cache():
    for id_set in LIST_OF_PROCESSED_IDS:
        id_set.clear()
    pretty_log("cache", "✅ Cleared all processed IDs caches.")

# 🍩────────────────────────────────────────────
#        💤 Webhook Url Cache
# 🍩────────────────────────────────────────────
webhook_url_cache: dict[tuple[int, int], dict[str, str]] = {}
#     ...
#
# }
# key = (bot_id, channel_id)
# Structure:
# webhook_url_cache = {
# (bot_id, channel_id): {
#     "url": "https://discord.com/api/webhooks/..."
#     "channel_name": "alerts-channel",
# },
#
# 🍩────────────────────────────────────────────
#        💤 Pokemon Cache
# 🍩────────────────────────────────────────────
pokemon_cache: dict[str, dict[str, str | int]] = {}
#     ...
#
# }
# Structure:
# pokemon_cache = {
# "pokemon_name": {
#     "dex_number": int,
#     "rarity": str,
#     "current_listing": int,
#     "lowest_market": int,
#     "true_lowest": int,
#     "listing_seen": str,
#     "emoji_id": str,
#     "image_link": str,
#     "last_updated": datetime
# },

# 🍩────────────────────────────────────────────
#        💤 Market Alert Cache
# 🍩────────────────────────────────────────────
market_alert_cache: list[dict] = []
# Structure
# {
#   "user_id": int,
#   "pokemon": str,
#   "dex_number": int,
#   "max_price": int,
#   "channel_id": int,
#   "ping": bool,
# }
# 🍩────────────────────────────────────────────
#        💤 Market Alert Index Cache
# 🍩────────────────────────────────────────────
_market_alert_index: dict[tuple[str, int], dict] = (
    {}
)  # key = (pokemon.lower(), channel_id)
# Structure
# {
#   (pokemon.lower(), channel_id): {
#       "user_id": int,
#       "pokemon": str,
#       "dex_number": int,
#       "max_price": int,
#       "channel_id": int,
#       "ping": bool,
#   }

# 🍩────────────────────────────────────────────
#        💤 Pokemon List Cache
# 🍩────────────────────────────────────────────
pokemon_list_cache: dict[str, int] = {}
# Structure:
# pokemon_list_cache = {
#     "pokemon_name": "dex_number",
#     }

# 🧩────────────────────────────────────────────
#        ⚡ Celestial Members Cache
# 🧩────────────────────────────────────────────
celestial_members_cache: dict[int, dict] = {}
# Structure:
# user_id -> {
#   "user_name": str,
#   "pokemon_name": str,
#   "channel_id": int
#   "actual_perks": str
#   "clan_bank_donation": int
#   "clan_treasury_doantion": int
#   "date_joined": int
# }


processing_end_giveaway_message_ids = set()


active_lottery_thread_ids: set[int] = set()
processing_end_lottery_ids: set[int] = set()
processing_lottery_purchase_ids: set[int] = set()

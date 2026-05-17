import discord

from constants.celestial_constants import (
    CELESTIAL_ROLES,
)

REQUIRED_ROLES = [
    CELESTIAL_ROLES.staff,
    CELESTIAL_ROLES.khy_role
]
ALLOWED_JOIN_ROLES = [CELESTIAL_ROLES.celestialnova_, CELESTIAL_ROLES.cosmic_catch_goal]
BLACKLISTED_ROLES = [
    CELESTIAL_ROLES.out_of_orbit,
    CELESTIAL_ROLES.muted,
    CELESTIAL_ROLES.grounded,
    CELESTIAL_ROLES.coin_saver,
]


DEFAULT_ALLOWED_DISPLAY = ", ".join(f"<@&{rid}>" for rid in ALLOWED_JOIN_ROLES)
BLACKLISTED_DISPLAY = ", ".join(f"<@&{rid}>" for rid in BLACKLISTED_ROLES)

Extra_Entries = {
    CELESTIAL_ROLES.top_catcher: 2,
    CELESTIAL_ROLES.server_booster: 1,
}
GIVEAWAY_ROLES = [
    CELESTIAL_ROLES.celestialnova_,
    CELESTIAL_ROLES.out_of_orbit,
    CELESTIAL_ROLES.muted,
    CELESTIAL_ROLES.grounded,
    CELESTIAL_ROLES.coin_saver,
    CELESTIAL_ROLES.top_catcher,
    CELESTIAL_ROLES.server_booster,
]
REG_GA_MIN_DURATION_SECONDS = 30 * 60


def format_roles_display(role_ids, guild: discord.Guild) -> str:

    if not role_ids:
        return "None"

    # Convert role IDs to role names
    role_names = []
    for role_id in role_ids:
        role = guild.get_role(role_id)
        if role:
            role_names.append(role.name)
        else:
            continue  # Skip if role not found
    return ", ".join(role_names) if role_names else "None"

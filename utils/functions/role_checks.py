import discord
from discord.ext import commands
from discord import app_commands
from constants.celestial_constants import CELESTIAL_ROLES, KHY_USER_ID
from utils.logs.pretty_log import pretty_log


# 🌸──────────────────────────────────────────────────────
# ✨ Custom Exceptions (Sparkles & Cute!) ✨
# ───────────────────────────────────────────────────────
class OwnerCoownerCheckFailure(app_commands.CheckFailure):
    pass


class StaffCheckFailure(app_commands.CheckFailure):
    pass


# 🌸──────────────────────────────────────────────────────
# 🐾💫 Cute Error Messages by Server — Cottagecore Style 💫🌿
# ───────────────────────────────────────────────────────
ERROR_MESSAGES = {
    "staff": "Only staff members can use this command. If you think this is a mistake, please contact the server staff.",
    "owner_coowner": "Only the server owner and co-owner can use this command. If you think this is a mistake, please contact the server staff.",
}


# 🌸──────────────────────────────────────────────────────
# 🔹 Helper function
# ───────────────────────────────────────────────────────
def has_role(user_roles, role_id):
    """Check if user has a role ID"""
    return role_id in [role.id for role in user_roles]


# 🌸──────────────────────────────────────────────────────
# 🔹 Slash command decorators
# ───────────────────────────────────────────────────────
def staff_only():
    async def predicate(interaction: discord.Interaction):
        # Allow khy (user id: 952071312124313611)
        if getattr(interaction.user, "id", None) == KHY_USER_ID:
            return True
        if not has_role(interaction.user.roles, CELESTIAL_ROLES.staff):
            raise StaffCheckFailure(ERROR_MESSAGES["staff"])
        return True

    return app_commands.check(predicate)

def owner_and_co_owner_only():
    async def predicate(interaction: discord.Interaction):
        # Allow khy (user id: 952071312124313611)
        if getattr(interaction.user, "id", None) == KHY_USER_ID:
            return True
        if not (
            has_role(interaction.user.roles, CELESTIAL_ROLES.clan_owner_)
            or has_role(interaction.user.roles, CELESTIAL_ROLES.co_owner)
        ):
            raise OwnerCoownerCheckFailure(ERROR_MESSAGES["owner_coowner"])
        return True

    return app_commands.check(predicate)

# Check if user is staff member
def is_staff_member(member: discord.Member) -> bool:
    """
    Checks if a member has any vna staff roles.
    """
    staff_role_ids = [CELESTIAL_ROLES.staff, CELESTIAL_ROLES.clan_owner_, CELESTIAL_ROLES.co_owner]
    if any(role.id in staff_role_ids for role in member.roles):
        return True
    return False

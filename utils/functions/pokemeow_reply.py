import discord


async def get_pokemeow_reply_member(message: discord.Message) -> discord.Member | None:
    """
    Determines if the message is a PokéMeow bot reply.
    If yes, returns the member that PokéMeow replied to.
    Returns None otherwise.
    """
    # 🛑 Only process messages from PokéMeow
    author_str = str(message.author).lower()
    if "pokémeow" not in author_str and "pokemeow" not in author_str:
        return None

    # 🛑 Ensure the message is a reply
    if not getattr(message, "reference", None):
        return None

    resolved_msg = getattr(message.reference, "resolved", None)

    # Fallback for uncached replied messages.
    if not isinstance(resolved_msg, discord.Message):
        ref_message_id = getattr(message.reference, "message_id", None)
        if not ref_message_id:
            return None

        try:
            resolved_msg = await message.channel.fetch_message(ref_message_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return None

    if not isinstance(resolved_msg, discord.Message):
        return None

    member = (
        resolved_msg.author if isinstance(resolved_msg.author, discord.Member) else None
    )
    return member




async def get_pokemeow_reply_two(message: discord.Message) -> discord.Member | None:
    """
    Determines if the message is a PokéMeow bot reply.
    If yes, returns the member that PokéMeow replied to.
    Returns None otherwise.
    """
    # 🛑 Only process messages from PokéMeow
    author_str = str(message.author).lower()
    if "pokémeow" not in author_str and "pokemeow" not in author_str:
        return None

    # 🛑 Ensure the message is a reply
    if not getattr(message, "reference", None):
        return None

    resolved_msg = getattr(message.reference, "resolved", None)
    if not isinstance(resolved_msg, discord.Message):
        return None

    member = (
        resolved_msg.author if isinstance(resolved_msg.author, discord.Member) else None
    )
    return member


def get_message_interaction_member(
    message: discord.Message,
) -> discord.Member | discord.User | None:
    """
    Returns the member who triggered the interaction that created this message, if available.
    Returns None if not an interaction-created message or not a guild interaction.
    """
    interaction_metadata = getattr(message, "interaction_metadata", None)
    if not interaction_metadata:
        return None

    member = getattr(interaction_metadata, "member", None)
    if isinstance(member, discord.Member):
        return member

    user = getattr(interaction_metadata, "user", None)
    if isinstance(user, (discord.Member, discord.User)):
        return user

    return None


async def get_pokemeow_reply_or_interaction_member(
    message: discord.Message,
) -> discord.Member | discord.User | None:
    """
    Returns the member who was replied to, or the interaction user as a fallback.
    """
    member = await get_pokemeow_reply_two(message)
    if member:
        return member

    return get_message_interaction_member(message)

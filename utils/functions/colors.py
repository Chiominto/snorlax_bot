import random
import discord


def get_random_snorlax_color():
    """Returns a random pastel color inspired by Snorlax."""
    # Pastel blues, teals, and creams inspired by Snorlax’s body and belly
    pastel_colors = [
        (120, 150, 180),  # Muted blue-gray
        (160, 190, 200),  # Soft teal
        (200, 220, 230),  # Pale sky blue
        (240, 235, 210),  # Creamy beige (belly)
        (210, 225, 240),  # Gentle pastel blue
        (180, 200, 190),  # Dusty green-gray
        (230, 240, 220),  # Light moss pastel
        (250, 245, 230),  # Warm cream
        (190, 210, 220),  # Misty gray-blue
        (170, 180, 200),  # Sleepy lavender-gray
    ]
    r, g, b = random.choice(pastel_colors)
    return discord.Colour.from_rgb(r, g, b)

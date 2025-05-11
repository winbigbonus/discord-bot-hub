"""
Assets for the gambling bot
Contains vector representations of casino game icons and symbols
"""

# Slot machine symbols
SLOT_SYMBOLS = {
    "diamond": {
        "emoji": "💎",
        "svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-diamond"><rect x="1" y="5" width="22" height="14" rx="7" ry="7"></rect><path d="M8 2l4 4 4-4M8 22l4-4 4 4M2 8l4 4-4 4M22 8l-4 4 4 4M12 2v20M2 12h20"></path></svg>"""
    },
    "heart": {
        "emoji": "❤️",
        "svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-heart"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>"""
    },
    "lemon": {
        "emoji": "🍋",
        "svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="12" rx="10" ry="8" fill="#FFD700"></ellipse><path d="M4 12a8 4 0 1 0 16 0" stroke="#654321"></path><path d="M12 4c-2 0-4 3.5-4 8s2 8 4 8" stroke="#654321"></path></svg>"""
    },
    "melon": {
        "emoji": "🍉",
        "svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a10 10 0 0 1 10 10c0 5.5-4.5 10-10 10S2 17.5 2 12A10 10 0 0 1 12 2z" fill="#FF5555"></path><path d="M12 2v20" stroke="#33CC33"></path><path d="M2 12h20" stroke="#33CC33"></path></svg>"""
    },
    "seven": {
        "emoji": "7️⃣",
        "svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2" ry="2" fill="#CC0000"></rect><path d="M8 8h8l-4 12" stroke="white" stroke-width="2"></path></svg>"""
    },
    "horseshoe": {
        "emoji": "🧲",
        "svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3C7 3 3 7 3 12v3c0 3 2 5 5 5h8c3 0 5-2 5-5v-3c0-5-4-9-9-9z" fill="#CC9933"></path><path d="M3 15v-3a9 9 0 0 1 18 0v3" stroke="#333"></path><path d="M7 20v2M17 20v2" stroke="#333"></path></svg>"""
    }
}

# Card suits
CARD_SUITS = ["♠️", "♥️", "♦️", "♣️"]

# Card values
CARD_VALUES = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]

# Dice faces
DICE_FACES = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]

# Connect 4 pieces
CONNECT4_PIECES = {
    "empty": "⚪",
    "red": "🔴",
    "yellow": "🟡"
}

# Function to get slot icon based on the name (with fallback)
def get_slot_icon(name):
    """Get the emoji representation of a slot symbol"""
    if name in SLOT_SYMBOLS:
        return SLOT_SYMBOLS[name]["emoji"]
    return "❓"  # Fallback

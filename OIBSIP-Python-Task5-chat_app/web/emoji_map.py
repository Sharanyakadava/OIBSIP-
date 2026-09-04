"""
emoji_map.py
Small shortcode -> Unicode emoji dictionary, plus a helper to replace
:shortcode: patterns in a message with the corresponding emoji.
Not exhaustive - covers the common ones people actually type.
"""

import re

EMOJI_MAP = {
    "smile": "😄",
    "grin": "😁",
    "laughing": "😆",
    "joy": "😂",
    "wink": "😉",
    "blush": "😊",
    "sunglasses": "😎",
    "heart_eyes": "😍",
    "thinking": "🤔",
    "cry": "😢",
    "sob": "😭",
    "angry": "😠",
    "scream": "😱",
    "wave": "👋",
    "thumbsup": "👍",
    "+1": "👍",
    "thumbsdown": "👎",
    "-1": "👎",
    "clap": "👏",
    "pray": "🙏",
    "ok_hand": "👌",
    "muscle": "💪",
    "heart": "❤️",
    "broken_heart": "💔",
    "fire": "🔥",
    "star": "⭐",
    "tada": "🎉",
    "100": "💯",
    "eyes": "👀",
    "rocket": "🚀",
    "check": "✅",
    "x": "❌",
    "warning": "⚠️",
    "coffee": "☕",
    "pizza": "🍕",
}

_SHORTCODE_PATTERN = re.compile(r":([a-zA-Z0-9_+-]+):")


def render_emoji(text):
    """Replace every :shortcode: in text with its emoji, if known."""
    def _replace(match):
        code = match.group(1).lower()
        return EMOJI_MAP.get(code, match.group(0))

    return _SHORTCODE_PATTERN.sub(_replace, text)

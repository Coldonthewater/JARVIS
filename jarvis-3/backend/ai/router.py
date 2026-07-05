"""
Router — decides whether a request should be handled locally or
escalated to the cloud, based on WHAT KIND of request it is.

Why category-based, not just "simple vs complex":
    A category-based approach mirrors how a person would delegate tasks
    — "small, routine things I handle myself; anything that needs real
    thought or research, I bring in help for." It's also much easier to
    reason about and tune than an abstract complexity score: if
    something is misrouted, you can look at the category list and fix
    exactly that case, rather than guessing why a fuzzy score was off.

LOCAL categories (fast, free, works offline):
    - everyday_conversation  (small talk, greetings, general chat)
    - app_control             (open/close apps)
    - smart_home              (lights, thermostats, plugs, etc.)
    - weather
    - memory_preference       (remembering/recalling user preferences)
    - automation              (running a saved automation/routine)

CLOUD categories (need real reasoning power):
    - code                    (writing or reviewing code)
    - planning                (long-term planning, multi-step strategy)
    - research
    - document_summary        (summarizing large documents)

Offline fallback:
    When there's no internet connection at all, every request is
    forced local regardless of category — handled via the `is_offline`
    flag passed in by the caller (engine.py will wire this up to a
    real connectivity check in a later module; for now it defaults to
    False).

Confidence escalation:
    Even a request classified as LOCAL can still be escalated after
    the fact: if the local model's own response contains an
    uncertainty phrase (see settings.ai_uncertainty_phrase_list), the
    engine automatically retries the same request via the cloud
    provider. That check lives in engine.py, since it depends on the
    response text, not just the incoming message — this file only
    exposes the helper function that does the phrase check.
"""

from enum import Enum

from backend.ai.base import Message
from backend.core.logging_setup import get_logger

logger = get_logger(__name__)


class Category(str, Enum):
    # Local
    EVERYDAY_CONVERSATION = "everyday_conversation"
    APP_CONTROL = "app_control"
    SMART_HOME = "smart_home"
    WEATHER = "weather"
    MEMORY_PREFERENCE = "memory_preference"
    AUTOMATION = "automation"
    # Cloud
    CODE = "code"
    PLANNING = "planning"
    RESEARCH = "research"
    DOCUMENT_SUMMARY = "document_summary"


# Which tier each category belongs to. This is the single source of
# truth the engine consults to decide local vs. cloud for a category.
LOCAL_CATEGORIES = frozenset({
    Category.EVERYDAY_CONVERSATION,
    Category.APP_CONTROL,
    Category.SMART_HOME,
    Category.WEATHER,
    Category.MEMORY_PREFERENCE,
    Category.AUTOMATION,
})

CLOUD_CATEGORIES = frozenset({
    Category.CODE,
    Category.PLANNING,
    Category.RESEARCH,
    Category.DOCUMENT_SUMMARY,
})

# Keyword signals per category, checked in the order below. Order
# matters where phrases could overlap — more specific/high-signal
# categories are checked first. This is a starting point, tuned over
# time as real usage shows what gets misclassified; see
# docs/future-features.md for a smarter version using a local
# classifier model instead of keywords.
_CATEGORY_KEYWORDS: dict[Category, tuple[str, ...]] = {
    Category.CODE: (
        "code", "function", "script", "debug", "bug", "programming",
        "python", "javascript", "refactor", "compile", "repository",
        "pull request", "unit test",
    ),
    Category.RESEARCH: (
        "research", "look up", "find out about", "compare options",
        "what are the pros and cons", "investigate",
    ),
    Category.DOCUMENT_SUMMARY: (
        "summarize", "summarise", "tl;dr", "give me a summary",
        "shorten this", "key points from",
    ),
    Category.PLANNING: (
        "plan", "strategy", "roadmap", "schedule my", "long-term",
        "step by step plan", "outline a",
    ),
    Category.SMART_HOME: (
        "lights", "light", "thermostat", "temperature", "plug",
        "turn on", "turn off", "dim", "lock the door", "unlock",
    ),
    Category.WEATHER: (
        "weather", "forecast", "temperature outside", "rain", "snow",
        "is it going to",
    ),
    Category.APP_CONTROL: (
        "open ", "close ", "launch ", "quit ", "start the app",
    ),
    Category.MEMORY_PREFERENCE: (
        "remember that", "don't forget", "my favorite", "my preference",
        "what do you know about me", "what did i tell you",
    ),
    Category.AUTOMATION: (
        "run my", "start my routine", "automation", "good morning routine",
        "good night routine",
    ),
}


def classify(latest_message: Message, *, is_offline: bool = False) -> Category:
    """
    Classifies a single user message into one of the categories above.

    Args:
        latest_message: the message to classify.
        is_offline: if True (no internet connection detected), always
            returns EVERYDAY_CONVERSATION so the request stays local
            regardless of content.

    Defaults to EVERYDAY_CONVERSATION (local) when nothing matches —
    the safe, cheap default for anything ambiguous.
    """
    if is_offline:
        logger.debug("Offline detected — forcing local routing")
        return Category.EVERYDAY_CONVERSATION

    text = latest_message.content.lower()

    for category, keywords in _CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                logger.debug(f"Classified as {category.value} (matched '{keyword}')")
                return category

    logger.debug("No category keywords matched — defaulting to everyday_conversation")
    return Category.EVERYDAY_CONVERSATION


def is_local_category(category: Category) -> bool:
    return category in LOCAL_CATEGORIES


def response_seems_uncertain(response_text: str, uncertainty_phrases: list[str]) -> bool:
    """
    Checks whether a (local model's) response text contains any phrase
    signaling low confidence, used by the engine to decide whether to
    escalate to cloud even though the request was routed local.
    """
    lowered = response_text.lower()
    return any(phrase in lowered for phrase in uncertainty_phrases)

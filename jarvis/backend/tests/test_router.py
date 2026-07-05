"""Tests for backend/ai/router.py — category classification and helpers."""

from backend.ai.base import Message
from backend.ai.router import (
    Category,
    classify,
    is_local_category,
    response_seems_uncertain,
)


def test_greeting_defaults_to_everyday_conversation():
    message = Message(role="user", content="hey what's up")
    assert classify(message) == Category.EVERYDAY_CONVERSATION


def test_code_request_classified_as_code():
    message = Message(role="user", content="can you write a python function for me")
    assert classify(message) == Category.CODE


def test_smart_home_request_classified_correctly():
    message = Message(role="user", content="turn on the living room lights")
    assert classify(message) == Category.SMART_HOME


def test_weather_request_classified_correctly():
    message = Message(role="user", content="what's the weather forecast today")
    assert classify(message) == Category.WEATHER


def test_planning_request_classified_correctly():
    message = Message(role="user", content="help me build a long-term plan for this project")
    assert classify(message) == Category.PLANNING


def test_research_request_classified_correctly():
    message = Message(role="user", content="research the best electric cars this year")
    assert classify(message) == Category.RESEARCH


def test_summary_request_classified_correctly():
    message = Message(role="user", content="summarize this document for me")
    assert classify(message) == Category.DOCUMENT_SUMMARY


def test_offline_forces_everyday_conversation_regardless_of_content():
    message = Message(role="user", content="write a python script to sort a list")
    assert classify(message, is_offline=True) == Category.EVERYDAY_CONVERSATION


def test_local_categories_are_flagged_local():
    assert is_local_category(Category.EVERYDAY_CONVERSATION) is True
    assert is_local_category(Category.SMART_HOME) is True
    assert is_local_category(Category.CODE) is False


def test_uncertain_response_detected():
    phrases = ["i'm not sure", "i don't know"]
    assert response_seems_uncertain("I'm not sure about that one.", phrases) is True


def test_confident_response_not_flagged_uncertain():
    phrases = ["i'm not sure", "i don't know"]
    assert response_seems_uncertain("The weather today is sunny and 72 degrees.", phrases) is False

"""
Tests for the EventBus.

These establish the testing pattern the rest of the project will follow:
  - One test file per module, mirroring the backend/ folder structure
  - pytest-asyncio for testing async code
  - Tests are named test_<behavior_being_verified>
"""

import pytest

from backend.core.event_bus import Event, EventBus


@pytest.mark.asyncio
async def test_subscriber_receives_published_event():
    bus = EventBus()
    received: list[Event] = []

    async def handler(event: Event) -> None:
        received.append(event)

    bus.subscribe("test_event", handler)
    await bus.publish(Event(name="test_event", payload={"value": 42}, source="test"))

    assert len(received) == 1
    assert received[0].payload["value"] == 42


@pytest.mark.asyncio
async def test_unsubscribed_handler_does_not_receive_event():
    bus = EventBus()
    received: list[Event] = []

    async def handler(event: Event) -> None:
        received.append(event)

    bus.subscribe("test_event", handler)
    bus.unsubscribe("test_event", handler)
    await bus.publish(Event(name="test_event", source="test"))

    assert len(received) == 0


@pytest.mark.asyncio
async def test_publishing_event_with_no_subscribers_does_not_raise():
    bus = EventBus()
    # Should simply do nothing — not raise an exception.
    await bus.publish(Event(name="nobody_listening", source="test"))


@pytest.mark.asyncio
async def test_one_failing_handler_does_not_block_others():
    bus = EventBus()
    received: list[str] = []

    async def failing_handler(event: Event) -> None:
        raise ValueError("intentional failure for testing")

    async def working_handler(event: Event) -> None:
        received.append("ok")

    bus.subscribe("test_event", failing_handler)
    bus.subscribe("test_event", working_handler)
    await bus.publish(Event(name="test_event", source="test"))

    # The working handler should still have run despite the other failing.
    assert received == ["ok"]


@pytest.mark.asyncio
async def test_multiple_subscribers_all_receive_event():
    bus = EventBus()
    counts = {"a": 0, "b": 0}

    async def handler_a(event: Event) -> None:
        counts["a"] += 1

    async def handler_b(event: Event) -> None:
        counts["b"] += 1

    bus.subscribe("test_event", handler_a)
    bus.subscribe("test_event", handler_b)
    await bus.publish(Event(name="test_event", source="test"))

    assert counts == {"a": 1, "b": 1}

"""
Global stop flags for background tasks (import / processing).
Thread-safe: uses sets protected by a lock.

Supports two levels:
- Event-level stop: stops ALL tasks for an event (import, processing, all cards)
- Card-level stop: stops only a specific card's processing
"""
import threading

_lock = threading.Lock()
_stopped_events: set[int] = set()
_stopped_cards: set[int] = set()


def request_stop(event_id: int) -> None:
    """Stop everything for this event."""
    with _lock:
        _stopped_events.add(event_id)


def request_stop_card(card_id: int) -> None:
    """Stop only a specific card."""
    with _lock:
        _stopped_cards.add(card_id)


def should_stop(event_id: int) -> bool:
    """Check if this event should stop (used by process_event and import)."""
    with _lock:
        return event_id in _stopped_events


def should_stop_card(event_id: int, card_id: int) -> bool:
    """Check if a card-level task should stop."""
    with _lock:
        return event_id in _stopped_events or card_id in _stopped_cards


def clear_stop(event_id: int) -> None:
    """Clear event-level stop flag."""
    with _lock:
        _stopped_events.discard(event_id)


def clear_stop_card(card_id: int) -> None:
    """Clear card-level stop flag."""
    with _lock:
        _stopped_cards.discard(card_id)

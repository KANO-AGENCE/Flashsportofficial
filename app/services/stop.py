"""
Global stop flags for background tasks (import / processing).
Thread-safe: uses a set protected by a lock.
"""
import threading

_lock = threading.Lock()
_stopped: set[int] = set()  # event IDs that should stop


def request_stop(event_id: int) -> None:
    with _lock:
        _stopped.add(event_id)


def should_stop(event_id: int) -> bool:
    with _lock:
        return event_id in _stopped


def clear_stop(event_id: int) -> None:
    with _lock:
        _stopped.discard(event_id)

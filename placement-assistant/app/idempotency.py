"""Stable fingerprints for side effects. Hashing, used for exactly-once."""
import hashlib  # noqa: F401
import json  # noqa: F401
import re
from datetime import date


def canonical_json(value) -> str:
    """TODO (Part 2.1): one spelling per meaning.
    Sorted keys, no spaces, and whole floats as integers (12.0 and 12 are the same drive id),
    including inside nested dicts and lists."""
    def normalise(item):
        if isinstance(item, float) and item.is_integer():
            return int(item)
        if isinstance(item, dict):
            return {key: normalise(item[key]) for key in sorted(item)}
        if isinstance(item, list):
            return [normalise(value) for value in item]
        if isinstance(item, tuple):
            return [normalise(value) for value in item]
        return item

    return json.dumps(normalise(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def idempotency_key(run_id: str, step_seq: int, tool_name: str, args: dict) -> str:
    """TODO (Part 2.1): the same tool call at the same step of the same run must always get the same key.
    SHA-256 hex digest of canonical_json([run_id, step_seq, tool_name, args]).

    Today it returns a random value, so a replayed call looks brand new."""
    payload = canonical_json([run_id, step_seq, tool_name, args]).encode()
    return hashlib.sha256(payload).hexdigest()


def notification_dedupe_key(roll_no: str, message: str, day: date) -> str:
    """TODO (Part 3.3): the same message to the same student on the same day is one notification.
    SHA-256 hex of canonical_json([roll_no, message with runs of whitespace collapsed and trimmed, day.isoformat()]).

    Today it returns a random value, so nothing is ever deduplicated."""
    clean_message = re.sub(r"\s+", " ", message).strip()
    payload = canonical_json([roll_no, clean_message, day.isoformat()]).encode()
    return hashlib.sha256(payload).hexdigest()

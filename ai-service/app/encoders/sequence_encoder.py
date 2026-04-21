"""
Sequence Encoder — Event Timeline Feature Extractor.

Converts a task's history of status transitions (activity_log rows) into a
structured feature vector capturing temporal patterns that are invisible
to single-snapshot models.

Input format (each event in the sequence):
  {
    "from_status": "TODO",
    "to_status": "IN_PROGRESS",
    "timestamp": "2026-04-15T10:00:00Z",   # ISO string or float epoch
    "time_in_status_hours": 24.5
  }

Output: 10-dim float32 feature vector:
  [0] avg_time_todo_hours
  [1] avg_time_in_progress_hours
  [2] avg_time_review_hours
  [3] num_transitions
  [4] num_reopens           (DONE → any backward jump)
  [5] transition_rate       (transitions / max(days_elapsed, 1))
  [6] fraction_time_blocked
  [7] max_single_phase_hours
  [8] total_elapsed_hours
  [9] has_history           (1.0 if any events, 0.0 if new task)
"""

import numpy as np
from typing import List, Dict, Any
from datetime import datetime, timezone

SEQ_DIM = 10

_STATUS_ORDER = {"TODO": 0, "IN_PROGRESS": 1, "REVIEW": 2, "DONE": 3}


def _parse_hours(val) -> float:
    """Safely convert time_in_status_hours to float."""
    try:
        return float(val) if val is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


class SequenceEncoder:
    """
    Stateless encoder — transforms a list of status-transition events
    into a fixed-size 10-dim feature vector.
    For tasks with no history, returns sensible defaults (all zeros except has_history=0).
    """

    def encode(self, events: List[Dict[str, Any]]) -> np.ndarray:
        """
        Args:
            events: List[dict] — ordered status transition events, oldest first.
        Returns:
            np.ndarray shape (SEQ_DIM,)
        """
        if not events:
            return np.zeros(SEQ_DIM, dtype=np.float32)

        times_by_status: Dict[str, List[float]] = {
            "TODO": [], "IN_PROGRESS": [], "REVIEW": [], "BLOCKED": []
        }
        num_transitions = len(events)
        num_reopens = 0
        total_elapsed = 0.0

        for ev in events:
            h = _parse_hours(ev.get("time_in_status_hours"))
            status = ev.get("from_status", "TODO")
            if status in times_by_status:
                times_by_status[status].append(h)
            else:
                times_by_status.setdefault(status, []).append(h)

            total_elapsed += h

            # Reopen: going backwards in status order
            from_ord = _STATUS_ORDER.get(ev.get("from_status", "TODO"), 0)
            to_ord = _STATUS_ORDER.get(ev.get("to_status", "TODO"), 0)
            if to_ord < from_ord:
                num_reopens += 1

        avg_todo = np.mean(times_by_status.get("TODO", [0])) if times_by_status.get("TODO") else 0.0
        avg_prog = np.mean(times_by_status.get("IN_PROGRESS", [0])) if times_by_status.get("IN_PROGRESS") else 0.0
        avg_rev = np.mean(times_by_status.get("REVIEW", [0])) if times_by_status.get("REVIEW") else 0.0
        avg_blocked = np.mean(times_by_status.get("BLOCKED", [0])) if times_by_status.get("BLOCKED") else 0.0

        days_elapsed = max(total_elapsed / 24, 1.0)
        transition_rate = num_transitions / days_elapsed

        fraction_blocked = avg_blocked / max(total_elapsed, 1.0)

        all_phase_hours = [h for phases in times_by_status.values() for h in phases]
        max_phase = max(all_phase_hours) if all_phase_hours else 0.0

        return np.array([
            avg_todo,
            avg_prog,
            avg_rev,
            float(num_transitions),
            float(num_reopens),
            transition_rate,
            fraction_blocked,
            max_phase,
            total_elapsed,
            1.0,           # has_history = True
        ], dtype=np.float32)

    def encode_batch(self, event_lists: List[List[Dict]]) -> np.ndarray:
        """Encode a batch of task event sequences → (N, SEQ_DIM) array."""
        return np.vstack([self.encode(evs) for evs in event_lists])

    def default_features(self, n: int = 1) -> np.ndarray:
        """Return default zero features for tasks with no history."""
        return np.zeros((n, SEQ_DIM), dtype=np.float32)


def synthesize_sequence_features(n: int, rng: np.random.Generator) -> np.ndarray:
    """
    Generate n synthetic sequence feature rows for training.
    Mirrors realistic patterns from real activity logs.
    """
    features = np.zeros((n, SEQ_DIM), dtype=np.float32)
    features[:, 0] = rng.exponential(24, n)               # avg_time_todo_hours
    features[:, 1] = rng.exponential(10, n)               # avg_time_in_progress_hours
    features[:, 2] = rng.exponential(4, n)                # avg_time_review_hours
    features[:, 3] = rng.integers(0, 8, n).astype(float)  # num_transitions
    features[:, 4] = rng.integers(0, 3, n).astype(float)  # num_reopens
    features[:, 5] = rng.uniform(0.1, 2.0, n)             # transition_rate
    features[:, 6] = rng.uniform(0.0, 0.3, n)             # fraction_blocked
    features[:, 7] = rng.exponential(20, n)               # max_single_phase_hours
    features[:, 8] = features[:, 0] + features[:, 1] + features[:, 2]  # total elapsed
    features[:, 9] = rng.choice([0.0, 1.0], n, p=[0.3, 0.7])           # has_history
    return features

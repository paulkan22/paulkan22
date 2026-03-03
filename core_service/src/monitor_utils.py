from dataclasses import dataclass


@dataclass
class MonitorCandidate:
    user_id: int
    priority: int = 0


def cap_candidates(candidates: list[MonitorCandidate], max_candidates_per_group: int) -> list[MonitorCandidate]:
    if max_candidates_per_group <= 0:
        return []
    return candidates[:max_candidates_per_group]

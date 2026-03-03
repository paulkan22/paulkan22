from dataclasses import dataclass


@dataclass(frozen=True)
class FloodDecision:
    severity: str
    cooldown_seconds: int


def classify_flood(wait_seconds: int) -> FloodDecision:
    if wait_seconds < 600:
        return FloodDecision(severity='small', cooldown_seconds=max(60, wait_seconds))
    if wait_seconds < 3600:
        return FloodDecision(severity='medium', cooldown_seconds=wait_seconds)
    return FloodDecision(severity='long', cooldown_seconds=wait_seconds)

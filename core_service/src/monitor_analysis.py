from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class MessageSample:
    user_id: int
    sent_at: datetime


@dataclass(frozen=True)
class ChatterHeuristics:
    min_unique_authors: int = 15
    max_top2_share: float = 0.65
    min_time_span_minutes: int = 30


@dataclass(frozen=True)
class MonitorDecision:
    is_chatter: bool
    parse_mode: str
    reason: str


def is_chatter_group(messages: list[MessageSample], rules: ChatterHeuristics | None = None) -> bool:
    if not messages:
        return False

    cfg = rules or ChatterHeuristics()
    authors = [m.user_id for m in messages]
    unique_authors = len(set(authors))
    if unique_authors < cfg.min_unique_authors:
        return False

    counts = Counter(authors)
    top2 = sum(v for _, v in counts.most_common(2))
    top2_share = top2 / len(messages)
    if top2_share > cfg.max_top2_share:
        return False

    span = max(m.sent_at for m in messages) - min(m.sent_at for m in messages)
    if span < timedelta(minutes=cfg.min_time_span_minutes):
        return False

    return True


def choose_monitor_parse_mode(
    *,
    members_open: bool,
    messages: list[MessageSample],
    rules: ChatterHeuristics | None = None,
) -> MonitorDecision:
    if members_open:
        return MonitorDecision(True, 'members_list', 'members are open, parse full participants')

    chatter = is_chatter_group(messages, rules)
    if chatter:
        return MonitorDecision(True, 'messages_full_history', 'hidden members + chatter group')
    return MonitorDecision(False, 'messages_recent_authors', 'hidden members + low activity diversity')

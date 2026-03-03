from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from random import randint


class AccountStatus(str, Enum):
    ACTIVE = 'ACTIVE'
    COOLDOWN = 'COOLDOWN'
    SLEEP = 'SLEEP'
    ERROR = 'ERROR'


@dataclass
class AccountRuntime:
    dynamic_limit: int = 80
    trust_score: int = 0
    status: AccountStatus = AccountStatus.ACTIVE
    sleep_until: datetime | None = None


@dataclass
class DynamicLimitPolicy:
    min_limit: int = 40
    max_limit: int = 150
    jitter_min_seconds: int = 30
    jitter_max_seconds: int = 60
    cooldown_min_minutes: int = 10
    cooldown_max_minutes: int = 30

    def next_delay(self) -> int:
        return randint(self.jitter_min_seconds, self.jitter_max_seconds)

    def on_small_flood(self, runtime: AccountRuntime) -> AccountRuntime:
        runtime.dynamic_limit = max(self.min_limit, int(runtime.dynamic_limit * 0.7))
        runtime.status = AccountStatus.COOLDOWN
        runtime.sleep_until = datetime.now(timezone.utc) + timedelta(
            minutes=randint(self.cooldown_min_minutes, self.cooldown_max_minutes)
        )
        return runtime

    def on_long_flood(self, runtime: AccountRuntime, flood_wait_seconds: int) -> AccountRuntime:
        runtime.dynamic_limit = max(self.min_limit, runtime.dynamic_limit // 2)
        runtime.status = AccountStatus.SLEEP
        runtime.sleep_until = datetime.now(timezone.utc) + timedelta(seconds=flood_wait_seconds)
        return runtime

    def reward_stable_period(self, runtime: AccountRuntime) -> AccountRuntime:
        grown = int(runtime.dynamic_limit * 1.2)
        runtime.dynamic_limit = min(self.max_limit, max(self.min_limit, grown))
        runtime.trust_score += 1
        if runtime.status != AccountStatus.ERROR:
            runtime.status = AccountStatus.ACTIVE
        return runtime

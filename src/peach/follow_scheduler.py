"""APScheduler-backed automatic follow checks and their persisted preference."""
from __future__ import annotations

import json
import logging
import os
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler


LOGGER = logging.getLogger(__name__)
JOB_ID = "peach-follow-update"
MIN_INTERVAL_MINUTES = 15
MAX_INTERVAL_MINUTES = 7 * 24 * 60


def _stamp(moment: datetime | None = None) -> str:
    return (moment or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat().replace(
        "+00:00", "Z")


@dataclass(frozen=True)
class FollowScheduleConfig:
    enabled: bool = True
    interval_minutes: int = 60


class FollowScheduleStore:
    """Small replace-on-write state file; scheduling preferences are not ledger truth."""

    def __init__(self, state_root: Path):
        self.path = Path(state_root) / "follow-schedule.json"

    @staticmethod
    def validate(enabled: object, interval_minutes: object) -> FollowScheduleConfig:
        if not isinstance(enabled, bool) or isinstance(interval_minutes, bool):
            raise ValueError("enabled must be a boolean and interval_minutes an integer")
        interval = int(interval_minutes)
        if not MIN_INTERVAL_MINUTES <= interval <= MAX_INTERVAL_MINUTES:
            raise ValueError(
                f"interval_minutes must be between {MIN_INTERVAL_MINUTES} and "
                f"{MAX_INTERVAL_MINUTES}"
            )
        return FollowScheduleConfig(bool(enabled), interval)

    def load(self) -> FollowScheduleConfig:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            return self.validate(payload.get("enabled", True), payload.get("interval_minutes", 60))
        except FileNotFoundError:
            return FollowScheduleConfig()
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            LOGGER.warning("invalid follow schedule preference at %s; using defaults", self.path)
            return FollowScheduleConfig()

    def save(self, config: FollowScheduleConfig) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(f".{self.path.name}.{os.getpid()}.tmp")
        temporary.write_text(
            json.dumps(asdict(config), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        os.replace(temporary, self.path)


class FollowUpdateScheduler:
    """Own one interval job and expose its state to the settings surface."""

    def __init__(self, state_root: Path, run_check: Callable[[], dict], *, available: bool):
        self.store = FollowScheduleStore(state_root)
        self.run_check = run_check
        self.available = bool(available)
        self.config = self.store.load()
        self.scheduler = BackgroundScheduler(timezone=timezone.utc, daemon=True)
        self._started = False
        self._state_lock = threading.Lock()
        self._running = False
        self._last_started_at: str | None = None
        self._last_finished_at: str | None = None
        self._last_error: str | None = None
        self._last_checked = 0
        self._last_added = 0

    def start(self) -> None:
        if self._started or not self.available:
            return
        self.scheduler.start()
        self._started = True
        self._apply_job()

    def stop(self) -> None:
        if not self._started:
            return
        self.scheduler.shutdown(wait=False)
        self._started = False

    def update(self, *, enabled: object, interval_minutes: object) -> dict:
        if not self.available:
            raise ValueError("automatic follow updates are available only on the ledger writer")
        self.config = self.store.validate(enabled, interval_minutes)
        self.store.save(self.config)
        if self._started:
            self._apply_job()
        return self.status()

    def _apply_job(self) -> None:
        if not self.config.enabled:
            if self.scheduler.get_job(JOB_ID) is not None:
                self.scheduler.remove_job(JOB_ID)
            return
        interval = self.config.interval_minutes
        self.scheduler.add_job(
            self._run,
            "interval",
            id=JOB_ID,
            minutes=interval,
            next_run_time=datetime.now(timezone.utc) + timedelta(minutes=interval),
            replace_existing=True,
            coalesce=True,
            max_instances=1,
            misfire_grace_time=min(interval * 60, 300),
        )

    def _run(self) -> None:
        with self._state_lock:
            self._running = True
            self._last_started_at = _stamp()
            self._last_error = None
        try:
            result = self.run_check()
            if result.get("busy"):
                raise RuntimeError("another follow check is already running")
            rows = result.get("results") or []
            failures = [row for row in rows if not row.get("ok")]
            with self._state_lock:
                self._last_checked = int(result.get("checked") or 0)
                self._last_added = sum(int(row.get("added") or 0) for row in rows)
                if failures:
                    self._last_error = f"{len(failures)} 个来源检查失败"
        except Exception as error:  # the background job must never terminate the scheduler
            LOGGER.exception("automatic follow update failed")
            with self._state_lock:
                self._last_error = str(error)
        finally:
            with self._state_lock:
                self._running = False
                self._last_finished_at = _stamp()

    def status(self) -> dict:
        job = self.scheduler.get_job(JOB_ID) if self._started else None
        next_run = job.next_run_time if job is not None else None
        with self._state_lock:
            return {
                "ok": True,
                "available": self.available,
                "enabled": self.config.enabled,
                "interval_minutes": self.config.interval_minutes,
                "running": self._running,
                "next_run_at": _stamp(next_run) if next_run else None,
                "last_started_at": self._last_started_at,
                "last_finished_at": self._last_finished_at,
                "last_error": self._last_error,
                "last_checked": self._last_checked,
                "last_added": self._last_added,
            }

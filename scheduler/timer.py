import logging
import threading
from datetime import datetime, timedelta
from typing import Callable

logger = logging.getLogger(__name__)


class DailyScheduler:
    """Lập lịch chạy pipeline mỗi ngày vào các giờ cố định."""

    def __init__(self, times: list, job_fn: Callable):
        self.times = times       # ["07:00", "12:00", "18:00"]
        self.job_fn = job_fn
        self._timers: list = []
        self._lock = threading.Lock()

    def start(self):
        for t in self.times:
            self._schedule_next(t)
        logger.info(f"Scheduler đã khởi động. Lịch đăng: {', '.join(self.times)}")

    def _schedule_next(self, hhmm: str):
        delay = self._seconds_until(hhmm)
        timer = threading.Timer(delay, self._fire, args=[hhmm])
        timer.daemon = True
        timer.start()
        with self._lock:
            self._timers.append(timer)
        eta = datetime.now() + timedelta(seconds=delay)
        logger.info(f"Lần chạy tiếp theo lúc {hhmm} sau {delay / 60:.1f} phút (ETA: {eta.strftime('%H:%M:%S %d/%m')})")

    def _fire(self, hhmm: str):
        logger.info(f"=== Scheduler kích hoạt lúc {hhmm} ===")
        try:
            self.job_fn()
        except Exception as e:
            logger.error(f"Pipeline thất bại lúc {hhmm}: {e}", exc_info=True)
        finally:
            self._schedule_next(hhmm)

    def _seconds_until(self, hhmm: str) -> float:
        now = datetime.now()
        h, m = map(int, hhmm.split(":"))
        target = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        return (target - now).total_seconds()

    def stop(self):
        with self._lock:
            for t in self._timers:
                t.cancel()
            self._timers.clear()
        logger.info("Scheduler đã dừng.")

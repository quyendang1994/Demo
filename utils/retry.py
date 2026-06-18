import time
import logging
import functools

logger = logging.getLogger(__name__)


def retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(Exception,)):
    """Decorator: retry với exponential backoff khi gặp ngoại lệ được chỉ định."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    if attempt < max_attempts:
                        logger.warning(
                            f"{func.__name__} thất bại lần {attempt}/{max_attempts}: {e}. "
                            f"Thử lại sau {current_delay:.1f}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"{func.__name__} thất bại sau {max_attempts} lần: {e}")
            raise last_exc
        return wrapper
    return decorator

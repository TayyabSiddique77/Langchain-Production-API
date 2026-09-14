import logging
import json
import time
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable


class JSONFormatter(logging.Formatter):

    def format(self, record):
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }

        # Merge any extra data attached to the record
        if hasattr(record, "extra_data"):
            log_obj.update(record.extra_data)

        return json.dumps(log_obj)


def get_logger(name: str = "production-api") -> logging.Logger:
    """Create a structured JSON logger"""

    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger


# ====Metrics Collector====


class MetricsCollector:
    """
    Collects and aggregate application metrics.

    In production, replace with Prometheus client:
     from prometheus_client import Counter, Histogram
    """

    def __init__(self):
        self._requests_total = 0
        self._errors_total = 0
        self._latency_sum = 0
        self._latency_count = 0
        self._tokens_input = 0
        self._tokens_output = 0
        self._cache_hits = 0
        self._cache_misses = 0

    def record_request(
        self,
        latency_ms: float,
        input_tokens: int = 0,
        output_tokens: int = 0,
        error: bool = False,
        cache_hit: bool = False,
    ):
        """Record metrics for a single request."""

        self._requests_total += 1

        if error:
            self._errors_total += 1

        self._latency_sum += latency_ms
        self._latency_count += 1

        self._tokens_input += input_tokens
        self._tokens_output += output_tokens

        if cache_hit:
            self._cache_hits += 1
        else:
            self._cache_misses += 1

    def get_metrics(self) -> dict[str, Any]:
        """Return current application metrics."""

        average_latency = (
            self._latency_sum / self._latency_count
            if self._latency_count > 0
            else 0
        )

        error_rate = (
            self._errors_total / self._requests_total
            if self._requests_total > 0
            else 0
        )

        total_cache_requests = self._cache_hits + self._cache_misses

        cache_hit_rate = (
            self._cache_hits / total_cache_requests
            if total_cache_requests > 0
            else 0
        )

        return {
            "requests_total": self._requests_total,
            "errors_total": self._errors_total,
            "error_rate": error_rate,
            "average_latency_ms": average_latency,
            "tokens_input": self._tokens_input,
            "tokens_output": self._tokens_output,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "cache_hit_rate": cache_hit_rate,
        }

    @property
    def summary(self) -> dict[str, Any]:
        """Return a summary of all collected application metrics."""

        return self.get_metrics()


# ====Request Timer====


class RequestTimer:
    """Measures the execution time of a request."""

    def __init__(self):
        self.start_time = None
        self.elapsed_ms = 0.0

    def start(self):
        """Start the timer."""
        self.start_time = time.perf_counter()

    def stop(self) -> float:
        """Stop the timer and return elapsed time in milliseconds."""

        if self.start_time is None:
            raise RuntimeError("Timer was not started.")

        elapsed_seconds = time.perf_counter() - self.start_time

        return elapsed_seconds * 1000

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            self.elapsed_ms = self.stop()
        return False


# ====Global Monitoring Objects====

logger = get_logger()
metrics = MetricsCollector()


# ====Monitoring Decorator====


def monitor(func: Callable) -> Callable:
    """
    Monitor function execution.

    Measures latency, logs request information,
    records errors, and updates application metrics.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):

        timer = RequestTimer()
        timer.start()

        error = False

        try:
            result = func(*args, **kwargs)
            return result

        except Exception:
            error = True
            raise

        finally:
            latency_ms = timer.stop()

            metrics.record_request(
                latency_ms=latency_ms,
                error=error
            )

            logger.info(
                f"Request completed: {func.__name__}",
                extra={
                    "extra_data": {
                        "latency_ms": round(latency_ms, 2),
                        "error": error,
                        "function": func.__name__,
                    }
                },
            )

    return wrapper

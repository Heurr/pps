import logging
import time
from timeit import default_timer

import prometheus_client
from prometheus_client import Counter, Gauge, Histogram
from prometheus_client.context_managers import Timer
from prometheus_client.utils import INF

from app.config.log import log_setting
from app.config.settings import base_settings

logger = logging.getLogger(__name__)


ENTITY_METRICS = Counter(
    "entity_metrics",
    "Total number of entities by given type, phase and status",
    ["entity", "phase", "operation"],
)


UPDATE_METRICS = Counter(
    "update_metrics", "Number of updated entities", ["update_type", "entity"]
)

JOB_METRICS = Counter(
    "job_processed",
    "Total number of entities processed by the job",
    ["name", "stage"],
)


JOB_TIMER = Gauge(
    "job_timer",
    "Time taken to process one entity in the job",
    ["name"],
)

API_METRICS = Histogram(
    "api_metrics",
    "API call latency stats",
    ["scope", "route"],
    buckets=[
        0.001,
        0.002,
        0.005,
        0.01,
        0.02,
        0.05,
        0.1,
        0.2,
        0.5,
        1,
        1.5,
        2,
        5,
        10,
        INF,
    ],
)

DB_CONNECTIONS = Gauge(
    "db_connections",
    "Number of open db connections",
    ["state"],
)

UNPOPULATED_ENTITIES = Counter(
    "unpopulated_entities",
    "Number of unpopulated entities requested for population",
    ["entity"],
)


class PerformanceTimer:
    def __init__(self, metric: Gauge):
        self.metric = metric

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, exc_type, exc_val, exc_tb):
        tm = time.time() - self.start
        self.metric.set(tm)


class LoggingTimer(Timer):
    def __init__(self, metric: Histogram, request):
        super().__init__(metric, "observe")
        self.request = request

    def __enter__(self):
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Implementation take from prometheus_client library, if condition is new
        duration = max(default_timer() - self._start, 0)
        if duration > log_setting.TOO_LONG_REQUEST_DURATION:
            logger.warning(
                "API request with labels %s taking too long (%.2f ms) with request: %s",
                self._metric._labelvalues,
                duration * 1000,
                self.request,
            )
        callback = getattr(self._metric, self._callback_name)
        callback(duration)


# FIXME: Use middleware
def start_prometheus_server():
    try:
        prometheus_client.start_http_server(base_settings.PROMETHEUS_PORT)
        logging.info(
            "Prometheus metrics server started at %s", base_settings.PROMETHEUS_PORT
        )
    except OSError as e:
        # Silently exit if the port is already in use
        # (the prometheus server is already running)
        if e.errno != 98:  # noqa
            raise e


start_prometheus_server()

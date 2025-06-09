from prometheus_client import Counter, Gauge, start_http_server
import time

from prometheus_client import Counter, Gauge, start_http_server
import time
class Metrics:
    NAMESPACE = "connector_stream_htx"

    MESSAGES_PROCESSED = Counter(
        '_messages_processed',
        'Total number of messages processed',
        ['topic'],
        NAMESPACE
    )

    TIME_LAG_SECONDS = Gauge(
        'time_lag_ms',
        'Lag between message timestamp and current time',
        ['topic']
    )


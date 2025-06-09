from prometheus_client import Counter, Gauge, start_http_server
import time

from prometheus_client import Counter, Gauge, start_http_server
import time
class Metrics:
    namespace = "connector_stream_htx"

    message_processed = Counter(
        '_messages_processed',
        'Total number of messages processed',
        ['topic'],
        namespace
    )

    time_lag_sec = Gauge(
        'time_lag_sec',
        'Lag between message timestamp and current time',
        ['topic']
    )


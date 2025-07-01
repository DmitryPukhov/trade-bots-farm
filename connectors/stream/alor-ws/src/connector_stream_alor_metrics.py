from prometheus_client import Counter, Gauge

from metrics_base import MetricsBase


class ConnectorStreamAlorMetrics(MetricsBase):

    namespace = "connector_stream_alor"

    messages_in_queue = Gauge(
        '_messages_in_queue',
        'Total number of messages in asyncio message queue',
        ['websocket'],
        namespace=namespace,
        registry=MetricsBase._registry

    )
    message_processed = Counter(
        '_messages_processed',
        'Total number of messages processed',
        ['topic'],
        namespace=namespace,
        registry=MetricsBase._registry

    )

    time_lag_sec = Gauge(
        '_time_lag_sec',
        'Lag between message timestamp and current time',
        ['topic'],
        namespace=namespace,
        registry=MetricsBase._registry
    )

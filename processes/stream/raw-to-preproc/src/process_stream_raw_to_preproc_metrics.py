from prometheus_client import Counter, Gauge

from metrics_base import MetricsBase


class ProcessStreamRawToPreprocMetrics(MetricsBase):
    namespace = "process_stream_raw_to_preproc"
    messages_input = Counter(
        '_messages_input',
        'Total number of input raw messages',
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
    messages_output = Counter(
        '_messages_output',
        'Total number of output preprocessed messages',
        ['topic'],
        namespace=namespace,
        registry=MetricsBase._registry
    )

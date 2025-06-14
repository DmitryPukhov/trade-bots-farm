from prometheus_client import Counter, Gauge

from metrics_base import MetricsBase


class FeaturesMetrics(MetricsBase):
    namespace = "process_stream_features"
    # Kafka and s3 input messages
    # Kakfa and s3 input time lag
    input_kafka_messages = Counter(
        '_kafka_input_messages',
        'Total number of input Kafka messages',
        ['topic'],
        namespace=namespace,
        registry=MetricsBase._registry
    )

    input_s3_rows = Counter(
        '_input_s3_rows',
        'Rows in s3 input dataset',
        ['s3_dir'],
        namespace=namespace,
        registry=MetricsBase._registry
    )

    input_s3_rows_good = Counter(
        '_input_s3_rows_good',
        'Rows in s3 input dataset',
        ['feature'],
        namespace=namespace,
        registry=MetricsBase._registry
    )
    input_s3_rows_not_merged = Counter(
        '_input_s3_rows_not_merged',
        'Rows in s3 input dataset not merged due to na after merge level2 and candles',
        ['feature'],
        namespace=namespace,
        registry=MetricsBase._registry
    )

    input_s3_time_lag_sec = Gauge(
        '_input_s3_time_lag_sec',
        'Lag between last s3 data and current time',
        ['s3_dir'],
        namespace=namespace,
        registry=MetricsBase._registry
    )

    feature_time_lag_sec = Gauge(
        '_feature_time_lag_sec',
        'Lag between feature timestamp and current time',
        ['topic'],
        namespace=namespace,
        registry=MetricsBase._registry
    )
    output_messages = Counter(
        '_feature_output_messages',
        'Total number of output features',
        ['topic'],
        namespace=namespace,
        registry=MetricsBase._registry
    )

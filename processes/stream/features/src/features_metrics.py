from prometheus_client import Counter, Gauge

from metrics_base import MetricsBase


class FeaturesMetrics(MetricsBase):
    namespace = "process_stream_features"
    # Kafka and s3 input messages
    input_rows = Counter(
        '_input_rows',
        'Total number of candles + level2 input rows come to feature calculator',
        ['topic'],
        namespace=namespace,
        registry=MetricsBase._registry
    )

    produced_kafka_messages = Counter(
        '_kafka_produced_messages',
        'Total number of features sent to Kafka',
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

    features_time_lag_sec = Gauge(
        '_features_time_lag_sec',
        'Lag between feature timestamp and current time',
        ['topic'],
        namespace=namespace,
        registry=MetricsBase._registry
    )

    features_calc_duration_sec = Gauge(
        '_features_calc_duration_sec',
        'How long it took to calculate features',
        ['topic'],
        namespace=namespace,
        registry=MetricsBase._registry
    )
    features_dirty_rows = Counter(
        '_features_dirty_rows',
        'Calculated but not cleaned',
        ['topic'],
        namespace=namespace,
        registry=MetricsBase._registry
    )
    features_cleaned_rows = Counter(
        '_features_cleaned_rows',
        'Cleaned but can contain already processed features',
        ['topic'],
        namespace=namespace,
        registry=MetricsBase._registry
    )
    features_new_rows = Counter(
        '_features_new_rows',
        'Cleaned new features',
        ['topic'],
        namespace=namespace,
        registry=MetricsBase._registry
    )

    features_output_rows = Counter(
        '_features_output_rows',
        'Total number of output features',
        ['topic'],
        namespace=namespace,
        registry=MetricsBase._registry
    )
    features_last_datetime = Gauge(
        '_features_last_datetime',
        'Last datetime of features',
        ['topic'],
        namespace=namespace,
        registry=MetricsBase._registry
    ),
    features_previous_datetime = Gauge(
        '_features_previoous_datetime',
        'Last datetime of previous feature batch',
        ['topic'],
        namespace=namespace,
        registry=MetricsBase._registry
    )

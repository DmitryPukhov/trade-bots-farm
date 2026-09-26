from prometheus_client import Counter

from metrics_base import MetricsBase


class ConnectorBatchS3ExternalMetrics(MetricsBase):
    namespace = "connector_batch_s3_external"

    files_transferred = Counter(
        '_files_transferred',
        'Total number of files downloaded',
        ['external_s3_dir'],
        namespace = namespace,
        registry = MetricsBase._registry
    )


    job_runs = Counter(
        '_job_runs',
        'Total runs of this job',
        namespace = namespace,
        registry = MetricsBase._registry
    )

from prometheus_client import Counter

from metrics_base import MetricsBase


class ProcessBatchRawToPreprocMetrics(MetricsBase):
    namespace = "process_batch_raw_to_preproc"

    files_transferred = Counter(
        '_files_transferred',
        'Total number of files downloaded',
        ['preproc_s3_dir'],
        namespace = namespace,
        registry = MetricsBase._registry
    )
    rows = Counter(
        '_rows',
        'Total rows in input datasets',
        ['s3_dir'],
        namespace = namespace,
        registry = MetricsBase._registry
    )



    job_runs = Counter(
        '_job_runs',
        'Total runs of this job',
        namespace = namespace,
        registry = MetricsBase._registry
    )

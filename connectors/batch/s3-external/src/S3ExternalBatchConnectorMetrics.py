from prometheus_client import Counter, Gauge, start_http_server
import time

from prometheus_client import Counter, Gauge, start_http_server
import time
class S3ExternalBatchConnectorMetrics:
    namespace = "connector_batch_s3_external"

    files_transferred = Counter(
        '_files_transferred',
        'Total number of files downloaded',
        ['external_s3_dir'],
        namespace = namespace
    )



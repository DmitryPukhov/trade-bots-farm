import logging
import os
import time

from prometheus_client import CollectorRegistry, push_to_gateway

from prometheus_client import Counter, Gauge


class Metrics:

    gateway = os.getenv('PUSHGATEWAY_URL', 'http://localhost:9091')

    namespace = "connector_stream_htx"
    registry = CollectorRegistry()
    message_processed = Counter(
        '_messages_processed',
        'Total number of messages processed',
        ['topic'],
        namespace = namespace,
        registry=registry

    )

    time_lag_sec = Gauge(
        '_time_lag_sec',
        'Lag between message timestamp and current time',
        ['topic'],
        namespace = namespace,
        registry = registry
    )


    @classmethod
    def push_to_gateway_periodical(cls):
        while True:
            try:
                print("push_to_gateway_periodical")
                cls.registry.collect()
                push_to_gateway(cls.gateway, job='trade_bots_farm', registry=cls.registry)
            except Exception as e:
                logging.error('Error while pushing metrics to gateway: {}'.format(e))
            time.sleep(10)




import asyncio
import logging
import os

from prometheus_client import CollectorRegistry, push_to_gateway
from prometheus_client import Counter, Gauge


class Metrics:
    gateway = os.getenv('PROMETHEUS_PUSHGATEWAY_URL', 'http://localhost:9091')
    _push_to_gateway_interval_sec = float(os.environ.get('METRICS_PUSH_TO_GATEWAY_INTERVAL_SEC') or 10)

    namespace = "connector_stream_htx"
    _registry = CollectorRegistry()
    message_processed = Counter(
        '_messages_processed',
        'Total number of messages processed',
        ['topic'],
        namespace=namespace,
        registry=_registry

    )

    time_lag_sec = Gauge(
        '_time_lag_sec',
        'Lag between message timestamp and current time',
        ['topic'],
        namespace=namespace,
        registry=_registry
    )

    @classmethod
    async def push_to_gateway_periodical(cls):
        while True:
            try:
                logging.debug(f"Pushing metrics to gateway {cls.gateway}")
                cls._registry.collect()
                push_to_gateway(cls.gateway, job='trade_bots_farm', registry=cls._registry)
            except Exception as e:
                logging.error(f"Error while pushing metrics to {cls.gateway}: {e}")
            await asyncio.sleep(cls._push_to_gateway_interval_sec)

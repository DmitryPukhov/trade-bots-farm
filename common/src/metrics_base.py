import asyncio
import logging
import os

from prometheus_client import CollectorRegistry, push_to_gateway


class MetricsBase:
    """
    Metrics base class. Provides a method to push metrics to a Prometheus pushgateway.
    """

    gateway = os.getenv('PROMETHEUS_PUSHGATEWAY_URL', 'http://localhost:9091')
    _push_to_gateway_interval_sec = float(os.environ.get('METRICS_PUSH_TO_GATEWAY_INTERVAL_SEC') or 5)
    _registry = CollectorRegistry()
    run_flag = True

    @classmethod
    async def push_to_gateway_(cls):
        try:
            if logging.getLogger().isEnabledFor(logging.DEBUG):
                collected_metrics = cls._registry.collect()
                logging.debug(f"Pushing {len(list(collected_metrics))} metrics to gateway {cls.gateway}")
            push_to_gateway(cls.gateway, job='trade_bots_farm', registry=cls._registry)
        except Exception as e:
            logging.error(f"Error while pushing metrics to {cls.gateway}: {e}")

    @classmethod
    async def push_to_gateway_periodical(cls):
        try:
            while cls.run_flag:
                # Push metrics to the Prometheus pushgateway.
                await cls.push_to_gateway_()

                # Delay before the next push.
                await asyncio.sleep(cls._push_to_gateway_interval_sec)
        except asyncio.CancelledError:
            # When cancelled, we want to push one last time.
            logging.info("Pushing metrics to gateway before exiting.")
            await cls.push_to_gateway_()
            logging.info("Metrics pusher stopped.")

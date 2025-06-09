import logging
import os

from prometheus_client import start_http_server

from common_tools import CommonTools
from htx_websocket_client import HtxWebSocketClient
from kafka_raw_producer import KafkaRawProducer


class ConnectorStreamHtxApp:
    """ Main class"""

    def __init__(self):

        CommonTools.init_logging()
        # Create websocket client, don't run just now
        self.__websocket_client_market = self.create_websocket_client()
        self._metrics_port = os.getenv('METRICS_PORT', 8000)

    def create_websocket_client(self):
        # Get key, secret
        htx_access_key = os.environ.get('HTX_ACCESS_KEY')
        htx_secret_key = os.environ.get('HTX_SECRET_KEY')
        if not htx_access_key or not htx_secret_key:
            raise Exception("HTX_ACCESS_KEY or HTX_SECRET_KEY not set")

        # Get topics to listen
        topics = [topic.strip() for topic in os.environ['HTX_TOPICS'].split(',')]
        if not topics:
            raise Exception("HTX_TOPICS not set")
        logging.info("HTX_TOPICS: %s", topics)

        # Get connection requisites
        htx_host = os.environ.get('HTX_HOST') or 'api.hbdm.com'
        htx_path = os.environ.get('HTX_PATH') or '/linear-swap-ws'

        kafka_raw_producer = KafkaRawProducer()

        # Create websocket client, don't run just now
        return HtxWebSocketClient(topics=topics,
                                                            host=htx_host,
                                                            path=htx_path,
                                                            access_key=htx_access_key,
                                                            secret_key=htx_secret_key,
                                                            be_spot=False,
                                                            is_broker=False,
                                                            receiver=kafka_raw_producer)


    def run(self):
        # Start Prometheus HTTP server for metrics (runs on port 8000 by default)
        start_http_server(self._metrics_port)

        kafka_raw_producer = KafkaRawProducer()
        websocket_client = HtxWebSocketClient(receiver=kafka_raw_producer)
        websocket_client.open()


if __name__ == '__main__':
    ConnectorStreamHtxApp().run()

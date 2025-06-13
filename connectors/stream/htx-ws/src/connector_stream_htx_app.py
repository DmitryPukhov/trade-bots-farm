import asyncio
import logging
import os

from common_tools import CommonTools
from htx_web_socket_client import HtxWebSocketClient
from kafka_raw_producer import KafkaRawProducer
from connector_stream_htx_metrics import ConnectorStreamHtxMetrics


class ConnectorStreamHtxApp:
    """ Main class"""

    def __init__(self):

        CommonTools.init_logging()

        # Get connection requisites
        self.htx_access_key = os.environ.get('HTX_ACCESS_KEY')
        self.htx_secret_key = os.environ.get('HTX_SECRET_KEY')
        self.htx_host = os.environ.get('HTX_HOST') or 'api.hbdm.com'
        self.htx_path = os.environ.get('HTX_PATH') or '/linear-swap-ws'
        if not self.htx_access_key or not self.htx_secret_key:
            raise Exception("HTX_ACCESS_KEY or HTX_SECRET_KEY not set")

        # Get topics to listen
        self.topics = [topic.strip() for topic in os.environ['HTX_TOPICS'].split(',')]
        if not self.topics:
            raise Exception("HTX_TOPICS not set")
        logging.info("HTX_TOPICS: %s", self.topics)

    async def run_async(self):
        """ Listen to HTX messages, produce them to Kafka"""

        # Set up the Kafka producer and the HTX client to run together
        kafka_raw_producer = KafkaRawProducer()
        client = HtxWebSocketClient(topics=self.topics,
                                    host=self.htx_host,
                                    path=self.htx_path,
                                    access_key=self.htx_access_key,
                                    secret_key=self.htx_secret_key,
                                    be_spot=False,
                                    is_broker=False,
                                    receiver=kafka_raw_producer)

        # Connect to HTX and listen to the messages
        try:
            await asyncio.gather(client.connect(),  # web socket event loop
                                 ConnectorStreamHtxMetrics().push_to_gateway_periodical()  # push metrics to gateway periodically
                                 )

        except asyncio.CancelledError:
            await client.close()

    def run(self):
        asyncio.run(self.run_async())


if __name__ == '__main__':
    ConnectorStreamHtxApp().run()

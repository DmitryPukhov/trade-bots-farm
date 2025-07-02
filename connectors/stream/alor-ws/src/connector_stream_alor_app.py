import asyncio
import os

from alor_ws_client import AlorWsClient
from common_tools import CommonTools
from alor_kafka_raw_producer import AlorKafkaRawProducer
from connector_stream_alor_metrics import ConnectorStreamAlorMetrics


class ConnectorStreamAlorApp:
    """ Main class"""

    def __init__(self):

        CommonTools.init_logging()
        self.tickets = os.environ.get('ALOR_TICKET').replace(" ", "").split(",")
        if not self.tickets:
            raise Exception("topics not set")

    async def run_async(self):
        """ Listen to exchange messages, produce them to Kafka"""

        # Queues to transfer data between web socket event loop and Kafka producer
        candles_1min_queue = asyncio.Queue()
        level2_queue = asyncio.Queue()
        bid_ask_queue = asyncio.Queue()

        client = AlorWsClient(candles_1min_queue = candles_1min_queue, level2_queue = level2_queue, bid_ask_queue = bid_ask_queue)

        # Kafka producer listens queues from alor web socket in background
        kafka_raw_producer = AlorKafkaRawProducer(candles_1min_queue = candles_1min_queue, level2_queue = level2_queue, bid_ask_queue = bid_ask_queue)
        await kafka_raw_producer.create_tasks()

        # Connect to exchange and listen to the messages
        try:
            await asyncio.gather(client.run_async(),  # web socket event loop
                                 ConnectorStreamAlorMetrics().push_to_gateway_periodical()  # push metrics to gateway periodically
                                 )

        except asyncio.CancelledError:
            await client.close()

    def run(self):
        asyncio.run(self.run_async())


if __name__ == '__main__':
    ConnectorStreamAlorApp().run()

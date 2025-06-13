import asyncio
import json
import logging
import os

from confluent_kafka import Producer, Consumer, KafkaException

from candles_preproc import CandlesPreproc
from common_tools import CommonTools
from level2_preproc import Level2Preproc
from process_stream_raw_to_preproc_metrics import ProcessStreamRawToPreprocMetrics

class ProcessStreamRawToPreprocApp:
    """ Main class"""

    def __init__(self):
        """ Configure producer and consumer """
        CommonTools.init_logging()

        self._src_topic = os.environ["KAFKA_TOPIC_SRC"]
        self._dest_topic = os.environ["KAFKA_TOPIC_DST"]
        self.kind = os.environ["KIND"]
        logging.info(
            f"{self.__class__.__name__} for {self.kind}, RAW_KIND={self.kind}Source topic: {self._src_topic}, Destination topic: {self._dest_topic}")

        # Create Kafka producer and consumer
        kafka_producer_conf, kafka_consumer_conf = self._create_kafka_configs(self.kind)
        self._producer = Producer(kafka_producer_conf)
        self._consumer = Consumer(kafka_consumer_conf)

        self._preprocessor = self.create_preprocessor(self.kind)

    def create_preprocessor(self, kind: str):
        """ Return preprocessor instance for specified kind of data"""
        match kind:
            case "level2":
                return Level2Preproc()
            case "candles":
                return CandlesPreproc()
            case _:
                return None

    def _create_kafka_configs(self, kind: str) -> (dict, dict):
        """ Create kafka producer and consumer configuration"""
        kafka_offset = os.environ.get("KAFKA_OFFSET", "latest")
        kafka_base_conf = {
            "bootstrap.servers": os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        }
        kafka_producer_conf = {**kafka_base_conf, **{
            "queue.buffering.max.ms": int(os.environ.get("KAFKA_AUTO_FLUSH_SEC", "1")) * 1000,
            # Auto-flush every 1000ms (1 second)
            "batch.num.messages": 100,  # OR: Flush after 100 messages
        }}
        group_id = f"{kind}_{self.__class__.__name__}"
        kafka_consumer_conf = {**kafka_base_conf, **{
            "group.id": group_id,
            "auto.offset.reset": kafka_offset,
            'enable.auto.commit': True
        }}
        logging.info(f"Kafka producer conf: {kafka_producer_conf}\nKafka consumer conf: {kafka_consumer_conf}")
        return kafka_producer_conf, kafka_consumer_conf

    async def process_loop(self):

        logging.info(
            f"Starting {self.__class__.__name__}, listen to {self._src_topic}, transform, produce to {self._dest_topic}")

        # Subscribe to Kafka topic
        self._consumer.subscribe([self._src_topic])

        # pull, process, push loop
        while True:

            # Get raw message from Kafka
            preproc_msg = self._consumer.poll(1)  # Seconds
            if preproc_msg is None:
                continue
            if preproc_msg.error():
                raise KafkaException(preproc_msg.error())
            ProcessStreamRawToPreprocMetrics.messages_input.labels(topic = self._src_topic).inc() # metrics

            # logging.debug(f"Received data from topic {self._src_topic}, message: {preproc_msg.value()}")
            # Accumulate and maybe generate preproc messages
            preproc_msgs = await self._preprocessor.process(preproc_msg.value().decode('utf-8'))
            preproc_msgs = await asyncio.gather(*preproc_msgs)

            # Normally 1 message in the list
            for preproc_msg in preproc_msgs:
                logging.info(f"Producing data to topic {self._dest_topic}, message: {preproc_msg}")
                self._producer.produce(self._dest_topic, json.dumps(preproc_msg))
                self._producer.flush()
                ProcessStreamRawToPreprocMetrics.messages_output.labels(topic = self._dest_topic).inc() # metrics

    async def run_async(self):
        await asyncio.gather(await self.process_loop(), await ProcessStreamRawToPreprocMetrics.push_to_gateway_periodical())

    def run(self):
        asyncio.run(self.run_async())


if __name__ == '__main__':
    ProcessStreamRawToPreprocApp().run()

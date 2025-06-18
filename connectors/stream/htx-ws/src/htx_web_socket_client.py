import asyncio
import base64
import gzip
import hmac
import json
import logging
import os
from collections import defaultdict
from datetime import timedelta, datetime
from hashlib import sha256
from typing import Optional
from urllib import parse

from websockets import connect, exceptions, ClientConnection

from connector_stream_htx_metrics import ConnectorStreamHtxMetrics


class HtxWebSocketClient:
    def __init__(self,
                 receiver,
                 topics: list[str] = os.environ.get("HTX_TOPICS"),
                 host: str = os.environ.get("HTX_WEBSOCKET_HOST", "api.hbdm.com"),
                 path: str = os.environ.get('HTX_PATH', '/linear-swap-ws'),
                 access_key: str = os.environ.get("HTX_ACCESS_KEY"),
                 secret_key: str = os.environ.get("HTX_SECRET_KEY"),
                 is_broker: bool = False,
                 be_spot: bool = False):
        self._host = host
        self._path = path
        self.url = 'wss://{}{}'.format(self._host, self._path)
        self._access_key = access_key
        self._secret_key = secret_key
        self._is_broker = is_broker
        self._be_spot = be_spot
        self._topics = [topic.strip() for topic in os.environ['HTX_TOPICS'].split(',')]
        self._running = False

        self._consumers = defaultdict(set)
        self.is_running = False
        self.watchdog_thread = None
        self.heartbeat_timeout = timedelta(seconds=60)
        self._reconnect_delay = self.heartbeat_timeout
        self.last_heartbeat = datetime.utcnow()  # record last heartbeat time
        self.receiver = receiver
        self._websocket:Optional[ClientConnection] = None
        self.msg_queue = asyncio.Queue()
        logging.info(f"Initialized, key: ***{access_key[-3:]}, secret: ***{secret_key[-3:]}")

    async def process_msg_queue_loop(self):
        """ Process messages from the queue"""

        while self._running:
            try:
                message = await self.msg_queue.get()
                await self._on_message(message)
                await asyncio.sleep(0.001)
            except Exception as e:
                logging.error(f"Error processing messages: {e}")
                # Close the web socket and it will be reconnected
                await self._websocket.close()
                await asyncio.sleep(0.001)


    async def read_messages_loop(self):
        """ Read messages from websocket, put to the queue """
        while self._running:
            try:
                logging.info(f"Connecting to {self.url}...")
                async with connect(self.url, max_queue=64) as websocket:
                    self._websocket = websocket
                    self._reconnect_delay = self.heartbeat_timeout  # Reset delay after successful connection
                    await self._on_open()
                    try:
                        async for message in websocket:
                            await self.msg_queue.put(message)
                            await asyncio.sleep(0)
                            ConnectorStreamHtxMetrics.messages_in_queue.labels(websocket=self.url).set(self.msg_queue.qsize())

                    except exceptions.ConnectionClosed as e:
                        await self._on_close(e.code, e.reason)
                        raise e  # Reraise the exception for reconnection
            except Exception as e:
                # Delay before reconnect
                await self._on_error(e)
                await asyncio.sleep(0)
                await self._handle_reconnect()

    async def run_async(self):
        self._running = True
        # Message processing loop
        await asyncio.gather(self.process_msg_queue_loop(), self.read_messages_loop())

    async def _handle_reconnect(self):
        if not self._running:
            return

        logging.info(f"Reconnecting in {self._reconnect_delay} seconds...")
        await asyncio.sleep(self._reconnect_delay.total_seconds())

        # Exponential backoff with max limit
        self._reconnect_delay = min(self.heartbeat_timeout * 2, self.heartbeat_timeout)

    async def close(self):
        self._running = False
        if self._websocket:
            await self._websocket.close()

    async def _on_open(self):
        logging.info(f"Socket opened: {self.url}")
        if self._is_broker:
            # Some endpoints requires this signature data, others just returns invalid command error and continue to work.
            signature_data = self._get_signature_data()  # signature data
            await self._safe_send(json.dumps(signature_data))  # as json string to be send
            await asyncio.sleep(0)
        await self.subscribe_events()

    async def subscribe_events(self):
        """Subscribe to topics """
        for topic in self._topics:
            params = json.dumps({"sub": topic})
            logging.info(f"Subscribing to socket data, params: {params}")
            await self._safe_send(params)  # as json string to be send
            await asyncio.sleep(0)

    async def _get_signature_data(self) -> dict:
        # it's utc time and an example is 2017-05-11T15:19:30
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
        url_timestamp = parse.quote(timestamp)  # url encode

        # get Signature
        if self._be_spot:
            suffix = 'accessKey={}&signatureMethod=HmacSHA256&signatureVersion=2.1&timestamp={}'.format(
                self._access_key, url_timestamp)
        else:
            suffix = 'AccessKeyId={}&SignatureMethod=HmacSHA256&SignatureVersion=2&Timestamp={}'.format(
                self._access_key, url_timestamp)
        payload = '{}\n{}\n{}\n{}'.format('GET', self._host, self._path, suffix)

        digest = hmac.new(self._secret_key.encode('utf8'), payload.encode(
            'utf8'), digestmod=sha256).digest()  # make sha256 with binary data
        # base64 encode with binary data and then get string
        signature = base64.b64encode(digest).decode()

        # data
        if self._be_spot:
            data = {
                "action": "req",
                "ch": "auth",
                "params": {
                    "authType": "api",
                    "accessKey": self._access_key,
                    "signatureMethod": "HmacSHA256",
                    "signatureVersion": "2.1",
                    "timestamp": timestamp,
                    "signature": signature
                }
            }
        else:
            data = {
                "op": "auth",
                "type": "api",
                "AccessKeyId": self._access_key,
                "SignatureMethod": "HmacSHA256",
                "SignatureVersion": "2",
                "Timestamp": timestamp,
                "Signature": signature
            }
        return data

    async def _safe_send(self, message):
        delay = 0.1
        try:
            await self._websocket.send(message)
        except asyncio.QueueFull:
            # Wait a bit and retry
            logging.warning(f"Message queue is full, waiting {delay} seconds before next retry")
            await asyncio.sleep(delay)
            delay *= 2
            await self._websocket.send(message)
            await asyncio.sleep(0)

    async def _on_message(self, message):
        self.last_heartbeat = datetime.utcnow()
        try:
            plain = message
            if not self._be_spot:
                plain = gzip.decompress(message).decode()

            jdata = json.loads(plain)
            if 'ping' in jdata:
                sdata = plain.replace('ping', 'pong')
                await self._safe_send(sdata)
                return
            elif 'op' in jdata:
                # Order and accounts notifications like {op: "notify", topic: "orders_cross@btc-usdt", data: []}
                opdata = jdata['op']
                if opdata == 'notify' and 'topic' in jdata:
                    # Pass the event to subscribers: broker, account, feed
                    topic = jdata['topic'].lower()
                    for params, consumer in [(params, consumer) for (params, consumer) in self._consumers[topic]
                                             if hasattr(consumer, 'on_socket_data')]:
                        consumer.on_socket_data(topic, jdata)
                elif opdata == 'ping':
                    sdata = plain.replace('ping', 'pong')
                    await self._safe_send(sdata)
                else:
                    pass
            elif 'action' in jdata:
                opdata = jdata['action']
                if opdata == 'ping':
                    sdata = plain.replace('ping', 'pong')
                    await self._safe_send(sdata)
                    return
                else:
                    pass
            elif 'ch' in jdata:
                # Pass the event to receiver
                topic = jdata['ch'].lower()
                await self.receiver.on_message(topic, jdata)
            elif jdata.get('status') == 'error':
                logging.error(f"Got message with error: {jdata}")
        except Exception as e:
            logging.error(e)
            # Raise the exception again for reconnection
            raise e

    async def _on_close(self, code, reason):
        logging.info(f"WebSocket connection closed: code={code}, reason={reason}")
        # Your close handler logic here

    async def _on_error(self, error):
        logging.error(f"WebSocket error: {error}")
        # Your error handler logic here

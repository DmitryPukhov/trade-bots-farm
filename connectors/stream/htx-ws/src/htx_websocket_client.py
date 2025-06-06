import base64
import gzip
import hmac
import json
import logging
import os
import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta
from hashlib import sha256
from typing import Callable
from urllib import parse

from websocket import WebSocketApp


class HtxWebSocketClient:
    """
    WebSocket Subscription Address
    Market Data Request and Subscription: wss://api.hbdm.com/swap-ws

    Order Push Subscription: wss://api.hbdm.com/swap-notification

    Index Kline Data and Basis Data Subscription: wss://api.hbdm.com/ws_index

    System status updates subscription ：wss://api.hbdm.com/center-notification

    If the url: api.hbdm.com can't be accessed, please use the url below:

    Market Data Request and Subscription Address: wss://api.btcgateway.pro/swap-ws;

    Order Push Subscription：wss://api.btcgateway.pro/swap-notification

    Index Kline Data and Basis Data Subscription: wss://api.btcgateway.pro/ws_index

    System status updates subscription ：wss://api.btcgateway.pro/center-notification
    """

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

        self._ws = None
        self._consumers = defaultdict(set)
        self.is_running = False
        self.watchdog_thread = None
        self.heartbeat_timeout = timedelta(seconds=60)
        self.last_heartbeat = datetime.utcnow()  # record last heartbeat time
        self.receiver = receiver
        logging.info(f"Initialized, key: ***{access_key[-3:]}, secret: ***{secret_key[-3:]}")

    def __del__(self):
        self.close()

    def __enter__(self):
        # self.open()
        return self

    def __exit__(self, *args):
        self.close()

    def open(self):
        logging.info(f"Opening socket: {self.url}")
        self._ws = WebSocketApp(self.url,
                                on_open=self._on_open,
                                on_message=self._on_msg,
                                on_close=self._on_close,
                                on_error=self._on_error)
        self.is_running = True
        self.last_heartbeat = datetime.utcnow()  # record last heartbeat time

        # Start new watchdog thread once
        if not self.watchdog_thread:
            self.watchdog_thread = threading.Thread(
                target=self._watchdog,
                daemon=True
            )
            self.watchdog_thread.start()

        self._ws.run_forever()

    def _on_open(self, ws):
        logging.info(f"Socket opened: {self.url}")
        if self._is_broker:
            # Some endpoints requires this signature data, others just returns invalid command error and continue to work.
            signature_data = self._get_signature_data()  # signature data
            self._ws.send(json.dumps(signature_data))  # as json string to be send

        self.subscribe_events()

    def subscribe_events(self):
        """Subscribe to topics """
        for topic in self._topics:
            params = json.dumps({"sub": topic})
            logging.info(f"Subscribing to socket data, params: {params}")
            self._ws.send(params)  # as json string to be send

    def _get_signature_data(self) -> dict:
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

    def _on_msg(self, ws, message):
        self.last_heartbeat = datetime.utcnow()
        try:
            plain = message
            if not self._be_spot:
                plain = gzip.decompress(message).decode()

            jdata = json.loads(plain)
            if 'ping' in jdata:
                sdata = plain.replace('ping', 'pong')
                self._ws.send(sdata)
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
                    self._ws.send(sdata)
                else:
                    pass
            elif 'action' in jdata:
                opdata = jdata['action']
                if opdata == 'ping':
                    sdata = plain.replace('ping', 'pong')
                    self._ws.send(sdata)
                    return
                else:
                    pass
            elif 'ch' in jdata:
                # Pass the event to receiver
                topic = jdata['ch'].lower()
                self.receiver.on_message(topic, jdata)
            elif jdata.get('status') == 'error':
                logging.error(f"Got message with error: {jdata}")
        except Exception as e:
            logging.error(e)

    def _on_close(self, *args):
        logging.info("Socket closed")

    def _on_error(self, ws, error):
        logging.error(f"Socket error: {error}")
        # Reopen
        self.close()
        self.open()

    def add_consumer(self, topic, params: dict, consumer):
        """ Registering consumer for the topic """
        logging.debug(f"Adding consumer, topic: {topic}, params: {params}, consumer: {consumer}")
        # topic -> (params, consumer obj)
        self._consumers[topic].add((json.dumps(params), consumer))

    def close(self):
        logging.info("Closing socket")
        if self._ws: self._ws.close()

    def _watchdog(self):
        watchdog_interval_sec = self.heartbeat_timeout.seconds / 2
        logging.info(f"Watchdog started with heartbeat timeout: {self.heartbeat_timeout}")
        while self.is_running:
            time.sleep(watchdog_interval_sec)
            elapsed = datetime.utcnow() - self.last_heartbeat
            if elapsed > self.heartbeat_timeout:
                logging.error(f"Watchdog: heartbeat timeout {self.heartbeat_timeout} elapsed. Reconnecting...")
                # Reopen
                self.close()
                self.open()
            else:
                logging.debug(f"Heartbeat is ok. {elapsed} elapsed since last heartbeat at {self.last_heartbeat}")
        logging.info(f"is_running: {self.is_running}. Watchdog stopped")

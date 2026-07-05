import asyncio
import json
import logging
import os
import uuid
from collections import defaultdict
from datetime import timedelta, datetime
from typing import Optional

import requests
from websockets import connect, exceptions, ClientConnection

from alor_ws_request import AlorWsRequest


class AlorWsClient:
    def __init__(self,
                 url: str = os.environ.get("ALOR_WEBSOCKET_URL", "wss://apidev.alor.ru/ws"),
                 oauth_url: str = os.environ.get("ALOR_OAUTH_URL", "https://oauthdev.alor.ru"),
                 refresh_token: str = os.environ.get("ALOR_REFRESH_TOKEN", ""),
                 tickets=tuple(os.environ.get("ALOR_TICKET", "").replace(" ", "").split(",")),
                 candles_1min_queue: asyncio.Queue = asyncio.Queue(),
                 level2_queue: asyncio.Queue = asyncio.Queue(),
                 bid_ask_queue: asyncio.Queue = asyncio.Queue(),

                 ):
        self._logger = logging.getLogger(__class__.__name__)
        self.tickets = tickets
        self._oauth_url = oauth_url
        self.url = url
        self._refresh_token = refresh_token
        self._access_token = None
        self._running = False

        self._consumers = defaultdict(set)
        self.is_running = False
        self.watchdog_thread = None
        self.heartbeat_timeout = timedelta(seconds=60)
        self._reconnect_delay = self.heartbeat_timeout
        self.last_heartbeat = datetime.utcnow()  # record last heartbeat time
        self._websocket: Optional[ClientConnection] = None

        self._websocket_ping_interval = os.environ.get("WEBSOCKET_PING_INTERVAL", 20)
        self._websocket_ping_timeout = os.environ.get("WEBSOCKET_PING_TIMEOUT", 20)
        self._websocket_close_timeout = os.environ.get("WEBSOCKET_CLOSE_TIMEOUT", 10)

        # Init queues for messages
        self._candles_guid = str(uuid.uuid4())
        self.candles_1min_queue = candles_1min_queue
        self._level2_guid = str(uuid.uuid4())
        self.level2_queue = level2_queue
        self._bid_ask_guid = str(uuid.uuid4())
        self.bid_ask_queue = bid_ask_queue
        self._queue_dict = {self._candles_guid: self.candles_1min_queue, self._level2_guid: self.level2_queue,
                            self._bid_ask_guid: self.bid_ask_queue}

        self._logger.info(
            f"Initialized, url: {self.url}, topics: {self.tickets}, token: ***{self._access_token[-3:] if self._access_token else ''}")

    async def read_messages_loop(self):
        """ Read messages from websocket, put to the queue """
        while self._running:
            try:
                await self._update_access_token()

                self._logger.info(
                    f"Connecting to {self.url}. Connection parameters:\nping_interval: {self._websocket_ping_interval},\n"
                    f"ping_timeout: {self._websocket_ping_timeout},\n"
                    f"close_timeout: {self._websocket_close_timeout}")


                async with connect(self.url,
                                   ping_interval=self._websocket_ping_interval,
                                   ping_timeout=self._websocket_ping_timeout,
                                   close_timeout=self._websocket_close_timeout,
                                   max_queue=64) as websocket:
                    self._websocket = websocket
                    self._reconnect_delay = self.heartbeat_timeout  # Reset delay after successful connection
                    await self._on_open()
                    try:
                        async for message in websocket:
                            await self._on_message(message)

                    except exceptions.ConnectionClosed as e:
                        await self._on_close(e.code, e.reason)
                        raise e  # Reraise the exception for reconnection
            except Exception as e:
                # Delay before reconnect
                await self._on_error(e)
                await asyncio.sleep(0)
                await self._handle_reconnect()

    async def _update_access_token(self):
        """
        Using constant refresh token, get new temporary access token. selt._token will be updated
        https://alor.dev/docs/api/http/jwt-token
        """
        self._logger.info(f"Updating access token using refresh token ***{self._refresh_token[-3:] if self._refresh_token else ''}. Oauth url: {self._oauth_url}")
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        payload = {"token": self._refresh_token}

        response = requests.post(self._oauth_url, json=payload, headers=headers)
        if response.status_code != 200:
            response.raise_for_status()
        # Get response as a string, update access token to new value
        self._access_token = json.loads(response.text)["AccessToken"]
        self._logger.info(f"Got new access token: ***{self._access_token[-3:] if self._access_token else ''}")

    async def run_async(self):
        self._running = True
        # Message processing loop
        await self.read_messages_loop()

    async def _handle_reconnect(self):
        if not self._running:
            return

        self._logger.info(f"Reconnecting in {self._reconnect_delay} seconds...")
        await asyncio.sleep(self._reconnect_delay.total_seconds())

        # Exponential backoff with max limit
        self._reconnect_delay = min(self.heartbeat_timeout * 2, self.heartbeat_timeout)

    async def close(self):
        self._running = False
        if self._websocket:
            await self._websocket.close()

    async def _on_open(self):
        self._logger.info(f"Socket opened: {self.url}")

        await self.subscribe_events()

    async def subscribe_events(self):
        """Subscribe to topics """
        for ticket in self.tickets:

            candles_req = await AlorWsRequest.subscribe_candles_1min_msg(self._access_token, self._candles_guid, ticket)
            level2_req = await AlorWsRequest.subscribe_level2_msg(self._access_token, self._level2_guid, ticket)
            bid_ask_req = await AlorWsRequest.subscribe_bid_ask_msg(self._access_token, self._bid_ask_guid, ticket)
            for req in [candles_req, level2_req, bid_ask_req]:
                req_obfuscated = json.loads(req)
                opcode = req_obfuscated["opcode"]
                self._logger.info(f"Subscribing to socket data, ticket: {ticket}, opcode: {opcode}")
                await self._safe_send(req)  # as json string to be send
                await asyncio.sleep(0)

    async def _safe_send(self, message, attempts=3):
        delay = 0.1
        good_flag = False
        for attempt in range(1, attempts + 1):
            try:
                await self._websocket.send(message)
                good_flag = True
                break
            except Exception as e:
                # Wait a bit and retry
                self._logger.warning(
                    f"Sending message to websocket attempt {attempt}/{attempts} failed, waiting {delay} seconds before next retry. Error is {e}")
                await asyncio.sleep(delay)
                delay *= 2
        if not good_flag:
            raise Exception("Failed to send message to websocket")

    async def _on_message(self, message):
        self.last_heartbeat = datetime.utcnow()
        # Message can be string, convert to dict if so
        if isinstance(message, str):
            message = json.loads(message)

        # Access token lives 30 minutes, check if it's expired and update it
        if "httpCode" in message and message["httpCode"] != 200:
            if message["httpCode"] == 401:
                # Update access token using refresh token according to oauth protocol
                await self._update_access_token()
            else:
                # Some other error, just log it
                self._logger.error(f"HTTP error message from websocket: {message}")
            return

        # Put the message to proper queue
        if "guid" in message and message["guid"] in self._queue_dict:
            await self._queue_dict[message["guid"]].put(json.dumps(message))

    async def _on_close(self, code, reason):
        self._logger.info(f"WebSocket connection closed: code={code}, reason={reason}")
        # Your close handler logic here

    async def _on_error(self, error):
        self._logger.error(f"WebSocket error: {error}")
        # Your error handler logic here

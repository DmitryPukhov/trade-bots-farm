import json
import uuid
from datetime import datetime


class AlorWsRequest:
    """ Helper class to form request bodies for Allor API https://alor.dev/docs/api/websocket/overview"""

    _TOPIC_SEPARATOR = "."

    def unsubscribe_msg(self, token: str, guid: uuid.UUID) -> dict:
        """
        Cancel existing subscription.
        See https://alor.dev/docs/api/websocket/data-subscriptions/Unsubscribe
        """
        return {
            "opcode": "unsubscribe",
            "guid": guid,
            "token": token
        }

    @staticmethod
    async def subscribe_candles_1min_msg(token: str, guid:str, ticket: str, ):
        exchange, instrument_group, code = ticket.split(AlorWsRequest._TOPIC_SEPARATOR)

        return json.dumps({
            "opcode": "BarsGetAndSubscribe",
            "code": code,
            "tf": "60",  # 1 min in seconds
            "from": datetime.now().timestamp(),
            "skipHistory": False,
            "splitAdjust": True,
            "exchange": exchange,
            "instrumentGroup": instrument_group,
            "format": "Slim",
            "frequency": 100,
            "guid": guid,
            "token": token
        })

    @staticmethod
    async def subscribe_level2_msg(token: str, guid: str, ticket: str, ):
        exchange, instrument_group, code = ticket.split(AlorWsRequest._TOPIC_SEPARATOR)
        return json.dumps({
            "opcode": "OrderBookGetAndSubscribe",
            "code": code,
            "depth": 10,
            "exchange": exchange,
            "instrumentGroup": instrument_group,
            "format": "Slim",
            "frequency": 100,
            "guid": guid,
            "token": token
        })

    @staticmethod
    async def subscribe_bid_ask_msg(token: str, guid: str, ticket: str, ):
        exchange, instrument_group, code = ticket.split(AlorWsRequest._TOPIC_SEPARATOR)
        return json.dumps({
            "opcode": "QuotesSubscribe",
            "code": code,
            "exchange": exchange,
            "instrumentGroup": instrument_group,
            "format": "Slim",
            "frequency": 100,
            "guid": guid,
            "token": token
        })

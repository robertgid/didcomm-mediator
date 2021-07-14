import json
from typing import Tuple, Optional

from aiohttp.client_ws import ClientWebSocketResponse
from sirius_sdk import AbstractP2PCoProtocol
from sirius_sdk.encryption.ed25519 import pack_message, unpack_message
from sirius_sdk.messaging import Message, restore_message_instance


class WebSocketCoProtocol(AbstractP2PCoProtocol):

    def __init__(self, ws: ClientWebSocketResponse, my_keys: Tuple[str, str], their_verkey: str, time_to_live: int = None):
        super().__init__(time_to_live)
        self.__transport: ClientWebSocketResponse = ws
        self.__my_keys = my_keys
        self.__their_verkey = their_verkey

    async def send(self, message: Message):
        payload = pack_message(
            message=json.dumps(message),
            to_verkeys=[self.__their_verkey],
            from_verkey=self.__my_keys[0],
            from_sigkey=self.__my_keys[1]
        )
        await self.__transport.send_bytes(payload)

    async def get_one(self) -> (Optional[Message], str, Optional[str]):
        payload = await self.__transport.receive_bytes()
        message, sender_vk, recip_vk = unpack_message(
            enc_message=payload,
            my_verkey=self.__my_keys[0],
            my_sigkey=self.__my_keys[1]
        )
        payload = json.loads(message)
        success, msg = restore_message_instance(payload)
        if success:
            return msg, sender_vk, recip_vk
        else:
            return Message(**payload), sender_vk, recip_vk

    async def switch(self, message: Message) -> (bool, Message):
        await self.send(message)
        msg, _, _ = await self.get_one()
        return True, msg

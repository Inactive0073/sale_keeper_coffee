import nats
from nats.aio.client import Client
from nats.js import JetStreamContext

from typing import Tuple, List


async def connect_to_nats(servers: List[str]) -> Tuple[Client, JetStreamContext]:
    nc: Client = await nats.connect(servers=servers)
    js: JetStreamContext = nc.jetstream()

    return nc, js

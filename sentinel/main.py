import asyncio
import signal
import logging
import sys

from sentinel.broker import Broker
from sentinel.bybit_ws import BybitWSClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("sentinel")


async def run() -> None:
    broker = Broker()
    client = BybitWSClient(broker)

    loop = asyncio.get_running_loop()

    def _request_shutdown() -> None:
        logger.info("SIGINT/SIGTERM received — initiating graceful shutdown")
        asyncio.ensure_future(client.shutdown())

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _request_shutdown)
        except NotImplementedError:
            signal.signal(sig, lambda s, f: _request_shutdown())

    try:
        await broker.connect()
        logger.info("Sentinel starting — entering main loop")
        await client.run_forever()
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt — shutting down")
    finally:
        await broker.disconnect()
        logger.info("Sentinel stopped")


def main() -> None:
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

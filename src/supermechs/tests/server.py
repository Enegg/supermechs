import asyncio
import logging
import sys
import threading

from SuperMechs.server import SMServer

logger = logging.getLogger("main")
handler = logging.StreamHandler()
logger.level = handler.level = logging.DEBUG
logger.addHandler(handler)

EXIT = "exit"


def read_input(queue: asyncio.Queue[str]) -> None:
    with sys.stdin as stdin:
        try:
            for line in iter(stdin.readline, ""):
                queue.put_nowait(line.strip())

        except (EOFError, KeyboardInterrupt):
            queue.put_nowait(EXIT)


input_queue = asyncio.Queue[str]()
input_thread = threading.Thread(target=read_input, args=(input_queue,))
input_thread.start()


async def main():
    import aiohttp

    lock = asyncio.Semaphore()

    async with aiohttp.ClientSession() as session:
        server = SMServer(session)
        sio = await server.create_socket("GodMode")

        sio.on(
            "*",
            lambda event, *data: logger.info(
                f"Unhandled event: {event} " + "".join(map(str, data))
            ),
        )

        while True:
            event = await input_queue.get()

            if event == EXIT:
                break

            async with lock:
                await sio.emit(event)


asyncio.run(main())

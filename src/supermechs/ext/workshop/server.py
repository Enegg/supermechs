import logging
import typing as t
from collections import defaultdict

from socketio import AsyncClient
from socketio.client import Handler

if t.TYPE_CHECKING:
    from aiohttp import ClientSession


logger = logging.getLogger(f"main.{__name__}")

Data = str | bytes | list["Data"] | tuple["Data", ...] | dict[str, "Data"]

CLIENT_VERSION: t.Final[str] = "2"
"""The websocket client version."""

WU_SERVER: t.Final[str] = "https://supermechs-workshop-server.thearchives.repl.co"
"""The websocket server URL."""


# possible events:
# server.message
# disconnecting
# lobby.join
# lobby.quit
# lobby.players
# lobby.players.exited
# lobby.players.matchmaker
# matchmaker.join
# matchmaker.quit
# matchmaker.validation
# profile.update
# battle.event
# battle.start
# battle.quit
# battle.event.error
# battle.event.confirmation


class SMServer:
    def __init__(self, session: "ClientSession") -> None:
        self.session = session
        self.clients: dict[str, AsyncClient] = {}

    async def create_socket(self, name: str) -> AsyncClient:
        """Create & connect to a socket for a player."""

        sio = AsyncClient(logger=logger, http_session=self.session, ssl_verify=False)
        sio.on("connect", lambda: logger.info(f"Connected as {name}"))
        sio.on("disconnect", lambda: logger.info(f"{name} disconnected"))
        sio.on(
            "connect_error", lambda data: logger.warning(f"Connection failed for {name}:\n{data}")
        )
        sio.on("message", lambda data: logger.info(f"Message: {data}"))
        sio.on("server.message", lambda data: logger.warning(f"Server message: {data}"))

        await sio.connect(
            WU_SERVER,
            headers={"x-player-name": name, "x-client-version": CLIENT_VERSION},
        )

        sid = sio.get_sid()
        logger.info(f"SID for {name} is {sid}")

        assert sid is not None
        self.clients[sid] = sio

        return sio

    async def kill_connections(self) -> None:
        """Disconnects all currently connected users."""

        for id, socket in tuple(self.clients.items()):
            await socket.disconnect()
            del self.clients[id]


class Client:
    def __init__(self, session: "ClientSession", logger: logging.Logger | bool = False) -> None:
        self.sio = AsyncClient(logger=logger, http_session=session, ssl_verify=False)
        self.sio.on("*", self.dispatch)

        self.listeners: dict[str, list[Handler]] = defaultdict(list)

    def dispatch(self, event: str, *data: t.Any) -> t.Any:
        # going the route of modifying _trigger_event would risk running into issues as we discard
        # return values and due to library emitting own events, there may be unexpected consequences
        if event in self.listeners:
            for callback in self.listeners[event]:
                callback(*data)

        else:
            self.sio.logger.info("Unhandled event: %s", event)

    def on(self, event: str, handler: Handler) -> None:
        "Register a handler for an event."
        self.listeners[event].append(handler)

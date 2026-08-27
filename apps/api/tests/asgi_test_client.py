"""Small synchronous ASGI client for the repository's test suite.

Starlette 1.6 delegates its legacy ``TestClient`` to the optional
``httpx2`` package. The project already depends on ``httpx`` and should
not need a second client implementation just to exercise its ASGI app.
This adapter preserves the synchronous API used by existing tests while
running every request on one daemon event loop through ``ASGITransport``.
"""

from __future__ import annotations

import asyncio
import queue
import threading
from collections.abc import Coroutine
from concurrent.futures import Future
from concurrent.futures import TimeoutError as FutureTimeoutError
from typing import Any

import httpx

_LOOP_READY = threading.Event()
_LOOP: asyncio.AbstractEventLoop | None = None
_SUBMISSIONS: queue.SimpleQueue[tuple[Coroutine[Any, Any, httpx.Response], Future[httpx.Response]]]
_SUBMISSIONS = queue.SimpleQueue()


async def _drain_submissions() -> None:
    """Schedule cross-thread submissions without depending on loop wakeup sockets."""

    while True:
        while True:
            try:
                coroutine, result_future = _SUBMISSIONS.get_nowait()
            except queue.Empty:
                break

            task = asyncio.create_task(coroutine)

            def transfer_result(
                completed: asyncio.Task[httpx.Response],
                target: Future[httpx.Response] = result_future,
            ) -> None:
                if target.cancelled():
                    return
                try:
                    target.set_result(completed.result())
                except BaseException as exc:
                    target.set_exception(exc)

            task.add_done_callback(transfer_result)

        await asyncio.sleep(0.001)


def _serve_event_loop() -> None:
    global _LOOP

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    _LOOP = loop
    loop.create_task(_drain_submissions())
    _LOOP_READY.set()
    loop.run_forever()


_LOOP_THREAD = threading.Thread(
    target=_serve_event_loop,
    name="riotqueens-asgi-test-loop",
    daemon=True,
)
_LOOP_THREAD.start()


def _event_loop() -> asyncio.AbstractEventLoop:
    if not _LOOP_READY.wait(timeout=5.0) or _LOOP is None:
        raise RuntimeError("ASGI test event loop failed to start")
    return _LOOP


class SyncASGIClient:
    """Expose blocking request helpers backed by ``httpx.AsyncClient``."""

    __test__ = False

    def __init__(
        self,
        app: Any,
        *,
        raise_server_exceptions: bool = True,
        request_timeout_seconds: float = 30.0,
    ) -> None:
        self.app = app
        self._raise_app_exceptions = raise_server_exceptions
        self._request_timeout_seconds = request_timeout_seconds

    async def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        transport = httpx.ASGITransport(
            app=self.app,
            raise_app_exceptions=self._raise_app_exceptions,
        )
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
            timeout=self._request_timeout_seconds,
        ) as client:
            return await client.request(method, url, **kwargs)

    def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        _event_loop()
        future: Future[httpx.Response] = Future()
        _SUBMISSIONS.put((self._request(method, url, **kwargs), future))
        try:
            return future.result(timeout=self._request_timeout_seconds)
        except FutureTimeoutError as exc:
            future.cancel()
            raise TimeoutError(
                f"ASGI request exceeded {self._request_timeout_seconds:g}s: "
                f"{method.upper()} {url}"
            ) from exc

    def get(self, url: str, **kwargs: Any) -> httpx.Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> httpx.Response:
        return self.request("POST", url, **kwargs)

    def delete(self, url: str, **kwargs: Any) -> httpx.Response:
        return self.request("DELETE", url, **kwargs)

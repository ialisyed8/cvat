# Copyright (C) CVAT.ai Corporation
#
# SPDX-License-Identifier: MIT

"""
Live label counts over a WebSocket.

Every push is produced by running the regular
GET /api/annotation-analytics/tasks/<id>/label-counts request through the full Django
middleware, authentication and permission stack, so the socket never shows data
the HTTP endpoint would refuse, and losing access closes the socket.
"""

import asyncio
import io
import re
from urllib.parse import urlsplit

from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.exceptions import DisallowedHost
from django.core.handlers.asgi import ASGIRequest
from django.core.handlers.base import BaseHandler
from django.db import close_old_connections

LABEL_COUNTS_WS_PATH = re.compile(r"^/api/annotation-analytics/tasks/\d+/label-counts/ws$")
POLL_INTERVAL_SECONDS = 2

# Application close codes are 4000 + the HTTP status of the refused request,
# e.g. 4401 (no login), 4403 (no access), 4404 (no such task).
CLOSE_CODE_BASE = 4000


class _RequestRunner:
    def __init__(self):
        self._handler = None

    def run(self, scope) -> tuple[int, str]:
        if self._handler is None:
            self._handler = BaseHandler()
            self._handler.load_middleware()

        headers = [(name, value) for name, value in scope["headers"] if name != b"accept-encoding"]
        http_scope = {
            **scope,
            "type": "http",
            "method": "GET",
            "path": scope["path"].removesuffix("/ws"),
            "headers": headers,
        }

        close_old_connections()
        try:
            response = self._handler.get_response(ASGIRequest(http_scope, io.BytesIO()))
            return response.status_code, response.content.decode()
        finally:
            close_old_connections()


def _is_same_origin(scope) -> bool:
    headers = dict(scope["headers"])
    origin = headers.get(b"origin")
    if origin is None:
        # not a browser, the request is still authenticated as usual
        return True

    origin = origin.decode()
    request = ASGIRequest({**scope, "type": "http", "method": "GET"}, io.BytesIO())
    try:
        host = request.get_host()
    except DisallowedHost:
        return False
    return urlsplit(origin).netloc == host or origin in settings.CSRF_TRUSTED_ORIGINS


class LabelCountsWebSocketRouter:
    def __init__(self, app):
        self._app = app
        self._runner = _RequestRunner()

    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket" and LABEL_COUNTS_WS_PATH.match(scope["path"]):
            await self._serve(scope, receive, send)
        else:
            await self._app(scope, receive, send)

    async def _fetch(self, scope) -> tuple[int, str]:
        return await sync_to_async(self._runner.run)(scope)

    async def _serve(self, scope, receive, send):
        message = await receive()
        if message["type"] != "websocket.connect":
            return

        # accept first, so that the client receives the application close code
        await send({"type": "websocket.accept"})

        if not _is_same_origin(scope):
            await send({"type": "websocket.close", "code": CLOSE_CODE_BASE + 403})
            return

        last_body = None
        receive_task = asyncio.ensure_future(receive())
        try:
            while True:
                status, body = await self._fetch(scope)
                if status != 200:
                    await send({"type": "websocket.close", "code": CLOSE_CODE_BASE + status})
                    return

                if body != last_body:
                    await send({"type": "websocket.send", "text": body})
                    last_body = body

                # client messages are ignored and do not trigger extra polls
                loop = asyncio.get_running_loop()
                deadline = loop.time() + POLL_INTERVAL_SECONDS
                while (remaining := deadline - loop.time()) > 0:
                    done, _ = await asyncio.wait({receive_task}, timeout=remaining)
                    if not done:
                        break
                    if receive_task.result()["type"] == "websocket.disconnect":
                        return
                    receive_task = asyncio.ensure_future(receive())
        finally:
            receive_task.cancel()

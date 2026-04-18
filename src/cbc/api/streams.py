from __future__ import annotations

from fastapi.responses import StreamingResponse


def simple_stream(text: str) -> StreamingResponse:
    async def iterator():
        yield text

    return StreamingResponse(iterator(), media_type="text/plain")

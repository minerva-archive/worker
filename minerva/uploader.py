import asyncio
import hashlib
from pathlib import Path
from typing import Callable

import httpx

from minerva.auth import auth_headers
from minerva.constants import (
    UPLOAD_CHUNK_RETRIES,
    UPLOAD_CHUNK_SIZE,
    UPLOAD_FINISH_RETRIES,
    UPLOAD_START_RETRIES,
)
from minerva.error_handling import _raise_if_upgrade_required, _retry_sleep, _retryable_status


async def upload_file(
    upload_server_url: str, token: str, file_id: int, path: Path, on_progress: Callable[[int, int], None] | None = None
) -> dict:
    # Fresh client per upload: multipart state must not be shared across coroutines
    headers = auth_headers(token)
    timeout = httpx.Timeout(connect=30, read=300, write=300, pool=30)
    async with httpx.AsyncClient(timeout=timeout) as client:
        # 1. Start session
        session_id = None
        for attempt in range(1, UPLOAD_START_RETRIES + 1):
            try:
                resp = await client.post(f"{upload_server_url}/api/upload/{file_id}/start", headers=headers)
                _raise_if_upgrade_required(resp)
                if _retryable_status(resp.status_code):
                    if attempt == UPLOAD_START_RETRIES:
                        raise RuntimeError(f"upload start failed ({resp.status_code})")
                    await asyncio.sleep(_retry_sleep(attempt))
                    continue
                resp.raise_for_status()
                session_id = resp.json()["session_id"]
                break
            except httpx.HTTPError as e:
                if attempt == UPLOAD_START_RETRIES:
                    raise RuntimeError(f"upload start failed ({e})") from e
                await asyncio.sleep(_retry_sleep(attempt))
        if not session_id:
            raise RuntimeError("Failed to create upload session")

        # 2. Send chunks
        file_size = path.stat().st_size
        sent = 0
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            while True:
                data = f.read(UPLOAD_CHUNK_SIZE)
                if not data:
                    break
                hasher.update(data)
                for attempt in range(1, UPLOAD_CHUNK_RETRIES + 1):
                    try:
                        resp = await client.post(
                            f"{upload_server_url}/api/upload/{file_id}/chunk",
                            params={"session_id": session_id},
                            headers={**headers, "Content-Type": "application/octet-stream"},
                            content=data,
                        )
                        _raise_if_upgrade_required(resp)
                        if _retryable_status(resp.status_code):
                            if attempt == UPLOAD_CHUNK_RETRIES:
                                raise RuntimeError(f"upload chunk failed ({resp.status_code})")
                            await asyncio.sleep(_retry_sleep(attempt, cap=20.0))
                            continue
                        resp.raise_for_status()
                        break
                    except httpx.HTTPError as e:
                        if attempt == UPLOAD_CHUNK_RETRIES:
                            raise RuntimeError(f"upload chunk failed ({e})") from e
                        await asyncio.sleep(_retry_sleep(attempt, cap=20.0))
                sent += len(data)
                if on_progress is not None:
                    on_progress(sent, file_size)

        # 3. Finish
        expected_sha256 = hasher.hexdigest()
        result: dict = {}
        for attempt in range(1, UPLOAD_FINISH_RETRIES + 1):
            try:
                resp = await client.post(
                    f"{upload_server_url}/api/upload/{file_id}/finish",
                    params={"session_id": session_id, "expected_sha256": expected_sha256},
                    headers=headers,
                )
                _raise_if_upgrade_required(resp)
                if _retryable_status(resp.status_code):
                    if attempt == UPLOAD_FINISH_RETRIES:
                        raise RuntimeError(f"upload finish failed ({resp.status_code})")
                    await asyncio.sleep(_retry_sleep(attempt, cap=20.0))
                    continue
                resp.raise_for_status()
                result = resp.json()
                break
            except httpx.HTTPError as e:
                if attempt == UPLOAD_FINISH_RETRIES:
                    raise RuntimeError(f"upload finish failed ({e})") from e
                await asyncio.sleep(_retry_sleep(attempt, cap=20.0))

        return result


__all__ = ["upload_file"]

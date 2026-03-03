import asyncio
import urllib.parse
from pathlib import Path

import httpx
import humanize
from pathvalidate import sanitize_filepath

from minerva.auth import auth_headers
from minerva.console import WorkerDisplay, console
from minerva.constants import MAX_RETRIES, REPORT_RETRIES, RETRY_DELAY
from minerva.downloader import download_file
from minerva.error_handling import _raise_if_upgrade_required, _retry_sleep, _retryable_status
from minerva.uploader import upload_file


def _response_detail(resp: httpx.Response) -> str:
    try:
        body = resp.json()
        if isinstance(body, dict):
            detail = body.get("detail")
            if detail is not None:
                return str(detail).strip()
    except Exception:
        pass
    return (resp.text or "").strip()


async def process_job(
    server_url: str,
    upload_server_url: str,
    token: str,
    job: dict,
    temp_dir: Path,
    keep_files: bool,
    aria2c_connections: int,
    pre_allocation: str,
    display: WorkerDisplay,
) -> None:
    file_id = job["file_id"]
    url = job["url"]
    dest_path = job["dest_path"]
    label = urllib.parse.unquote(dest_path if len(dest_path) <= 60 else "…" + dest_path[-57:])
    known_size = job.get("size", 0) or 0
    display.job_start(file_id, label)

    last_err: Exception | None = None
    file_size: int | None = None
    uploaded: bool = False

    # get local file path, mirroring URL path to avoid collisions
    # decodes percent-encoded characters, removes invalid path characters
    try:
        parsed_url = urllib.parse.urlparse(url)
        url_path = urllib.parse.unquote(parsed_url.path).lstrip("/")
        unsafe_local_path = temp_dir / parsed_url.netloc / url_path
        local_path = sanitize_filepath(unsafe_local_path, normalize=True)
    except ValueError as e:
        last_err = e
        display.job_done(file_id, label, ok=False, note=f"Invalid filename: {e}")
        try:
            await report_job(server_url, token, file_id, "failed", error=str(last_err)[:500])
        except Exception:
            pass
        console.print(f"[red]  {dest_path}: Invalid filename: {e}")
        return

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # Download
            display.job_update(file_id, "DL")
            await download_file(
                url,
                local_path,
                aria2c_connections,
                known_size,
                pre_allocation,
                on_progress=lambda done, size: display.job_update(file_id=file_id, status="DL", size=size, done=done),
            )
            file_size = local_path.stat().st_size
            # Upload
            display.job_update(file_id, "UL", size=file_size or 0)
            await upload_file(
                upload_server_url=upload_server_url,
                token=token,
                file_id=file_id,
                path=local_path,
                on_progress=lambda done, size: display.job_update(file_id=file_id, status="UL", size=size, done=done),
            )
            uploaded = True
            break
        except Exception as e:
            last_err = e
            if attempt < MAX_RETRIES:
                display.job_update(file_id, "RT")
                await asyncio.sleep(RETRY_DELAY * attempt)

    if not uploaded:
        # All retries exhausted on download/upload path
        display.job_done(file_id, label, ok=False, note=f"[{MAX_RETRIES} attempts] {str(last_err)}")
        try:
            await report_job(server_url, token, file_id, "failed", error=str(last_err)[:500])
        except Exception:
            pass
        local_path.unlink(missing_ok=True)
        return

    # Surface success to user immediately once upload bytes + finish call succeeded
    display.job_done(file_id, label, ok=True, note=humanize.naturalsize(file_size))
    if not keep_files:
        local_path.unlink(missing_ok=True)

    # Best-effort completion report; do not re-run transfer on control-plane flakiness.
    try:
        await report_job(server_url, token, file_id, "completed", bytes_downloaded=file_size)
    except Exception as e:
        console.print(f"[yellow]  {dest_path}: uploaded but report delayed ({str(e)[:120]})")


async def report_job(
    server_url: str,
    token: str,
    file_id: int,
    status: str,
    bytes_downloaded: int | None = None,
    error: str | None = None,
) -> None:
    async with httpx.AsyncClient(timeout=30) as client:
        for attempt in range(1, REPORT_RETRIES + 1):
            try:
                resp = await client.post(
                    f"{server_url}/api/jobs/report",
                    headers=auth_headers(token),
                    json={"file_id": file_id, "status": status, "bytes_downloaded": bytes_downloaded, "error": error},
                )
                _raise_if_upgrade_required(resp)
                if resp.status_code == 401:
                    raise RuntimeError("Token expired. Run: python worker.py login")
                if resp.status_code == 409 and status == "completed":
                    # Async finalize race: upload accepted, but finalize/verify not visible yet.
                    detail = _response_detail(resp).lower()
                    if "not finalized" in detail or "upload" in detail:
                        if attempt == REPORT_RETRIES:
                            resp.raise_for_status()
                        await asyncio.sleep(min(2.0, 0.25 + attempt * 0.1))
                        continue
                if _retryable_status(resp.status_code):
                    if attempt == REPORT_RETRIES:
                        resp.raise_for_status()
                    await asyncio.sleep(_retry_sleep(attempt, cap=20.0))
                    continue
                resp.raise_for_status()
                return
            except httpx.HTTPError:
                if attempt == REPORT_RETRIES:
                    raise
                await asyncio.sleep(_retry_sleep(attempt, cap=20.0))

import asyncio
from asyncio.subprocess import Process
from pathlib import Path
from typing import Any, AsyncGenerator

from minerva.constants import ARIA2C
from minerva.downloaders import Downloader, ProgressCallback


class Aria2c(Downloader):
    async def __call__(
        self, url: str, dest: Path, connections: int, pre_allocation: str, on_progress: ProgressCallback
    ) -> None:
        if not ARIA2C:
            raise EnvironmentError("Cannot download with aria2c as it could not be found...")

        proc = await asyncio.create_subprocess_exec(
            str(ARIA2C),
            f"--max-connection-per-server={connections}",
            f"--split={connections}",
            f"--file-allocation={pre_allocation}",
            "--min-split-size=1M",
            "--dir",
            str(dest.parent),
            "--out",
            dest.name,
            "--auto-file-renaming=false",
            "--allow-overwrite=true",
            "--console-log-level=warn",
            "--retry-wait=3",
            "--max-tries=5",
            "--timeout=120",
            "--connect-timeout=15",
            "--continue",
            url,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        async def consume_progress() -> None:
            async for downloaded, total in Aria2c.get_progress(dest, proc):
                on_progress(downloaded, total)

        progress_task = asyncio.create_task(consume_progress())

        try:
            _, stderr = await proc.communicate()
        finally:
            progress_task.cancel()
            await asyncio.gather(progress_task, return_exceptions=True)

        if proc.returncode != 0:
            raise RuntimeError(f"aria2c exit {proc.returncode}: {stderr.decode()[:200]}")

    @staticmethod
    async def get_progress(filename: Path, proc: Process) -> AsyncGenerator[tuple[int, int], None]:
        """Yield progress of an Aria2c download by reading its .aria2 control file."""
        try:
            while proc.returncode is None:
                try:
                    data = Aria2c.parse_control_file(filename.with_suffix(f"{filename.suffix}.aria2"))
                    yield data["downloaded_length"], data["total_length"]
                except FileNotFoundError:
                    pass
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            return

    @staticmethod
    def parse_control_file(filename: Path) -> dict[str, Any]:
        """Parse Aria2c's .aria2 control file to get download progress information."""
        with open(filename, "rb") as fp:
            fp.read(2)  # version
            fp.read(4)  # ext
            infohashlength = int.from_bytes(fp.read(4), byteorder="big", signed=False)
            fp.read(infohashlength)

            piece_length = int.from_bytes(fp.read(4), byteorder="big", signed=False)
            total_length = int.from_bytes(fp.read(8), byteorder="big", signed=False)
            fp.read(8)  # upload_length
            bitfield_length = int.from_bytes(fp.read(4), byteorder="big", signed=False)
            bitfield = fp.read(bitfield_length)
            downloaded_chunks = int.from_bytes(bitfield, "big").bit_count()

            return {
                "filename": filename,
                "total_length": total_length,
                "downloaded_length": min(downloaded_chunks * piece_length, total_length),
                "total_chunks": bitfield_length * 8,
                "downloaded_chunks": downloaded_chunks,
            }


__all__ = ["Aria2c"]

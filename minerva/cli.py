"""
Minerva DPN Worker — single-file volunteer download client.

Optional (faster downloads):
    Install aria2c: https://aria2.github.io/

Usage:
    minerva login                    # Authenticate with Discord
    minerva run                      # Start downloading
    minerva run -c 8 -b 24           # 8 concurrent, fetch 24 per batch
    minerva run --server http://...  # Custom server URL
"""

import asyncio
from pathlib import Path

import click

from minerva import __version__
from minerva.auth import do_login, load_token
from minerva.console import console
from minerva.constants import (
    ARIA2C_CONNECTIONS,
    ARIA2C_PRE_ALLOCATION,
    BATCH_SIZE,
    CONCURRENCY,
    KEEP_FILES,
    SERVER_URL,
    TEMP_DIR,
    UPLOAD_SERVER_URL,
)
from minerva.doctor import doctor_cmd
from minerva.loop import worker_loop
from minerva.version_check import check_for_update


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx: click.Context) -> None:
    """Minerva Worker — help archive the internet."""
    check_for_update()
    console.print(f"[bold green]Minerva Worker v{__version__}[/bold green]")
    if ctx.invoked_subcommand is None:
        ctx.invoke(run)


@main.command()
@click.option("--server", default=SERVER_URL, help="Manager server URL")
def login(server: str) -> str:
    """Authenticate with Discord."""
    return do_login(server)


@main.command()
def status() -> None:
    """Show login status."""
    token = load_token()
    console.print("[green]Logged in" if token else "[red]Not logged in")


@main.command()
@click.pass_context
@click.option("--server", default=SERVER_URL, help="Manager server URL")
@click.option("--upload-server", default=UPLOAD_SERVER_URL, help="Upload API URL")
@click.option("-c", "--concurrency", default=CONCURRENCY, help="Concurrent downloads")
@click.option("-b", "--batch-size", default=BATCH_SIZE, help="Max files to fetch per API call")
@click.option("-a", "--aria2c-connections", default=ARIA2C_CONNECTIONS, help="aria2c connections per file")
@click.option(
    "-p",
    "--pre-allocation",
    default=ARIA2C_PRE_ALLOCATION,
    help="Pre-allocation method when using aria2c (prealloc, falloc, none)",
)
@click.option("--temp-dir", default=str(TEMP_DIR), help="Temp download dir")
@click.option("--keep-files", is_flag=True, default=KEEP_FILES, help="Keep downloaded files after upload")
def run(
    ctx: click.Context,
    server: str,
    upload_server: str,
    concurrency: int,
    batch_size: int,
    aria2c_connections: int,
    pre_allocation: str,
    temp_dir: str,
    keep_files: bool,
) -> None:
    """Start downloading and uploading files."""
    # Ensure user is logged-in first
    token = load_token()
    if not token:
        token = ctx.invoke(login, server=server)
    if not token:
        console.print("[red]Could not login, please try again...")
        return

    # start main loop
    asyncio.run(
        worker_loop(
            server,
            upload_server,
            token,
            Path(temp_dir),
            concurrency,
            batch_size,
            aria2c_connections,
            pre_allocation,
            keep_files,
        )
    )


main.add_command(doctor_cmd)

if __name__ == "__main__":
    main()

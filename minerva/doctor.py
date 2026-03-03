import shutil
from pathlib import Path

import click
import httpx

from minerva.auth import load_token
from minerva.console import console
from minerva.constants import (
    CONNECTIVITY_CHECK_TIMEOUT,
    HAS_ARIA2C,
    SERVER_URL,
    TEMP_DIR,
    UPLOAD_SERVER_URL,
)
from minerva.version_check import check_for_update


def check_url(name: str, url: str) -> None:
    try:
        with httpx.Client(timeout=CONNECTIVITY_CHECK_TIMEOUT) as client:
            resp = client.get(url)

            # expect any kind of response
            if resp.status_code >= 200 and resp.status_code < 400:
                print_success(name, f"Connected and working (code {resp.status_code})")
            else:
                print_warn(name, f"Connected, but returned HTTP code {resp.status_code}")
    except Exception as e:
        print_error(name, f"Failed to connect - {e}")


def print_success(tag: str, message: str) -> None:
    console.print(f"[green]✅ {tag + ':':<16}[/green] {message}")


def print_error(tag: str, message: str) -> None:
    console.print(f"[red]❌ {tag + ':':<16}[/red] {message}")


def print_warn(tag: str, message: str) -> None:
    console.print(f"[yellow]⚠️ {tag + ':':<16}[/yellow] {message}")


@click.command("doctor")
@click.option("--server", default=SERVER_URL, help="Manager server URL")
@click.option("--upload-server", default=UPLOAD_SERVER_URL, help="Upload API URL")
@click.option("--temp-dir", default=str(TEMP_DIR), help="Temp download dir")
def doctor_cmd(server: str, upload_server: str, temp_dir: str) -> None:
    console.print("[bold]Checking your setup...[/bold]")

    token = load_token()
    if token:
        print_success("Login Token", "Logged in")
    else:
        print_error("Login Token", "Not set (run `minerva login` first)")

    check_url("Internet", "http://google.com/gen_204")
    check_url("Manager Server", server)
    check_url("Upload Server", upload_server)

    has_update = check_for_update()
    if not has_update:
        print_success("Script version", "Up to date")
    else:
        print_warn("Script version", "A new version is available")

    if HAS_ARIA2C:
        print_success("Downloader", "aria2c installed")
    else:
        print_warn("Downloader", "aria2c not found, using slower httpx")

    t_dir = Path(temp_dir)
    try:
        t_dir.mkdir(parents=True, exist_ok=True)
        test_file = t_dir / ".doctor_test"
        test_file.write_text("test")
        test_file.unlink()
        print_success("Temp Directory", f"Writable ({t_dir})")
    except Exception as e:
        print_error("Temp Directory", f"Not writable ({t_dir}) - {e}")

    if t_dir.exists():
        _, _, free = shutil.disk_usage(t_dir)
        free_gb = free / (1024**3)
        print_success("Free Space", f"{free_gb:.2f} GB available")

    console.print()

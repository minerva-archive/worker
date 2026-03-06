import http.server
import threading
import urllib.parse
import webbrowser
from typing import Any

from rich.console import Console

from minerva import __version__
from minerva.constants import AUTH_HOST, AUTH_PORT, IS_DOCKER, TOKEN_FILE


def auth_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "X-Minerva-Worker-Version": __version__,
    }


def save_token(token: str) -> None:
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(token)


def load_token() -> str | None:
    if TOKEN_FILE.exists():
        t = TOKEN_FILE.read_text().strip()
        if t:
            return t
    return None


def do_login(server_url: str) -> str:
    token = None
    event = threading.Event()

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            nonlocal token
            params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if "token" in params:
                token = params["token"][0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h2>Logged in! You can close this tab.</h2>")
                event.set()
            else:
                self.send_response(400)
                self.end_headers()

        def log_message(self, *_: Any) -> None:
            pass

    srv = http.server.HTTPServer((AUTH_HOST, AUTH_PORT), Handler)
    srv.timeout = 120

    console = Console()

    url = f"{server_url}/auth/discord/login?worker_callback=http://{AUTH_HOST}:{AUTH_PORT}/"
    console.print("[bold]Opening browser for Discord login...")
    console.print(f"[dim]If it doesn't open: {url}")
    webbrowser.open(url)
    if IS_DOCKER:
        console.print("[dim]You seem to be running in a container which might not be able to open a browser link.")
        console.print("[dim]If the link is not working, see the alternative authentication method in the README.")

    while not event.is_set():
        srv.handle_request()
    srv.server_close()

    if not token:
        raise RuntimeError("Login failed")

    save_token(token)
    console.print("[bold green]Login successful!")

    return token

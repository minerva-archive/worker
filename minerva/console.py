import collections
import threading

import humanize
from rich import box
from rich.console import Console, Group
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from minerva.constants import HISTORY_LINES

console = Console()


class WorkerDisplay:
    """
    Fixed-height terminal display:
      • HISTORY_LINES of recent completed/failed jobs (oldest scrolls off)
      • divider rule
      • one row per active worker slot
    """

    def __init__(self) -> None:
        self.history: collections.deque = collections.deque(maxlen=HISTORY_LINES)
        self.active: dict = {}  # file_id -> dict
        self._lock = threading.Lock()

    def job_start(self, file_id: int, label: str) -> None:
        with self._lock:
            self.active[file_id] = dict(label=label, status="DL", size=0, done=0)

    def job_update(self, file_id: int, status: str, size: int | None = None, done: int | None = None) -> None:
        with self._lock:
            if file_id in self.active:
                entry = self.active[file_id]
                entry["status"] = status
                if size is not None:
                    entry["size"] = size
                if done is not None:
                    entry["done"] = done

    def job_done(self, file_id: int, label: str, ok: bool, note: str = "") -> None:
        with self._lock:
            self.active.pop(file_id, None)
            icon = "[green]✓[/green]" if ok else "[red]✗[/red]"
            color = "green" if ok else "red"
            entry = f"{icon} [{color}]{label}[/{color}]"
            if note:
                entry += f"  [dim]{note}[/dim]"
            self.history.append(entry)

    def __rich__(self) -> Group:
        # History panel — always HISTORY_LINES tall so active table stays anchored
        lines = list(self.history)
        while len(lines) < HISTORY_LINES:
            lines.insert(0, "[dim]—[/dim]")

        # Active jobs table
        table = Table(box=box.SIMPLE, show_header=True, expand=True, header_style="bold dim", padding=(0, 1))
        table.add_column("", width=3)  # status badge
        table.add_column("File")
        table.add_column("Size", width=7, justify="right")
        table.add_column("Progress", width=24)

        with self._lock:
            snapshot = list(self.active.values())

        for info in snapshot:
            st = info["status"]
            color = {"DL": "cyan", "UL": "yellow", "RT": "magenta"}.get(st, "white")
            size = info["size"]
            done = info["done"]

            if size:
                pct = min(1.0, done / size)
                bar_w = 14
                filled = int(bar_w * pct)
                bar = (
                    f"[{color}]"
                    + "█" * filled
                    + f"[/{color}]"
                    + "[dim]"
                    + "░" * (bar_w - filled)
                    + "[/dim]"
                    + f" {pct * 100:4.0f}%"
                )
            else:
                bar = "[dim]working…[/dim]"

            table.add_row(
                f"[{color}]{st}[/{color}]",
                info["label"],
                humanize.naturalsize(size) if size else "?",
                bar,
            )

        return Group(
            *[Text.from_markup(line) for line in lines],
            Rule(style="dim"),
            table,
        )

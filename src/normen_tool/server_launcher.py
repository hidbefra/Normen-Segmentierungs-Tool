from __future__ import annotations

import logging
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from pathlib import Path

if __package__ in {None, ""}:
    package_root = Path(__file__).resolve().parents[2]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))

import uvicorn

from normen_tool.logging_config import setup_logging


logger = logging.getLogger(__name__)


class ServerController:
    def __init__(self, host: str = "127.0.0.1", port: int = 8000) -> None:
        self.host = host
        self.port = port
        self._server: uvicorn.Server | None = None
        self._thread: threading.Thread | None = None
        self._error: str | None = None
        self._log_level = "INFO"

    @property
    def is_running(self) -> bool:
        return (
            self._thread is not None
            and self._thread.is_alive()
            and bool(self._server and self._server.started)
        )

    @property
    def is_starting(self) -> bool:
        return (
            self._thread is not None
            and self._thread.is_alive()
            and not bool(self._server and self._server.started)
        )

    @property
    def error(self) -> str | None:
        return self._error

    def start(self, log_level: str = "INFO") -> bool:
        if self._thread is not None and self._thread.is_alive():
            return False

        self._error = None
        self._log_level = log_level.upper()
        setup_logging(log_level=self._log_level)
        logger.info("Server launcher requested start on %s:%s", self.host, self.port)

        config = uvicorn.Config(
            "normen_tool.main:app",
            host=self.host,
            port=self.port,
            log_level=self._log_level.lower(),
            access_log=True,
            log_config=None,
            reload=False,
            loop="asyncio",
        )
        self._server = uvicorn.Server(config)
        self._server.install_signal_handlers = lambda: None  # type: ignore[assignment]

        self._thread = threading.Thread(target=self._run_server, daemon=True)
        self._thread.start()
        return True

    def _run_server(self) -> None:
        try:
            assert self._server is not None
            self._server.run()
        except Exception as exc:  # pragma: no cover - defensive GUI boundary
            self._error = str(exc)
            logger.exception("Server failed to start")

    def stop(self) -> bool:
        if self._server is None:
            return False

        logger.info("Server launcher requested stop")
        self._server.should_exit = True
        if self._thread is not None:
            self._thread.join(timeout=5)
        return True

    def status_text(self) -> str:
        if self._error:
            return f"Fehler: {self._error}"
        if self.is_running:
            return f"Läuft auf http://{self.host}:{self.port}"
        if self.is_starting:
            return "Server startet..."
        return "Server gestoppt"


class ServerLauncherApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Normen-Segmentierungs-Tool Launcher")
        self.geometry("460x220")
        self.resizable(False, False)

        self.controller = ServerController()
        self.log_level_var = tk.StringVar(value="INFO")
        self.status_var = tk.StringVar(value="Server gestoppt")
        self.url_var = tk.StringVar(value="http://127.0.0.1:8000")

        self._build_ui()
        self.after(250, self._refresh_status)

    def _build_ui(self) -> None:
        container = ttk.Frame(self, padding=16)
        container.pack(fill="both", expand=True)

        title = ttk.Label(
            container, text="Normen-Segmentierungs-Tool", font=("Segoe UI", 13, "bold")
        )
        title.grid(row=0, column=0, columnspan=3, sticky="w")

        ttk.Label(container, text="Status:").grid(
            row=1, column=0, sticky="w", pady=(16, 4)
        )
        ttk.Label(container, textvariable=self.status_var).grid(
            row=1, column=1, columnspan=2, sticky="w", pady=(16, 4)
        )

        ttk.Label(container, text="URL:").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Label(container, textvariable=self.url_var).grid(
            row=2, column=1, columnspan=2, sticky="w", pady=4
        )

        ttk.Label(container, text="Log-Level:").grid(
            row=3, column=0, sticky="w", pady=4
        )
        level_box = ttk.Combobox(
            container,
            textvariable=self.log_level_var,
            values=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
            state="readonly",
            width=12,
        )
        level_box.grid(row=3, column=1, sticky="w", pady=4)

        self.start_button = ttk.Button(
            container, text="Server starten", command=self._start_server
        )
        self.start_button.grid(row=4, column=0, pady=(22, 0), sticky="w")

        self.stop_button = ttk.Button(
            container, text="Server stoppen", command=self._stop_server
        )
        self.stop_button.grid(row=4, column=1, pady=(22, 0), sticky="w")

        open_logs_button = ttk.Button(
            container, text="Log-Ordner öffnen", command=self._open_log_folder
        )
        open_logs_button.grid(row=4, column=2, pady=(22, 0), sticky="e")

        container.columnconfigure(2, weight=1)

    def _start_server(self) -> None:
        started = self.controller.start(self.log_level_var.get())
        if not started:
            messagebox.showinfo(
                "Server", "Der Server läuft bereits oder startet gerade."
            )

    def _stop_server(self) -> None:
        if not self.controller.stop():
            messagebox.showinfo("Server", "Kein laufender Server gefunden.")

    def _open_log_folder(self) -> None:
        log_path = setup_logging(log_level=self.log_level_var.get())
        folder = str(Path(log_path).parent)
        try:
            import os

            os.startfile(folder)
        except Exception as exc:  # pragma: no cover - GUI convenience
            messagebox.showerror(
                "Logs", f"Log-Ordner konnte nicht geöffnet werden: {exc}"
            )

    def _refresh_status(self) -> None:
        self.status_var.set(self.controller.status_text())
        if self.controller.is_running:
            self.url_var.set(f"http://{self.controller.host}:{self.controller.port}")
        if self.controller.error:
            messagebox.showerror("Serverfehler", self.controller.error)
            self.controller._error = None
        self.after(500, self._refresh_status)


def main() -> None:
    setup_logging()
    app = ServerLauncherApp()
    app.mainloop()


if __name__ == "__main__":
    main()

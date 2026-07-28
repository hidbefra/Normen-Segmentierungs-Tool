from __future__ import annotations


from normen_tool.server_launcher import ServerController


class FakeServer:
    def __init__(self, config) -> None:
        self.config = config
        self.started = False
        self.should_exit = False
        self.install_signal_handlers = lambda: None
        self.run_calls = 0

    def run(self) -> None:
        self.run_calls += 1
        self.started = True


class FakeThread:
    def __init__(self, target, daemon=True) -> None:
        self.target = target
        self.daemon = daemon
        self._alive = False

    def start(self) -> None:
        self._alive = True
        self.target()

    def is_alive(self) -> bool:
        return self._alive

    def join(self, timeout=None) -> None:
        self._alive = False


def test_server_controller_start_stop_and_status(monkeypatch, tmp_path):
    captured = {}

    def fake_setup_logging(
        *, log_level="INFO", log_dir=None, log_file_name="normen_tool.log", force=False
    ):
        captured["log_level"] = log_level
        captured["log_dir"] = log_dir
        captured["force"] = force
        return tmp_path / log_file_name

    def fake_config(app, host, port, log_level, access_log, log_config, reload, loop):
        captured["config"] = {
            "app": app,
            "host": host,
            "port": port,
            "log_level": log_level,
            "access_log": access_log,
            "log_config": log_config,
            "reload": reload,
            "loop": loop,
        }
        return object()

    def fake_server(config):
        server = FakeServer(config)
        captured["server"] = server
        return server

    monkeypatch.setattr("normen_tool.server_launcher.setup_logging", fake_setup_logging)
    monkeypatch.setattr("normen_tool.server_launcher.uvicorn.Config", fake_config)
    monkeypatch.setattr("normen_tool.server_launcher.uvicorn.Server", fake_server)
    monkeypatch.setattr("normen_tool.server_launcher.threading.Thread", FakeThread)

    controller = ServerController(host="127.0.0.1", port=9000)

    assert controller.status_text() == "Server gestoppt"
    assert controller.start(log_level="debug") is True
    assert captured["log_level"] == "DEBUG"
    assert captured["config"]["host"] == "127.0.0.1"
    assert captured["config"]["port"] == 9000
    assert captured["config"]["log_level"] == "debug"
    assert captured["config"]["log_config"] is None
    assert controller.status_text() == "Läuft auf http://127.0.0.1:9000"

    assert controller.start() is False
    assert controller.stop() is True
    assert captured["server"].should_exit is True
    assert controller.status_text() == "Server gestoppt"


def test_server_controller_run_failure_sets_error(monkeypatch):
    class FailingServer:
        started = False

        def run(self) -> None:
            raise RuntimeError("boom")

    controller = ServerController()
    controller._server = FailingServer()  # type: ignore[assignment]

    monkeypatch.setattr(
        "normen_tool.server_launcher.logger.exception", lambda *args, **kwargs: None
    )

    controller._run_server()

    assert controller.error == "boom"
    assert controller.status_text() == "Fehler: boom"

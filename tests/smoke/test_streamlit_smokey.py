from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests

ROOT = Path(__file__).resolve().parents[2]
APP_PATH = ROOT / "streamlit_app.py"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_health(
    url: str,
    process: subprocess.Popen,
    timeout_seconds: float = 30.0,
) -> requests.Response:
    deadline = time.monotonic() + timeout_seconds
    last_error = "service not ready"

    while time.monotonic() < deadline:
        if process.poll() is not None:
            pytest.fail(
                f"Streamlit encerrou antes de ficar saudável. "
                f"exit_code={process.returncode}"
            )

        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                return response
            last_error = f"HTTP {response.status_code}"
        except requests.RequestException as exc:
            last_error = repr(exc)

        time.sleep(0.5)

    pytest.fail(f"Streamlit não ficou saudável: {last_error}")


@pytest.mark.smoke
def test_streamlit_smokey_external_http(tmp_path):
    port = _free_port()

    health_url = f"http://127.0.0.1:{port}/_stcore/health"
    root_url = f"http://127.0.0.1:{port}/"

    log_path = tmp_path / "streamlit-smokey.log"

    env = os.environ.copy()
    env.pop("GEMINI_API_KEY", None)
    env.pop("GEMINI_MODEL", None)

    with log_path.open("w", encoding="utf-8") as log_file:
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                str(APP_PATH),
                "--server.headless=true",
                "--server.address=127.0.0.1",
                f"--server.port={port}",
                "--browser.gatherUsageStats=false",
            ],
            cwd=ROOT,
            env=env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
        )

        try:
            health = _wait_for_health(
                health_url,
                process,
            )

            assert health.text.strip().lower() == "ok"

            response = requests.get(
                root_url,
                timeout=5,
            )

            assert response.status_code == 200
            assert (
                "text/html"
                in response.headers.get(
                    "content-type",
                    "",
                ).lower()
            )
            assert process.poll() is None

        finally:
            process.terminate()

            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)

"""Measure the live console's browser first-audible frame.

Runs the real frontend in headless Chrome against the running car-live backend
and the warmed TTS service, and reports the features.js first_audio latency
(request time to the first scheduled buffer plus device latency) for several
clean broadcasts. A run counts as clean when the previous broadcast has
finished, so the measurement is not distorted by queued synthesis.

Usage:
    python scripts/measure_live_first_audio.py [--runs 3] [--limit-ms 2000]

Exits 0 only when every measured run is under --limit-ms.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.request

import websockets.sync.client as ws_client

FRONTEND_URL = "http://127.0.0.1:5173/index.html#studio"
SCRIPT = "第一句话，介绍今天的直播主题。第二句话，原本介绍续航表现。第三句话，最后说明购车政策。"
CHROME = "google-chrome"


class Chrome:
    def __init__(self, port: int):
        self.port = port
        self.process = subprocess.Popen(
            [CHROME, "--headless=new", "--no-sandbox", "--disable-gpu",
             f"--remote-debugging-port={port}",
             "--autoplay-policy=no-user-gesture-required",
             f"--user-data-dir=/tmp/chrome-first-audio-{port}", "about:blank"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        self.ws = None
        self._id = 0

    def connect(self) -> None:
        deadline = time.time() + 30
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/json/list", timeout=1) as response:
                    pages = [t for t in json.load(response) if t.get("type") == "page"]
                if pages:
                    self.ws = ws_client.connect(pages[0]["webSocketDebuggerUrl"], max_size=None, legacy=True)
                    return
            except Exception:
                pass
            time.sleep(0.5)
        raise RuntimeError("chrome did not expose a page target")

    def send(self, method: str, **params):
        self._id += 1
        self.ws.send(json.dumps({"id": self._id, "method": method, "params": params}))
        while True:
            message = json.loads(self.ws.recv())
            if message.get("id") == self._id:
                return message

    def eval(self, expression: str):
        result = self.send("Runtime.evaluate", expression=expression, returnByValue=True, userGesture=True)
        body = result.get("result", {})
        if "exceptionDetails" in body:
            raise RuntimeError(body["exceptionDetails"].get("text") or "evaluate failed")
        return body.get("result", {}).get("value")

    def wait(self, expression: str, timeout: float = 90) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                if self.eval(expression):
                    return True
            except Exception:
                pass
            time.sleep(0.25)
        return False

    def close(self) -> None:
        try:
            if self.ws is not None:
                self.ws.close()
        finally:
            self.process.terminate()


def measure(runs: int) -> list[int]:
    chrome = Chrome(9231)
    try:
        chrome.connect()
        chrome.send("Page.enable")
        chrome.send("Runtime.enable")
        chrome.send("Page.navigate", url=FRONTEND_URL)
        if not chrome.wait("document.readyState==='complete' && !!document.querySelector('#play')"):
            raise RuntimeError("studio view did not load")
        chrome.eval(
            "window.__fa=[];(function(){const f=window.CarLiveFeatures;if(!f||f.__wrapped)return;"
            "const orig=f.audioScheduled;f.audioScheduled=function(run,source,when){try{"
            "window.__fa.push(Math.round(Math.max(0, performance.now()-run.requestedAt+"
            "(when-audioCtx.currentTime+(audioCtx.baseLatency||0)+(audioCtx.outputLatency||0))*1000)));"
            "}catch(e){}return orig.apply(this,arguments);};f.__wrapped=true;})();"
        )
        values: list[int] = []
        for _ in range(runs):
            chrome.eval("document.querySelector('#stop').click()")
            time.sleep(2.5)  # let the previous generation worker drain
            chrome.eval(f"document.querySelector('#script').value={SCRIPT!r}")
            before = chrome.eval("window.__fa.length")
            chrome.eval("document.querySelector('#play').click()")
            if not chrome.wait(f"window.__fa.length>{before}", 60):
                raise RuntimeError("no first-audio sample was recorded")
            values.append(int(chrome.eval(f"window.__fa[{before}]")))
            chrome.wait("document.querySelector('#playstate').textContent.includes('完成') || !liveRun", 90)
            time.sleep(1.0)
        return values
    finally:
        chrome.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--limit-ms", type=int, default=2000)
    args = parser.parse_args()
    try:
        values = measure(args.runs)
    except Exception as exc:  # noqa: BLE001 - report the real blocker and fail the check
        print(f"live first-audio measurement failed: {type(exc).__name__}: {exc}")
        return 1
    print(f"browser first-audible frame ms: {values} (limit {args.limit_ms} ms)")
    return 0 if values and all(value < args.limit_ms for value in values) else 1


if __name__ == "__main__":
    sys.exit(main())

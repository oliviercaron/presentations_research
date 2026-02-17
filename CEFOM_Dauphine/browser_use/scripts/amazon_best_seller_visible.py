#!/usr/bin/env python3
# ------------------------------------------------------------
# Amazon Best Sellers (Books) demo using browser_use (VISIBLE)
# - Opens Amazon Best Sellers (Books)
# - Finds rank #1
# - Opens the product page
# - Stops (does NOT add to cart or sign in)
# ------------------------------------------------------------

import asyncio
import json
import os
import socket
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.request import urlopen

from dotenv import load_dotenv
from browser_use import Agent, Browser, ChatOpenAI


async def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    load_dotenv(repo_root / ".env")
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY missing in browser_use/.env")

    # Optional: attach to an existing Chrome with remote debugging.
    cdp_url = os.getenv("BROWSER_USE_CDP_URL")

    # Optional: force a specific Chromium binary.
    executable_path = os.getenv("BROWSER_USE_EXECUTABLE_PATH")
    if not executable_path:
        candidates = []
        if os.name == "nt":
            candidates.extend(
                [
                    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
                    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
                    Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe",
                ]
            )
        else:
            candidates.extend(
                [
                    repo_root / ".pw-browsers/chromium-1200/chrome-linux64/chrome",
                    repo_root
                    / ".pw-browsers/chromium_headless_shell-1200/chrome-headless-shell-linux64/chrome-headless-shell",
                    Path("/usr/bin/google-chrome"),
                    Path("/usr/bin/chromium"),
                    Path("/usr/bin/chromium-browser"),
                ]
            )

        # Try Playwright-style cache under repo_root/.pw-browsers
        pw_root = repo_root / ".pw-browsers"
        if pw_root.exists():
            for exe in pw_root.rglob("chrome.exe" if os.name == "nt" else "chrome"):
                candidates.append(exe)
            for exe in pw_root.rglob("chrome-headless-shell.exe" if os.name == "nt" else "chrome-headless-shell"):
                candidates.append(exe)

        for candidate in candidates:
            if candidate.exists():
                executable_path = str(candidate)
                break

    # Launch a visible browser if no CDP URL is provided.
    chrome_proc = None
    if not cdp_url:
        if not executable_path:
            raise RuntimeError(
                "No Chromium executable found. Set BROWSER_USE_EXECUTABLE_PATH or install a browser."
            )

        def find_free_port() -> int:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", 0))
                return s.getsockname()[1]

        port = find_free_port()
        cdp_url = f"http://127.0.0.1:{port}"

        user_data_dir = Path(tempfile.mkdtemp(prefix="chrome-devtools-visible-"))
        chrome_cmd = [
            executable_path,
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--no-first-run",
            "--no-default-browser-check",
            f"--user-data-dir={user_data_dir}",
            f"--remote-debugging-port={port}",
            "about:blank",
        ]
        chrome_proc = subprocess.Popen(
            chrome_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Wait for CDP to be ready
        deadline = time.time() + 10
        while time.time() < deadline:
            try:
                with urlopen(f"http://127.0.0.1:{port}/json/version", timeout=1) as r:
                    json.load(r)
                break
            except Exception:
                time.sleep(0.2)
        else:
            chrome_proc.kill()
            raise RuntimeError("Failed to start visible Chromium (CDP not ready).")

    # Visible mode when possible (requires WSLg or X server).
    headless = False

    browser = Browser(
        cdp_url=cdp_url,
        executable_path=executable_path,
        headless=headless,
        chromium_sandbox=False,
        args=[
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
        ],
        window_size={"width": 1440, "height": 900},
        keep_alive=False,
        highlight_elements=True,
        wait_between_actions=0.8,
        record_video_dir=str(repo_root / "videos"),
    )

    llm = ChatOpenAI(model="gpt-5-nano")

    task = (
        "Open https://www.amazon.com/Best-Sellers-Books/zgbs/books/ . "
        "Find the #1 best-selling book (rank 1). "
        "Click it to open its product page. "
        "Stop there and report the title. "
        "If a cookie or location dialog appears, close or dismiss it. "
        "Do NOT sign in and do NOT add anything to cart."
    )

    system_hint = (
        "Never add items to cart, never sign in, never start checkout. "
        "Only navigate to the Best Sellers page and open the rank #1 product page. "
        "If blocked by a captcha, stop and report that a captcha appeared."
    )

    agent = Agent(
        task=task,
        llm=llm,
        browser=browser,
        use_vision=False,
        extend_system_message=system_hint,
    )

    history = await agent.run(max_steps=30)
    final_text = history.final_result() or "No final result."
    print(final_text)

    # Keep the browser visible for a short time.
    await asyncio.sleep(60)

    await agent.close()
    if chrome_proc is not None:
        chrome_proc.kill()


if __name__ == "__main__":
    asyncio.run(main())

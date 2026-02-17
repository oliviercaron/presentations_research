#!/usr/bin/env python3
# ------------------------------------------------------------
# Amazon Best Sellers (Books) demo using browser_use
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
import time
from pathlib import Path
from urllib.request import urlopen

from dotenv import load_dotenv
from browser_use import Agent, Browser, ChatOpenAI


async def main() -> None:
    repo_root = Path("/mnt/c/Users/Olivier/Documents/GitHub/python_experiments/browser_use")
    load_dotenv(repo_root / ".env")
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY missing in browser_use/.env")

    # If you already launched a Chrome with --remote-debugging-port,
    # set BROWSER_USE_CDP_URL="http://127.0.0.1:9222" to attach to it.
    cdp_url = os.getenv("BROWSER_USE_CDP_URL")

    # Optional: force a specific Chromium binary (useful in WSL).
    executable_path = os.getenv("BROWSER_USE_EXECUTABLE_PATH")
    if not executable_path:
        candidates = [
            repo_root / ".pw-browsers/chromium-1200/chrome-linux64/chrome",
            repo_root
            / ".pw-browsers/chromium_headless_shell-1200/chrome-headless-shell-linux64/chrome-headless-shell",
        ]
        for candidate in candidates:
            if candidate.exists():
                executable_path = str(candidate)
                break

    # Headless avoids display issues in WSL when launching locally.
    headless = True if not cdp_url else None

    # If no CDP URL was provided, start a local headless Chromium with a random port.
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

        chrome_cmd = [
            executable_path,
            "--headless",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--no-first-run",
            "--no-default-browser-check",
            f"--user-data-dir=/tmp/chrome-devtools-{port}",
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
            raise RuntimeError("Failed to start local Chromium (CDP not ready).")
    # No manual interaction in headless mode.
    post_run_pause_sec = 0
    max_steps = 30

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
        highlight_elements=False,
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

    history = await agent.run(max_steps=max_steps)
    final_text = history.final_result() or "No final result."
    print(final_text)

    if post_run_pause_sec > 0:
        print(f"Keeping browser open for {post_run_pause_sec}s for manual actions...")
        await asyncio.sleep(post_run_pause_sec)

    await agent.close()
    if chrome_proc is not None:
        chrome_proc.kill()


if __name__ == "__main__":
    asyncio.run(main())

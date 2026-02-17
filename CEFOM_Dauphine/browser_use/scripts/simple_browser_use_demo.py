#!/usr/bin/env python3

# ============================================================
# Browser Use demo (simple Python script)
# ============================================================
# Goal:
# - Open the page: https://books.toscrape.com/catalogue/page-41.html
# - Read each book title + its star rating (One/Two/Three/Four/Five)
# - Print the highest rating and the titles with that rating
# - Let you *see* the browser moving (demo mode)
#
# Why your previous run said "p.star-rating not found":
# - The default "extract" tool reads a simplified page snapshot
#   that often drops HTML class attributes (like "p.star-rating Five").
# - So the extractor cannot see the star-rating classes, even though
#   they exist in the real DOM.
#
# Fix used here (still simple):
# - We explicitly tell the agent to use the "evaluate" action.
# - "evaluate" runs JavaScript *inside the page* and can read class names.
#
# LLM choice:
# - You asked for gpt-5-nano, so we use that model.
# - We keep use_vision=False (text-only) to avoid needing a vision model.
#   This is OK because we read ratings from DOM class names, not from images.
#
# Visibility (demo):
# - headless=False means you will see the browser window moving.
# - If you *really* want headless=True, change the constant below,
#   but then you will NOT see the browser.
# ============================================================

import asyncio
import os
import re
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from browser_use import Agent, Browser, ChatOpenAI


async def main() -> None:
    # ---- Load API key from .env ----
    # The agent + LLM need OPENAI_API_KEY.
    repo_root = Path(__file__).resolve().parents[1]
    load_dotenv(repo_root / ".env")
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is missing. Put it in .env at repo root.")

    # ---- Choose whether the browser is visible ----
    # False = visible (demo); True = headless (no window)
    HEADLESS = False
    # Keep the browser open after the run.
    # For a clean exit, keep this False and use POST_RUN_PAUSE_SEC instead.
    KEEP_BROWSER_OPEN = False
    # Optional pause after the agent finishes, so you can see the final state.
    POST_RUN_PAUSE_SEC = 2.0
    # Small step budget to avoid agent loops.
    MAX_STEPS = 20

    # ---- Create the Browser Use browser ----
    # keep_alive=True keeps the window open after the run (useful for demo).
    # highlight_elements=True draws visible boxes/labels on elements the agent interacts with.
    # wait_between_actions slows the agent so the demo is easy to follow.
    # record_video_dir saves a video so you can replay the demo.
    video_dir = repo_root / "videos"
    video_dir.mkdir(parents=True, exist_ok=True)
    browser = Browser(
        headless=HEADLESS,
        window_size={"width": 1440, "height": 900},
        keep_alive=KEEP_BROWSER_OPEN,
        highlight_elements=True,
        wait_between_actions=0.8,
        record_video_dir=str(video_dir),
    )

    # ---- Create the LLM client ----
    # This is the exact model you requested.
    llm = ChatOpenAI(model="gpt-5-nano")

    # ---- Task ----
    # You asked for a minimal prompt: only the site URL and the request.
    task = (
        "Open https://books.toscrape.com/ and find the book or books with the highest "
        "star rating on page 41. Return only the title(s)."
    )

    # ---- Save the LLM conversation (full prompts + outputs) ----
    # Browser Use writes one text file per step; we will merge them into one MD file.
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    conv_dir = repo_root / "conversations" / f"run_{run_id}"
    conv_dir.mkdir(parents=True, exist_ok=True)
    conv_md = conv_dir / "conversation.md"

    # ---- Extend the default system message ----
    # We keep the user prompt minimal, but add a system hint that forces
    # a DOM-level evaluation if ratings are not visible in "extract".
    system_hint = (
        "On page 41, use evaluate once to read p.star-rating classes and titles, then answer. "
        "Do not repeat the same extract query multiple times. "
        "After evaluate, return only the title(s) with the highest rating and finish. "
        "If evaluate finds no ratings, report that ratings are unavailable on page 41 and finish."
    )

    # ---- Create and run the agent ----
    agent = Agent(
        task=task,
        llm=llm,
        browser=browser,
        use_vision=False,
        extend_system_message=system_hint,
        save_conversation_path=str(conv_dir),
    )

    history = await agent.run(max_steps=MAX_STEPS)

    # ---- Merge per-step conversation files into one Markdown file ----
    # This gives you a single readable file with all steps in order.
    def step_key(path: Path) -> int:
        match = re.search(r"_(\d+)\\.txt$", path.name)
        return int(match.group(1)) if match else 0

    conv_files = sorted(conv_dir.glob("conversation_*.txt"), key=step_key)
    lines = [
        "# Browser Use conversation",
        f"_Run folder: {conv_dir.name}_",
        "",
    ]
    for fpath in conv_files:
        step_num = step_key(fpath)
        content = fpath.read_text(encoding="utf-8", errors="replace").strip()
        lines.append(f"## Step {step_num}")
        lines.append(f"**Source file:** `{fpath.name}`")
        lines.append("")
        lines.append("```text")
        lines.append(content)
        lines.append("```")
        lines.append("")
    conv_md.write_text("\n".join(lines), encoding="utf-8")

    print(f"Conversation saved to: {conv_md}")
    final_text = history.final_result() or "No final result."
    print(final_text)

    # Optional pause, then cleanup to avoid hanging processes.
    if POST_RUN_PAUSE_SEC > 0:
        await asyncio.sleep(POST_RUN_PAUSE_SEC)
    await agent.close()


if __name__ == "__main__":
    asyncio.run(main())

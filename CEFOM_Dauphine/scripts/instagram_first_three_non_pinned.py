from __future__ import annotations

import argparse
import json
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import instaloader
import requests

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
)


def _safe_filename(name: str) -> str:
    # Keep it readable while avoiding problematic filesystem characters.
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("_")
    return cleaned or "post"


def _load_session_if_available(loader: instaloader.Instaloader, login_user: Optional[str]) -> None:
    if not login_user:
        return
    session_path = Path.home() / ".config" / "instaloader" / f"session-{login_user}"
    if session_path.exists():
        loader.load_session_from_file(login_user)


@dataclass
class MediaItem:
    index: int
    kind: str
    is_video: bool
    url: str
    filename: str


def _media_items(post: instaloader.Post) -> List[MediaItem]:
    items: List[MediaItem] = []

    if post.typename == "GraphSidecar":
        for i, node in enumerate(post.get_sidecar_nodes(), start=1):
            is_video = bool(node.is_video)
            url = node.video_url if is_video else node.display_url
            ext = "mp4" if is_video else "jpg"
            items.append(
                MediaItem(index=i, kind="sidecar", is_video=is_video, url=url, filename=f"media_{i:02d}.{ext}")
            )
        return items

    if post.typename == "GraphVideo":
        items.append(MediaItem(index=1, kind="video", is_video=True, url=post.video_url, filename="media_01.mp4"))
        return items

    items.append(MediaItem(index=1, kind="image", is_video=False, url=post.url, filename="media_01.jpg"))
    return items


def _download_file(url: str, dest: Path) -> None:
    headers = {"user-agent": USER_AGENT, "referer": "https://www.instagram.com/"}
    with requests.get(url, headers=headers, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 64):
                if chunk:
                    f.write(chunk)


def _extract_comments(post: instaloader.Post, max_comments: Optional[int]) -> Dict[str, Any]:
    comments: List[Dict[str, Any]] = []
    error: Optional[str] = None

    try:
        iterator = post.get_comments()
        for idx, comment in enumerate(iterator, start=1):
            comments.append(
                {
                    "id": comment.id,
                    "created_at_utc": comment.created_at_utc.isoformat(),
                    "owner_username": getattr(comment.owner, "username", None),
                    "text": comment.text,
                    "likes_count": comment.likes_count,
                    "parent_id": comment.parent_id,
                }
            )
            if max_comments is not None and idx >= max_comments:
                break
    except Exception as exc:  # noqa: BLE001 - we want to capture the failure reason
        error = f"comments_unavailable: {type(exc).__name__}: {exc}"

    return {
        "count_collected": len(comments),
        "max_comments": max_comments,
        "error": error,
        "items": comments,
    }


def _post_metadata(post: instaloader.Post) -> Dict[str, Any]:
    caption = (post.caption or "").strip()
    return {
        "shortcode": post.shortcode,
        "url": f"https://www.instagram.com/p/{post.shortcode}/",
        "date_utc": post.date_utc.isoformat(),
        "typename": post.typename,
        "is_pinned": bool(getattr(post, "is_pinned", False)),
        "caption": caption,
        "likes": post.likes,
        "comments": post.comments,
    }


def _first_non_pinned_posts(profile: instaloader.Profile, limit: int) -> List[instaloader.Post]:
    posts: List[instaloader.Post] = []
    for post in profile.get_posts():
        if getattr(post, "is_pinned", False):
            continue
        posts.append(post)
        if len(posts) >= limit:
            break
    if not posts:
        raise RuntimeError("Aucun post non épinglé trouvé.")
    return posts


def run(username: str, limit: int, login_user: Optional[str], max_comments: Optional[int], sleep_s: float) -> Path:
    loader = instaloader.Instaloader(
        quiet=True,
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
    )
    _load_session_if_available(loader, login_user=login_user)

    profile = instaloader.Profile.from_username(loader.context, username)
    posts = _first_non_pinned_posts(profile, limit=limit)

    root_dir = Path("/home/olivier") / username
    root_dir.mkdir(parents=True, exist_ok=True)

    summary: List[Dict[str, Any]] = []

    for i, post in enumerate(posts, start=1):
        meta = _post_metadata(post)
        post_dir_name = f"{i:02d}_{_safe_filename(post.shortcode)}"
        post_dir = root_dir / post_dir_name
        post_dir.mkdir(parents=True, exist_ok=True)

        media_items = _media_items(post)
        for item in media_items:
            dest = post_dir / item.filename
            try:
                _download_file(item.url, dest)
                status = "downloaded"
            except Exception as exc:  # noqa: BLE001
                status = f"download_failed: {type(exc).__name__}: {exc}"
            summary.append(
                {
                    "post_index": i,
                    "shortcode": post.shortcode,
                    "media_index": item.index,
                    "media_kind": item.kind,
                    "is_video": item.is_video,
                    "media_url": item.url,
                    "file": str(dest),
                    "status": status,
                }
            )
            time.sleep(sleep_s)

        comments_payload = _extract_comments(post, max_comments=max_comments)

        (post_dir / "metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        (post_dir / "media.json").write_text(
            json.dumps([asdict(m) for m in media_items], ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (post_dir / "comments.json").write_text(
            json.dumps(comments_payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        time.sleep(sleep_s)

    (root_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return root_dir


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Télécharge les médias et tente d'extraire les commentaires des 3 premiers posts non épinglés. "
            "Organisation: /home/olivier/<username>/"
        )
    )
    parser.add_argument("username", nargs="?", default="fast_train_driver")
    parser.add_argument("--limit", type=int, default=3, help="Nombre de posts non épinglés (défaut: 3).")
    parser.add_argument(
        "--login-user",
        dest="login_user",
        default=None,
        help="Nom d'utilisateur Instagram pour charger une session Instaloader existante.",
    )
    parser.add_argument(
        "--max-comments",
        dest="max_comments",
        type=int,
        default=100,
        help="Nombre max de commentaires par post (défaut: 100).",
    )
    parser.add_argument(
        "--sleep",
        dest="sleep_s",
        type=float,
        default=1.0,
        help="Délai entre requêtes (défaut: 1.0s).",
    )
    args = parser.parse_args()

    root_dir = run(
        username=args.username,
        limit=max(1, args.limit),
        login_user=args.login_user,
        max_comments=args.max_comments,
        sleep_s=max(0.0, args.sleep_s),
    )

    print(f"Sortie: {root_dir}")
    print("Contenu:")
    for path in sorted(root_dir.glob("*")):
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

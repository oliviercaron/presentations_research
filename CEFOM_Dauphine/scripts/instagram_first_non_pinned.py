from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import instaloader


@dataclass
class MediaItem:
    index: int
    is_video: bool
    url: str
    kind: str


def _load_session_if_available(loader: instaloader.Instaloader, login_user: Optional[str]) -> None:
    if not login_user:
        return
    session_path = Path.home() / ".config" / "instaloader" / f"session-{login_user}"
    if session_path.exists():
        loader.load_session_from_file(login_user)


def _extract_media(post: instaloader.Post) -> List[MediaItem]:
    items: List[MediaItem] = []

    if post.typename == "GraphSidecar":
        for i, node in enumerate(post.get_sidecar_nodes(), start=1):
            is_video = bool(node.is_video)
            url = node.video_url if is_video else node.display_url
            items.append(MediaItem(index=i, is_video=is_video, url=url, kind="sidecar"))
        return items

    if post.typename == "GraphVideo":
        items.append(MediaItem(index=1, is_video=True, url=post.video_url, kind="video"))
        return items

    items.append(MediaItem(index=1, is_video=False, url=post.url, kind="image"))
    return items


def _first_non_pinned_post(profile: instaloader.Profile) -> instaloader.Post:
    for post in profile.get_posts():
        if not getattr(post, "is_pinned", False):
            return post
    raise RuntimeError("Aucun post non épinglé trouvé.")


def run(target_username: str, login_user: Optional[str]) -> Dict[str, Any]:
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

    profile = instaloader.Profile.from_username(loader.context, target_username)
    post = _first_non_pinned_post(profile)

    media = _extract_media(post)
    caption = (post.caption or "").strip()

    return {
        "username": target_username,
        "shortcode": post.shortcode,
        "url": f"https://www.instagram.com/p/{post.shortcode}/",
        "date_utc": post.date_utc.isoformat(),
        "is_pinned": bool(getattr(post, "is_pinned", False)),
        "typename": post.typename,
        "caption": caption,
        "media": [item.__dict__ for item in media],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Récupère le 1er post non épinglé d'un profil Instagram et liste ses médias. "
            "Si besoin d'auth, crée d'abord une session: instaloader --login TON_USER"
        )
    )
    parser.add_argument("username", nargs="?", default="fast_train_driver")
    parser.add_argument(
        "--login-user",
        dest="login_user",
        default=None,
        help="Nom d'utilisateur Instagram pour charger une session Instaloader existante.",
    )
    args = parser.parse_args()

    result = run(target_username=args.username, login_user=args.login_user)

    print("Premier post non épinglé:")
    print(f"- Profil:     {result['username']}")
    print(f"- Shortcode:  {result['shortcode']}")
    print(f"- URL:        {result['url']}")
    print(f"- Date (UTC): {result['date_utc']}")
    print(f"- Type:       {result['typename']}")

    caption_preview = result["caption"][:200].replace("\n", " ")
    if caption_preview:
        suffix = "..." if len(result["caption"]) > 200 else ""
        print(f"- Caption:    {caption_preview}{suffix}")

    print("\nMédias:")
    for item in result["media"]:
        media_type = "video" if item["is_video"] else "image"
        print(f"- [{item['index']}] {media_type}: {item['url']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

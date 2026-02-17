from __future__ import annotations

import argparse
import re
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag

BASE_URL = "https://fr.trustpilot.com/review/www.carrefour.fr"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
)

RATING_RE = re.compile(r"(\d+(?:[\.,]\d+)?)")


@dataclass
class ScrapeConfig:
    pages: int
    delay_seconds: float


def _parse_rating(alt_text: Optional[str]) -> Optional[float]:
    if not alt_text:
        return None
    match = RATING_RE.search(alt_text)
    if not match:
        return None
    return float(match.group(1).replace(",", "."))


def _clean_text(text: Optional[str]) -> Optional[str]:
    if not text:
        return text
    # Trustpilot appends "Voir plus" to truncated snippets.
    return text.replace("Voir plus", "").strip()


def _is_carousel_card(article: Tag) -> bool:
    classes = " ".join(article.get("class", []))
    return "carousel" in classes.lower()


def _extract_review(article: Tag, page: int) -> Dict[str, Any]:
    name_el = article.select_one('[data-consumer-name-typography="true"]')
    time_el = article.select_one("time[datetime]")
    rating_img = article.find("img", alt=re.compile(r"Not[eé]"))
    link_el = article.select_one('a[href^="/reviews/"]')
    title_el = article.select_one('a[href^="/reviews/"] h2') or article.select_one("h2")
    text_el = article.select_one('[data-service-review-text-typography="true"]') or article.select_one(
        '[data-relevant-review-text-typography="true"]'
    )

    author_name = name_el.get_text(strip=True) if name_el else None
    rating = _parse_rating(rating_img.get("alt") if rating_img else None)
    review_title = title_el.get_text(strip=True) if title_el else None
    review_text = _clean_text(text_el.get_text(" ", strip=True) if text_el else None)
    review_date = time_el.get("datetime") if time_el else None
    review_url = urljoin(BASE_URL, link_el.get("href")) if link_el else None

    return {
        "page": page,
        "author_name": author_name,
        "rating": rating,
        "review_date": review_date,
        "review_title": review_title,
        "review_text": review_text,
        "review_url": review_url,
    }


def _fetch_page(session: requests.Session, page: int) -> List[Dict[str, Any]]:
    headers = {
        "user-agent": USER_AGENT,
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "accept-language": "fr-FR,fr;q=0.9,en;q=0.8",
        "referer": BASE_URL,
    }
    resp = session.get(BASE_URL, params={"page": page}, headers=headers, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "lxml")
    articles: Iterable[Tag] = (
        article
        for article in soup.select('article[data-service-review-card-paper="true"]')
        if not _is_carousel_card(article)
    )

    rows = [_extract_review(article, page=page) for article in articles]
    # Filter out obviously empty rows if the markup changes.
    return [row for row in rows if row.get("author_name") and row.get("review_text")]


def fetch_reviews_to_dataframe(config: ScrapeConfig) -> pd.DataFrame:
    session = requests.Session()
    all_rows: List[Dict[str, Any]] = []

    for page in range(1, config.pages + 1):
        rows = _fetch_page(session, page=page)
        if not rows:
            break
        all_rows.extend(rows)
        time.sleep(config.delay_seconds)

    df = pd.DataFrame(all_rows)
    if df.empty:
        return df

    return df[
        [
            "page",
            "author_name",
            "rating",
            "review_date",
            "review_title",
            "review_text",
            "review_url",
        ]
    ]


def _configure_pandas_display() -> None:
    pd.set_option("display.max_rows", None)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 180)
    pd.set_option("display.max_colwidth", 140)
    pd.set_option("display.expand_frame_repr", False)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Récupère les avis Trustpilot FR de Carrefour et les affiche en DataFrame. "
            "Par défaut, scrape 3 pages pour rester raisonnable."
        )
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=3,
        help="Nombre de pages à scraper (défaut: 3).",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Délai (secondes) entre pages pour être poli (défaut: 1.0).",
    )

    args = parser.parse_args(argv)

    if args.pages < 1:
        print("--pages doit être >= 1", file=sys.stderr)
        return 2

    _configure_pandas_display()

    config = ScrapeConfig(pages=args.pages, delay_seconds=args.delay)
    df = fetch_reviews_to_dataframe(config)

    if df.empty:
        print("Aucun avis extrait (possible changement de markup / blocage).")
        return 1

    print(df)
    print(f"\nTotal avis extraits: {len(df)} (pages: {args.pages})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import sys
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd
import requests

API_URL = "https://quotes.toscrape.com/api/quotes"


def _normalize_quote(quote: Dict[str, Any], page: int, tag_filter: Optional[str]) -> Dict[str, Any]:
    author = quote.get("author", {}) or {}
    tags: Iterable[str] = quote.get("tags", []) or []
    return {
        "page": page,
        "tag_filter": tag_filter,
        "text": quote.get("text"),
        "author_name": author.get("name"),
        "author_slug": author.get("slug"),
        "author_goodreads_link": author.get("goodreads_link"),
        "tags": ",".join(tags),
    }


def fetch_quotes_to_dataframe(tag: Optional[str] = None) -> pd.DataFrame:
    session = requests.Session()
    page = 1
    rows: List[Dict[str, Any]] = []

    while True:
        params: Dict[str, Any] = {"page": page}
        if tag:
            params["tag"] = tag

        response = session.get(API_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        quotes = data.get("quotes", []) or []
        for quote in quotes:
            rows.append(_normalize_quote(quote, page=page, tag_filter=tag))

        if not data.get("has_next"):
            break
        page += 1

    df = pd.DataFrame(rows)
    # Order columns explicitly for readability in the console.
    return df[
        [
            "page",
            "tag_filter",
            "author_name",
            "author_slug",
            "author_goodreads_link",
            "tags",
            "text",
        ]
    ]


def main() -> None:
    tag = sys.argv[1] if len(sys.argv) > 1 else None

    pd.set_option("display.max_rows", None)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 160)
    pd.set_option("display.max_colwidth", 120)
    pd.set_option("display.expand_frame_repr", False)

    df = fetch_quotes_to_dataframe(tag=tag)
    print(df)
    print(f"\nTotal quotes: {len(df)}")


if __name__ == "__main__":
    main()

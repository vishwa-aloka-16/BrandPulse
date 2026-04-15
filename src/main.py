from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from extract.extractor import RedditExtractor
from load.analyzer import SentimentAnalyzer
from load.cleaner import clean_mentions
from transform.mysql_loader import MySQLLoader


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = ROOT_DIR / "config" / "brands.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the BrandPulse social ETL pipeline.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Path to brands JSON config.")
    parser.add_argument("--limit", type=int, default=int(os.getenv("REDDIT_LIMIT", "25")))
    parser.add_argument("--time-filter", default=os.getenv("REDDIT_TIME_FILTER", "week"))
    parser.add_argument("--sort", default=os.getenv("REDDIT_SORT", "new"))
    parser.add_argument("--dry-run", action="store_true", help="Print a summary without writing to MySQL.")
    args = parser.parse_args()

    load_dotenv(ROOT_DIR / ".env")
    config = _load_config(Path(args.config))

    extractor = RedditExtractor()
    analyzer = SentimentAnalyzer()
    all_rows: list[dict[str, object]] = []

    for brand_config in config["brands"]:
        brand = brand_config["name"]
        keywords = brand_config["keywords"]
        subreddits = brand_config.get("subreddits")

        mentions = extractor.search_brand(
            brand,
            keywords,
            subreddits=subreddits,
            limit=args.limit,
            time_filter=args.time_filter,
            sort=args.sort,
        )
        cleaned = clean_mentions(mentions)
        analyzed = analyzer.analyze(cleaned)
        all_rows.extend(analyzed)
        print(f"{brand}: extracted {len(mentions)} mentions, prepared {len(analyzed)} rows")

    if args.dry_run:
        print(f"Dry run complete. {len(all_rows)} rows are ready for loading.")
        _print_sample(all_rows)
        return

    affected_count = MySQLLoader().upsert_mentions(all_rows)
    print(f"Loaded {affected_count} affected rows into MySQL.")


def _load_config(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as file:
        config = json.load(file)

    brands = config.get("brands")
    if not isinstance(brands, list) or not brands:
        raise ValueError("Config must include a non-empty 'brands' list.")

    for brand in brands:
        if not brand.get("name") or not brand.get("keywords"):
            raise ValueError("Each brand must include 'name' and 'keywords'.")

    return config


def _print_sample(rows: list[dict[str, object]]) -> None:
    if not rows:
        return

    sample = rows[0]
    print("Sample row:")
    print(
        json.dumps(
            {
                "brand": sample["brand"],
                "keyword": sample["keyword"],
                "source": sample["source"],
                "title": sample["title"],
                "sentiment_label": sample["sentiment_label"],
                "sentiment_compound": sample["sentiment_compound"],
                "permalink": sample["permalink"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

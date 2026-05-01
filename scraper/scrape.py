from __future__ import annotations

import argparse
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urldefrag, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from rag.config import RAW_DIR
from settings import env_float, env_int, env_list


DEFAULT_START_URLS = [
    "https://debales.ai/",
    "https://debales.ai/blog",
    "https://debales.ai/integrations",
]

ALLOWED_DOMAIN = "debales.ai"
DEFAULT_MAX_PAGES = 80
REQUEST_TIMEOUT = 20


@dataclass(frozen=True)
class ScrapedPage:
    url: str
    title: str
    text: str


def normalize_url(url: str) -> str:
    clean_url, _fragment = urldefrag(url)
    parsed = urlparse(clean_url)
    if not parsed.scheme:
        clean_url = f"https://{clean_url}"
        parsed = urlparse(clean_url)
    path = parsed.path.rstrip("/") or "/"
    return parsed._replace(path=path, params="", query="").geturl()


def is_allowed_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and parsed.netloc.lower().endswith(ALLOWED_DOMAIN)


def slug_for_url(url: str) -> str:
    parsed = urlparse(url)
    raw = f"{parsed.netloc}{parsed.path}".strip("/")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", raw).strip("-").lower()
    return slug or "home"


def extract_text(html: str, url: str) -> ScrapedPage:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "iframe"]):
        tag.decompose()

    title = soup.title.get_text(" ", strip=True) if soup.title else url
    main = soup.find("main") or soup.body or soup
    text = main.get_text("\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    deduped_lines = list(dict.fromkeys(lines))
    return ScrapedPage(url=url, title=title, text="\n".join(deduped_lines))


def discover_links(html: str, base_url: str) -> set[str]:
    soup = BeautifulSoup(html, "html.parser")
    links: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if href.startswith(("mailto:", "tel:", "javascript:")):
            continue
        normalized = normalize_url(urljoin(base_url, href))
        if is_allowed_url(normalized):
            links.add(normalized)
    return links


def save_page(page: ScrapedPage, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{slug_for_url(page.url)}.txt"
    content = f"URL: {page.url}\nTITLE: {page.title}\n\n{page.text}\n"
    path.write_text(content, encoding="utf-8")
    return path


def scrape_site(
    start_urls: Iterable[str] = DEFAULT_START_URLS,
    output_dir: Path = RAW_DIR,
    max_pages: int = DEFAULT_MAX_PAGES,
    delay_seconds: float = 0.5,
) -> list[Path]:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "DebalesAIAgentBot/1.0 (+https://debales.ai/)",
            "Accept": "text/html,application/xhtml+xml",
        }
    )

    queue = [normalize_url(url) for url in start_urls]
    seen: set[str] = set()
    saved_paths: list[Path] = []

    while queue and len(seen) < max_pages:
        url = queue.pop(0)
        if url in seen or not is_allowed_url(url):
            continue
        seen.add(url)

        try:
            response = session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f"Skipping {url}: {exc}")
            continue

        content_type = response.headers.get("content-type", "")
        if "html" not in content_type.lower():
            continue

        page = extract_text(response.text, url)
        if page.text:
            saved_paths.append(save_page(page, output_dir))

        for link in sorted(discover_links(response.text, url)):
            if link not in seen and link not in queue:
                queue.append(link)

        time.sleep(delay_seconds)

    return saved_paths


def main() -> None:
    configured_urls = env_list("DEBALES_START_URLS", DEFAULT_START_URLS)
    parser = argparse.ArgumentParser(description="Scrape Debales AI pages into local text files.")
    parser.add_argument("--max-pages", type=int, default=env_int("SCRAPER_MAX_PAGES", DEFAULT_MAX_PAGES))
    parser.add_argument("--delay", type=float, default=env_float("SCRAPER_DELAY_SECONDS", 0.5))
    parser.add_argument("--output-dir", type=Path, default=RAW_DIR)
    parser.add_argument("urls", nargs="*", default=configured_urls)
    args = parser.parse_args()

    paths = scrape_site(
        start_urls=args.urls,
        output_dir=args.output_dir,
        max_pages=args.max_pages,
        delay_seconds=args.delay,
    )
    print(f"Saved {len(paths)} pages to {args.output_dir}")


if __name__ == "__main__":
    main()

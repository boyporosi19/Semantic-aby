"""
Scraper untuk CNN.com
Mengambil data berita terkini: judul, ringkasan, URL, dan kategori.
"""

import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def scrape_cnn() -> list[dict]:
    """
    Scrape berita dari CNN.com.

    Returns:
        List of dict berisi title, url, dan source_url
    """
    base_url = "https://edition.cnn.com"
    all_news = []
    seen_titles = set()

    try:
        response = requests.get(base_url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[CNN] Error fetching CNN: {e}")
        return all_news

    soup = BeautifulSoup(response.text, "lxml")

    # CNN uses various link patterns for articles
    for link in soup.find_all("a", href=True):
        href = link.get("href", "")
        text = link.get_text(strip=True)

        # Filter for article links
        if not text or len(text) < 20:
            continue

        # CNN article URLs typically contain date patterns like /2025/04/
        is_article = False
        if "/20" in href and ("/" in href.split("/20")[1] if "/20" in href else False):
            is_article = True
        elif href.startswith("/") and href.count("/") >= 3 and "index.html" in href:
            is_article = True

        if not is_article:
            continue

        # Normalize URL
        if href.startswith("/"):
            full_url = base_url + href
        elif href.startswith("http"):
            full_url = href
        else:
            continue

        # Deduplicate
        if text in seen_titles:
            continue
        seen_titles.add(text)

        # Extract category from URL path
        parts = href.strip("/").split("/")
        category = parts[0] if parts else "general"
        if category.startswith("20"):
            category = parts[1] if len(parts) > 1 else "general"

        all_news.append({
            "title": text,
            "url": full_url,
            "category": category,
            "source_url": base_url,
        })

    return all_news


if __name__ == "__main__":
    data = scrape_cnn()
    print(f"Scraped {len(data)} articles from CNN")
    for n in data[:5]:
        print(f"  - [{n['category']}] {n['title'][:70]}...")

import requests


HEADERS = {
    "User-Agent": "SemanticWebScraper/1.0 (Educational Project; Python/requests)",
}


def scrape_wikipedia(max_articles: int = 30) -> list[dict]:
    """
    Scrape artikel dari Wikipedia menggunakan API.

    Args:
        max_articles: Jumlah artikel yang diambil (default: 30)

    Returns:
        List of dict berisi title, summary, url, categories, source_url
    """
    api_url = "https://en.wikipedia.org/w/api.php"
    all_articles = []

    # Step 1: Get random article titles
    params_random = {
        "action": "query",
        "format": "json",
        "list": "random",
        "rnnamespace": 0,
        "rnlimit": max_articles,
    }

    try:
        response = requests.get(api_url, params=params_random, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as e:
        print(f"[Wikipedia] Error fetching random articles: {e}")
        return all_articles

    page_ids = [str(item["id"]) for item in data.get("query", {}).get("random", [])]

    if not page_ids:
        return all_articles

    # Step 2: Get details in batches of 20 (API limit)
    batch_size = 20
    for batch_start in range(0, len(page_ids), batch_size):
        batch_ids = page_ids[batch_start:batch_start + batch_size]

        params_details = {
            "action": "query",
            "format": "json",
            "pageids": "|".join(batch_ids),
            "prop": "extracts|categories|info",
            "exintro": True,
            "explaintext": True,
            "exsentences": 3,
            "cllimit": 5,
            "inprop": "url",
        }

        try:
            response = requests.get(api_url, params=params_details, headers=HEADERS, timeout=10)
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as e:
            print(f"[Wikipedia] Error fetching article details: {e}")
            continue

        pages = data.get("query", {}).get("pages", {})

        for page_id, page_data in pages.items():
            title = page_data.get("title", "")
            extract = page_data.get("extract", "")
            full_url = page_data.get("fullurl", f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}")

            categories = []
            for cat in page_data.get("categories", []):
                cat_title = cat.get("title", "").replace("Category:", "")
                if cat_title:
                    categories.append(cat_title)

            if title and extract:
                all_articles.append({
                    "title": title,
                    "summary": extract.strip()[:300],
                    "url": full_url,
                    "categories": categories,
                    "page_id": page_id,
                    "source_url": "https://en.wikipedia.org/",
                })

    return all_articles


if __name__ == "__main__":
    data = scrape_wikipedia()
    print(f"Scraped {len(data)} articles from Wikipedia")
    for a in data[:5]:
        print(f"  - {a['title']}: {a['summary'][:80]}...")

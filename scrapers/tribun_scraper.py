import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en;q=0.5",
}


def scrape_tribun() -> list[dict]:
    """
    Scrape berita dari tribunnews.com.

    Returns:
        List of dict berisi title, url, summary, category, date, source_url
    """
    urls_to_scrape = [
        "https://www.tribunnews.com/",
        "https://www.tribunnews.com/nasional",
        "https://www.tribunnews.com/internasional",
    ]
    all_news = []
    seen_titles = set()

    for page_url in urls_to_scrape:
        try:
            response = requests.get(page_url, headers=HEADERS, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"[Tribun] Error fetching {page_url}: {e}")
            continue

        soup = BeautifulSoup(response.text, "lxml")

        # Tribunnews article links
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            title = link.get_text(strip=True)

            if not title or len(title) < 15:
                continue

            # Filter for tribunnews article URLs
            if "tribunnews.com/" not in href:
                continue

            # Article URLs typically have a date pattern or /read/ or specific section paths
            is_article = False
            if "/20" in href and href.count("/") >= 4:
                is_article = True

            if not is_article:
                continue

            if title in seen_titles:
                continue
            seen_titles.add(title)

            # Normalize URL
            if href.startswith("/"):
                full_url = "https://www.tribunnews.com" + href
            else:
                full_url = href

            # Category from URL
            category = "umum"
            if "/nasional/" in href:
                category = "nasional"
            elif "/internasional/" in href:
                category = "internasional"
            elif "/bisnis/" in href:
                category = "bisnis"
            elif "/techno/" in href:
                category = "techno"
            elif "/superskor/" in href or "/sport/" in href:
                category = "olahraga"
            elif "/seleb/" in href:
                category = "seleb"
            elif "/kesehatan/" in href:
                category = "kesehatan"
            elif "/otomotif/" in href:
                category = "otomotif"
            elif "/travel/" in href:
                category = "travel"
            elif "/pendidikan/" in href:
                category = "pendidikan"

            # Try to find summary from parent
            parent = link.find_parent(["div", "li", "article"])
            summary = ""
            if parent:
                p_elem = parent.find("p")
                if p_elem:
                    summary = p_elem.get_text(strip=True)[:200]

            # Date
            parent = link.parent
            date = ""
            for _ in range(4):
                if not parent or parent.name == "body": break
                time_elem = parent.find("time")
                if not time_elem: time_elem = parent.find("div", class_=lambda c: c and "date" in str(c).lower())
                if not time_elem: time_elem = parent.find("span", class_=lambda c: c and "date" in str(c).lower())
                if time_elem:
                    date = time_elem.get_text(strip=True)
                    break
                parent = parent.parent

            all_news.append({
                "title": title,
                "url": full_url,
                "summary": summary,
                "category": category,
                "date": date,
                "source_url": page_url,
            })

    return all_news


if __name__ == "__main__":
    data = scrape_tribun()
    print(f"Scraped {len(data)} articles from Tribunnews")
    for n in data[:5]:
        print(f"  - [{n['category']}] {n['title'][:70]}...")

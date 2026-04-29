"""
Scraper untuk detik.com
Mengambil data berita terkini: judul, ringkasan, URL, kategori, dan tanggal.
"""

import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en;q=0.5",
}


def scrape_detik() -> list[dict]:
    """
    Scrape berita dari detik.com.

    Returns:
        List of dict berisi title, url, summary, category, date, source_url
    """
    urls_to_scrape = [
        "https://www.detik.com/terpopuler",
        "https://news.detik.com/",
        "https://finance.detik.com/",
    ]
    all_news = []
    seen_titles = set()

    for page_url in urls_to_scrape:
        try:
            response = requests.get(page_url, headers=HEADERS, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"[Detik] Error fetching {page_url}: {e}")
            continue

        soup = BeautifulSoup(response.text, "lxml")

        # Detik uses various article containers
        articles = soup.find_all("article")
        if not articles:
            # Fallback: find links that look like articles
            articles = soup.find_all("div", class_=lambda c: c and ("media" in c.lower() or "list" in c.lower() or "article" in c.lower()))

        for article in articles:
            link = article.find("a", href=True)
            if not link:
                continue

            href = link.get("href", "")
            title_elem = article.find(["h2", "h3", "h4"]) or link
            title = title_elem.get_text(strip=True)

            if not title or len(title) < 10 or title in seen_titles:
                continue

            # Filter for detik article URLs
            if "detik.com" not in href:
                continue

            seen_titles.add(title)

            # Summary
            summary_elem = article.find("p") or article.find("span", class_=lambda c: c and "detail" in str(c).lower())
            summary = summary_elem.get_text(strip=True) if summary_elem else ""

            # Date
            parent = link.parent
            date = ""
            for _ in range(4):
                if not parent or parent.name == "body": break
                date_elem = parent.find("div", class_=lambda c: c and ("date" in str(c).lower() or "time" in str(c).lower()))
                if not date_elem: date_elem = parent.find("span", class_=lambda c: c and ("date" in str(c).lower() or "time" in str(c).lower()))
                if not date_elem: date_elem = parent.find("time")
                if date_elem:
                    date = date_elem.get_text(strip=True)
                    break
                parent = parent.parent

            # Category from URL
            category = "umum"
            if "news.detik" in href:
                category = "news"
            elif "finance.detik" in href:
                category = "finance"
            elif "sport.detik" in href:
                category = "sport"
            elif "hot.detik" in href:
                category = "entertainment"
            elif "inet.detik" in href:
                category = "tech"
            elif "food.detik" in href:
                category = "food"
            elif "health.detik" in href:
                category = "health"

            all_news.append({
                "title": title,
                "url": href,
                "summary": summary[:200] if summary else "",
                "category": category,
                "date": date,
                "source_url": page_url,
            })

    return all_news


if __name__ == "__main__":
    data = scrape_detik()
    print(f"Scraped {len(data)} articles from Detik")
    for n in data[:5]:
        print(f"  - [{n['category']}] {n['title'][:70]}...")

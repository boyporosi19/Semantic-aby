import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en;q=0.5",
}


def scrape_kompas() -> list[dict]:
    """
    Scrape berita dari kompas.com.

    Returns:
        List of dict berisi title, url, summary, category, date, source_url
    """
    urls_to_scrape = [
        "https://news.kompas.com/",
        "https://www.kompas.com/tren",
        "https://tekno.kompas.com/",
    ]
    all_news = []
    seen_titles = set()

    for page_url in urls_to_scrape:
        try:
            response = requests.get(page_url, headers=HEADERS, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"[Kompas] Error fetching {page_url}: {e}")
            continue

        soup = BeautifulSoup(response.text, "lxml")

        # Kompas uses various article containers
        article_links = soup.find_all("a", class_=lambda c: c and ("headline" in str(c).lower() or "article" in str(c).lower() or "latest" in str(c).lower()))

        # Also find h2/h3 within article containers
        if not article_links:
            for heading in soup.find_all(["h2", "h3", "h4"]):
                link = heading.find("a", href=True)
                if link:
                    article_links.append(link)

        # Broader search for article links
        if len(article_links) < 5:
            for link in soup.find_all("a", href=True):
                href = link.get("href", "")
                text = link.get_text(strip=True)
                if "kompas.com/read/" in href and text and len(text) > 15:
                    article_links.append(link)

        for link in article_links:
            href = link.get("href", "")
            title = link.get_text(strip=True)

            if not title or len(title) < 10 or title in seen_titles:
                continue

            if "kompas.com" not in href:
                continue

            seen_titles.add(title)

            # Category from URL
            category = "umum"
            if "news.kompas" in href:
                category = "news"
            elif "tekno.kompas" in href:
                category = "tekno"
            elif "megapolitan.kompas" in href:
                category = "megapolitan"
            elif "regional.kompas" in href:
                category = "regional"
            elif "money.kompas" in href:
                category = "ekonomi"
            elif "nasional.kompas" in href:
                category = "nasional"
            elif "internasional.kompas" in href:
                category = "internasional"
            elif "entertainment.kompas" in href:
                category = "entertainment"
            elif "bola.kompas" in href:
                category = "bola"
            elif "sains.kompas" in href:
                category = "sains"

            # Try to find date
            parent = link.parent
            date = ""
            for _ in range(4):
                if not parent or parent.name == "body": break
                date_elem = parent.find("div", class_=lambda c: c and "date" in str(c).lower())
                if not date_elem: date_elem = parent.find("span", class_=lambda c: c and "date" in str(c).lower())
                if not date_elem: date_elem = parent.find("time")
                if date_elem:
                    date = date_elem.get_text(strip=True)
                    break
                parent = parent.parent

            all_news.append({
                "title": title,
                "url": href,
                "summary": "",
                "category": category,
                "date": date,
                "source_url": page_url,
            })

    return all_news


if __name__ == "__main__":
    data = scrape_kompas()
    print(f"Scraped {len(data)} articles from Kompas")
    for n in data[:5]:
        print(f"  - [{n['category']}] {n['title'][:70]}...")

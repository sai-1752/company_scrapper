import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime
import json
import re

HEADERS = {"User-Agent": "Mozilla/5.0"}

PRIORITY_PATHS = [
    "/about", "/company", "/products", "/solutions",
    "/industries", "/pricing", "/careers", "/contact"
]

def fetch_page(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.text, None
    except Exception as e:
        return None, str(e)

def extract_emails(text):
    return list(set(re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)))

def extract_phones(text):
    return list(set(re.findall(r"\+?\d[\d\s\-]{8,15}", text)))

def scrape_website(base_url):
    visited_pages = []
    errors = []

    result = {
        "identity": {
            "company_name": urlparse(base_url).netloc.replace("www.", ""),
            "website_url": base_url,
            "tagline": "Not found on website"
        },
        "business_summary": {
            "what_they_do": "Not found on website",
            "primary_offerings": [],
            "target_segments": []
        },
        "evidence_proof": {
            "key_pages_detected": [],
            "business_signals": [],
            "social_links": {}
        },
        "contact_location": {
            "emails": [],
            "phone_numbers": [],
            "address": "Not found on website",
            "contact_page_url": ""
        },
        "team_hiring": {
            "careers_page_url": "",
            "roles_or_departments": []
        },
        "metadata": {
            "timestamp": datetime.utcnow().isoformat(),
            "pages_crawled": [],
            "errors_or_limitations": []
        }
    }

    # Crawl homepage
    homepage_html, err = fetch_page(base_url)
    if err:
        result["metadata"]["errors_or_limitations"].append(err)
        return result

    soup = BeautifulSoup(homepage_html, "html.parser")
    visited_pages.append(base_url)

    text_content = soup.get_text(" ", strip=True)
    result["contact_location"]["emails"] = extract_emails(text_content)
    result["contact_location"]["phone_numbers"] = extract_phones(text_content)

    # Crawl priority pages
    for path in PRIORITY_PATHS:
        page_url = urljoin(base_url, path)
        html, err = fetch_page(page_url)
        if err:
            continue

        visited_pages.append(page_url)
        result["evidence_proof"]["key_pages_detected"].append(path)

        page_soup = BeautifulSoup(html, "html.parser")
        page_text = page_soup.get_text(" ", strip=True).lower()

        if "career" in path:
            result["team_hiring"]["careers_page_url"] = page_url
        if "contact" in path:
            result["contact_location"]["contact_page_url"] = page_url

        # Simple business signal extraction
        keywords = ["clients", "certification", "iso", "gmp", "case study", "award"]
        for k in keywords:
            if k in page_text:
                result["evidence_proof"]["business_signals"].append(k)

    result["metadata"]["pages_crawled"] = visited_pages
    return result

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python scraper.py <website_url>")
        sys.exit(1)

    url = sys.argv[1]
    output = scrape_website(url)
    print(json.dumps(output, indent=2))

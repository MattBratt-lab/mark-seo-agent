from fastmcp import FastMCP
import requests
from bs4 import BeautifulSoup
import json

# 1. Initialize the Server
mcp = FastMCP("SEO-Brain")

# 2. Add your tool (This is what Claude/Cursor will use)
@mcp.tool()
def simple_audit(url: str) -> str:
    """
    Audits a URL for basic SEO health.
    Use this when you need to check a site's status.
    """
    results = {}

    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; SEO-Brain/1.0)"}
        response = requests.get(url, headers=headers, timeout=10)
        results["status_code"] = response.status_code
        results["url"] = response.url  # final URL after redirects

        soup = BeautifulSoup(response.text, "html.parser")

        # Title
        title_tag = soup.find("title")
        title_text = title_tag.get_text(strip=True) if title_tag else None
        results["title"] = title_text
        results["title_length"] = len(title_text) if title_text else 0
        results["title_ok"] = bool(title_text and 10 <= len(title_text) <= 70)

        # Meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        desc_content = meta_desc["content"].strip() if meta_desc and meta_desc.get("content") else None
        results["meta_description"] = desc_content
        results["meta_description_length"] = len(desc_content) if desc_content else 0
        results["meta_description_ok"] = bool(desc_content and 50 <= len(desc_content) <= 160)

        # H1
        h1_tags = soup.find_all("h1")
        h1_texts = [h.get_text(strip=True) for h in h1_tags]
        results["h1_count"] = len(h1_tags)
        results["h1_tags"] = h1_texts
        results["h1_ok"] = len(h1_tags) == 1

        # H2s
        h2_tags = soup.find_all("h2")
        results["h2_count"] = len(h2_tags)
        results["h2_tags"] = [h.get_text(strip=True) for h in h2_tags[:5]]

        # Images missing alt text
        images = soup.find_all("img")
        missing_alt = [img.get("src", "unknown") for img in images if not img.get("alt")]
        results["images_total"] = len(images)
        results["images_missing_alt"] = len(missing_alt)
        results["images_missing_alt_ok"] = len(missing_alt) == 0

        # Canonical
        canonical = soup.find("link", attrs={"rel": "canonical"})
        results["canonical"] = canonical["href"] if canonical and canonical.get("href") else None

        # Open Graph
        og_title = soup.find("meta", property="og:title")
        og_desc = soup.find("meta", property="og:description")
        results["og_title"] = og_title["content"] if og_title and og_title.get("content") else None
        results["og_description"] = og_desc["content"] if og_desc and og_desc.get("content") else None

        # HTTPS check
        results["https"] = url.startswith("https://")

        # Word count (rough)
        body_text = soup.get_text(separator=" ", strip=True)
        word_count = len(body_text.split())
        results["word_count"] = word_count
        results["word_count_ok"] = word_count >= 300

        # Overall pass/fail
        checks = ["title_ok", "meta_description_ok", "h1_ok", "images_missing_alt_ok", "word_count_ok", "https"]
        passed = sum(1 for c in checks if results.get(c))
        results["score"] = f"{passed}/{len(checks)}"
        results["passed_checks"] = passed
        results["total_checks"] = len(checks)

    except requests.exceptions.Timeout:
        return json.dumps({"error": "Request timed out", "url": url})
    except requests.exceptions.ConnectionError as e:
        return json.dumps({"error": f"Connection error: {str(e)}", "url": url})
    except Exception as e:
        return json.dumps({"error": str(e), "url": url})

    return json.dumps(results, indent=2)

# 3. Add a Resource (This is how you show data to agents in 2026)
@mcp.resource("seo://checklist")
def get_seo_checklist() -> str:
    """Returns the standard SEO checklist."""
    return "1. Check H1\n2. Check Meta Tags\n3. Check Alt Text"

if __name__ == "__main__":
    # Start the server on port 5000
    mcp.run(transport="http", port=5000)

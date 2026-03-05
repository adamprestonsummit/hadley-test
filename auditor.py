"""
auditor.py
Handles page fetching and per-criterion analysis via OpenAI.
"""

import json
import re
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from typing import Dict


# ── System prompt template ─────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert SEO and web accessibility auditor with deep knowledge of:
- Google's Search Quality Guidelines
- WCAG 2.2 accessibility standards
- Schema.org structured data specifications
- Core Web Vitals and technical SEO best practices
- The llmstxt.org specification for AI-readable content

You analyse HTML source code and return structured audit findings in JSON format only.
Never return anything outside the JSON object.
"""

CRITERION_PROMPTS: Dict[str, str] = {
    "structured_data": """Analyse this HTML for structured data (JSON-LD, Microdata, RDFa).

Check:
- Presence and type of schema markup
- Completeness of schema properties (required vs recommended)
- Correct nesting and syntax
- Use of appropriate schema types for the page content
- Multiple schemas if appropriate (Article + BreadcrumbList, etc.)

Return JSON:
{
  "score": <0-100>,
  "summary": "<2-3 sentence overview>",
  "findings": [
    {"status": "pass|fail|warn", "message": "<specific finding>"}
  ],
  "recommendations": ["<actionable recommendation>"]
}""",

    "aria_accessibility": """Analyse this HTML for ARIA and accessibility features.

Check:
- ARIA roles, labels (aria-label, aria-labelledby, aria-describedby)
- Landmark regions (main, nav, header, footer, aside)
- Alt text on images (present, descriptive, not generic)
- Heading hierarchy (single H1, logical H2-H6 order)
- Form labels and input associations
- Link text descriptiveness (avoid "click here", "read more")
- Focus management hints

Return JSON:
{
  "score": <0-100>,
  "summary": "<2-3 sentence overview>",
  "findings": [
    {"status": "pass|fail|warn", "message": "<specific finding>"}
  ],
  "recommendations": ["<actionable recommendation>"]
}""",

    "content_structure": """Analyse this HTML for content structure and semantic HTML.

Check:
- Proper use of H1-H6 heading hierarchy
- Semantic HTML5 elements (article, section, main, aside, nav, header, footer)
- Paragraph length and readability
- Use of lists where appropriate
- Table usage and headers
- Content-to-code ratio hints
- Keyword placement in headings and early content

Return JSON:
{
  "score": <0-100>,
  "summary": "<2-3 sentence overview>",
  "findings": [
    {"status": "pass|fail|warn", "message": "<specific finding>"}
  ],
  "recommendations": ["<actionable recommendation>"]
}""",

    "meta_tags": """Analyse this HTML for meta tags and on-page SEO signals.

Check:
- Title tag (presence, length 50-60 chars, keyword inclusion)
- Meta description (presence, length 150-160 chars, compelling copy)
- Canonical URL tag
- Robots meta tag
- Viewport meta tag
- Open Graph tags (og:title, og:description, og:image, og:url)
- Twitter Card tags
- Hreflang if multilingual signals present

Return JSON:
{
  "score": <0-100>,
  "summary": "<2-3 sentence overview>",
  "findings": [
    {"status": "pass|fail|warn", "message": "<specific finding>"}
  ],
  "recommendations": ["<actionable recommendation>"]
}""",

    "llms_txt": """The user has attempted to fetch /llms.txt for this site. 
The result is provided at the end of the HTML under the marker '<!-- LLMS_TXT_CONTENT -->'.

Analyse whether this site has a valid llms.txt file per the llmstxt.org specification.

Check:
- Presence of the file (was it found or 404?)
- H1 site name
- Blockquote description
- Sections with H2 headings
- Links to important pages with descriptions
- Presence of optional /llms-full.txt reference
- Overall usefulness for AI agents navigating the site

If no llms.txt found, score accordingly and recommend adding one.

Return JSON:
{
  "score": <0-100>,
  "summary": "<2-3 sentence overview>",
  "findings": [
    {"status": "pass|fail|warn", "message": "<specific finding>"}
  ],
  "recommendations": ["<actionable recommendation>"]
}""",

    "page_speed_signals": """Analyse this HTML for page speed and performance signals.

Check:
- Render-blocking <script> tags in <head> without async/defer
- Large inline CSS or JS
- Images without width/height attributes
- Images without loading="lazy" (below the fold candidates)
- Resource hints: <link rel="preload|prefetch|preconnect|dns-prefetch">
- Use of modern image formats (webp, avif) in src or srcset
- Number of external resources referenced

Return JSON:
{
  "score": <0-100>,
  "summary": "<2-3 sentence overview>",
  "findings": [
    {"status": "pass|fail|warn", "message": "<specific finding>"}
  ],
  "recommendations": ["<actionable recommendation>"]
}""",

    "internal_linking": """Analyse the internal linking structure visible in this HTML.

Check:
- Number of internal links (relative paths or same domain)
- Anchor text quality (descriptive vs generic)
- Navigation structure
- Breadcrumb links
- Footer links
- Orphaned-page risk (very few internal links)

Return JSON:
{
  "score": <0-100>,
  "summary": "<2-3 sentence overview>",
  "findings": [
    {"status": "pass|fail|warn", "message": "<specific finding>"}
  ],
  "recommendations": ["<actionable recommendation>"]
}""",

    "mobile_readiness": """Analyse this HTML for mobile-readiness signals.

Check:
- Viewport meta tag (content="width=device-width, initial-scale=1")
- Fixed-width elements (inline style width > 600px)
- Touch targets (button/link sizes - look for tiny clickable areas)
- Absence of user-scalable=no (bad practice)
- Responsive image srcset or picture elements
- Mobile-specific meta tags

Return JSON:
{
  "score": <0-100>,
  "summary": "<2-3 sentence overview>",
  "findings": [
    {"status": "pass|fail|warn", "message": "<specific finding>"}
  ],
  "recommendations": ["<actionable recommendation>"]
}""",

    "security_headers": """Analyse this HTML for security signals visible in the markup.

Check:
- URL uses HTTPS (provided in the URL)
- Content-Security-Policy meta tag
- X-Content-Type-Options hints
- Referrer-Policy meta tag
- Mixed content risks (http:// resources in an https page)
- Unsafe inline JS patterns (onclick= etc. in large numbers)

Return JSON:
{
  "score": <0-100>,
  "summary": "<2-3 sentence overview>",
  "findings": [
    {"status": "pass|fail|warn", "message": "<specific finding>"}
  ],
  "recommendations": ["<actionable recommendation>"]
}""",

    "social_sharing": """Analyse this HTML for social sharing optimisation.

Check:
- Open Graph tags completeness (og:title, og:description, og:image, og:url, og:type)
- Twitter Card tags (twitter:card, twitter:title, twitter:description, twitter:image)
- og:image size hints or explicit dimensions
- Social share buttons or structured sharing links
- Author/publisher markup

Return JSON:
{
  "score": <0-100>,
  "summary": "<2-3 sentence overview>",
  "findings": [
    {"status": "pass|fail|warn", "message": "<specific finding>"}
  ],
  "recommendations": ["<actionable recommendation>"]
}""",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; SEOAuditBot/1.0; +https://github.com/your-repo)"
    )
}

MAX_HTML_CHARS = 80_000  # ~20k tokens - enough for analysis without blowing context


class WebsiteAuditor:
    def __init__(self, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)

    # ── Page fetching ──────────────────────────────────────────────────────────

    def fetch_page(self, url: str) -> dict:
        """Fetch the target page and optionally the llms.txt file."""
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:
            response = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
            response.raise_for_status()
            html = response.text

            # Attempt to fetch llms.txt
            base = self._base_url(url)
            llms_content = self._fetch_llms_txt(base)

            # Inject llms.txt content into HTML for the criterion prompt
            if llms_content:
                html += f"\n<!-- LLMS_TXT_CONTENT -->\n{llms_content}\n<!-- END_LLMS_TXT -->"
            else:
                html += "\n<!-- LLMS_TXT_CONTENT -->\nFile not found (404 or unreachable)\n<!-- END_LLMS_TXT -->"

            # Truncate to avoid excessive token usage
            if len(html) > MAX_HTML_CHARS:
                html = html[:MAX_HTML_CHARS] + "\n<!-- [HTML TRUNCATED FOR ANALYSIS] -->"

            return {
                "success": True,
                "html": html,
                "url": url,
                "status_code": response.status_code,
                "size_kb": len(response.content) / 1024,
            }

        except requests.exceptions.SSLError:
            return {"success": False, "error": "SSL certificate error. Try with http:// if this is a test site."}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Could not connect to the server. Check the URL."}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Request timed out after 15 seconds."}
        except requests.exceptions.HTTPError as e:
            return {"success": False, "error": f"HTTP error: {e}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _base_url(self, url: str) -> str:
        """Extract scheme + netloc from a URL."""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def _fetch_llms_txt(self, base_url: str) -> str | None:
        """Try to fetch /llms.txt or /llms-full.txt."""
        for path in ["/llms.txt", "/llms-full.txt"]:
            try:
                r = requests.get(base_url + path, headers=HEADERS, timeout=8)
                if r.status_code == 200:
                    return r.text[:5000]  # Limit size
            except Exception:
                pass
        return None

    # ── Analysis ───────────────────────────────────────────────────────────────

    def analyse_criterion(self, criterion_key: str, html: str, url: str) -> dict:
        """Send HTML to OpenAI and parse the structured response."""
        prompt = CRITERION_PROMPTS.get(criterion_key)
        if not prompt:
            return {
                "score": 0,
                "summary": "Unknown criterion.",
                "findings": [],
                "recommendations": [],
            }

        user_message = f"URL: {url}\n\nHTML Source:\n{html}\n\n---\n\n{prompt}"

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.1,
                max_tokens=1200,
                response_format={"type": "json_object"},
            )

            raw = response.choices[0].message.content
            data = json.loads(raw)

            # Normalise score to 0-100
            score = float(data.get("score", 0))
            score = max(0.0, min(100.0, score))
            data["score"] = score

            return data

        except json.JSONDecodeError as e:
            return {
                "score": 0,
                "summary": f"Could not parse OpenAI response as JSON: {e}",
                "findings": [{"status": "fail", "message": "JSON parse error from AI response."}],
                "recommendations": ["Retry the audit."],
            }
        except Exception as e:
            return {
                "score": 0,
                "summary": f"OpenAI API error: {e}",
                "findings": [{"status": "fail", "message": str(e)}],
                "recommendations": [],
            }

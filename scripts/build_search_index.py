import json
import re
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PageText(HTMLParser):
    def __init__(self, source, section=None):
        super().__init__()
        self.section = section
        self.collecting = False
        self.in_title = False
        self.parts = []
        self.title_parts = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        if tag == "main":
            self.collecting = self.section is None or dict(attrs).get("id") == self.section
        if tag == "h1" and self.collecting:
            self.in_title = True

    def handle_data(self, data):
        if self.collecting:
            self.parts.append(data)
            if self.in_title:
                self.title_parts.append(data)

    def handle_endtag(self, tag):
        if tag == "h1":
            self.in_title = False
        if tag == "main":
            self.collecting = False

    @staticmethod
    def normalize(parts):
        text = re.sub(r"\s+", " ", " ".join(parts)).strip()
        return re.sub(r"\s+([.,:;!?])", r"\1", text)


def build_index():
    sources = [
        ("about/index.html", None, "About", "about/index.html"),
        ("contact/index.html", None, "Contact", "contact/index.html"),
        (Path("projects") / "index.html", None, "Projects", "projects/index.html"),
        (Path("blog") / "index.html", None, "Blog", "blog/index.html"),
    ]
    for folder in ("projects", "blog"):
        for path in sorted((ROOT / folder).glob("*.html")):
            if path.name != "index.html":
                sources.append((path, None, None, f"{folder}/{path.name}"))
    pages = []
    for filename, section, title, url in sources:
        document = PageText(
            (ROOT / filename).read_text(encoding="utf-8"), section
        )
        text = document.normalize(document.parts)
        title = title or document.normalize(document.title_parts)
        if not text or not title:
            raise ValueError(f"Missing searchable content or title in {filename}: {section}")
        pages.append({"url": url, "title": title, "text": text})
    return pages


if __name__ == "__main__":
    output = "window.siteSearchPages = " + json.dumps(build_index(), indent=2) + ";\n"
    (ROOT / "assets" / "js" / "search-index.js").write_text(output, encoding="utf-8")

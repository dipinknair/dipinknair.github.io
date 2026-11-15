import json
import runpy
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
PAGES = [ROOT / "index.html", ROOT / "projects" / "index.html"]
PAGES.extend(sorted((ROOT / "blog").glob("*.html")))


class HeaderParser(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.in_header = False
        self.in_nav = False
        self.link = None
        self.links = []
        self.ids = set()
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "header":
            self.in_header = True
        if self.in_header:
            if "id" in attrs:
                self.ids.add(attrs["id"])
            if tag == "nav":
                self.in_nav = True
            if tag == "a" and self.in_nav:
                self.link = [attrs["href"], ""]
                self.links.append(self.link)

    def handle_data(self, data):
        if self.link is not None:
            self.link[1] += data

    def handle_endtag(self, tag):
        if tag == "a":
            self.link = None
        if tag == "nav":
            self.in_nav = False
        if tag == "header":
            self.in_header = False


class NavigationTests(unittest.TestCase):
    def test_standalone_headers_match_homepage(self):
        home = HeaderParser(PAGES[0].read_text(encoding="utf-8"))
        for path in PAGES[1:]:
            with self.subTest(page=path.relative_to(ROOT)):
                header = HeaderParser(path.read_text(encoding="utf-8"))
                self.assertEqual(
                    [label for _, label in header.links],
                    [label for _, label in home.links],
                )
                self.assertEqual(header.ids, home.ids)

    def test_navigation_links_resolve_to_pages_and_views(self):
        for path in PAGES:
            header = HeaderParser(path.read_text(encoding="utf-8"))
            for href, label in header.links:
                with self.subTest(page=path.relative_to(ROOT), link=label):
                    url = urlsplit(href)
                    target = (path.parent / url.path).resolve() if url.path else path
                    if target.is_dir():
                        target /= "index.html"
                    self.assertTrue(target.is_file(), href)
                    if url.fragment:
                        self.assertIn(
                            f'id="v-{url.fragment}"',
                            target.read_text(encoding="utf-8"),
                        )


class SearchIndexTests(unittest.TestCase):
    def test_committed_index_matches_current_page_content(self):
        generator = runpy.run_path(str(ROOT / "scripts" / "build_search_index.py"))
        source = (ROOT / "assets" / "js" / "search-index.js").read_text(encoding="utf-8")
        pages = json.loads(source.removeprefix("window.siteSearchPages = ").strip().removesuffix(";"))
        self.assertEqual(pages, generator["build_index"]())

    def test_article_body_terms_find_the_correct_posts(self):
        source = (ROOT / "assets" / "js" / "search-index.js").read_text(encoding="utf-8")
        pages = json.loads(source.removeprefix("window.siteSearchPages = ").strip().removesuffix(";"))
        for term, url in [
            ("seccomp", "blog/jetson-nano-home-server.html"),
            ("fine-grained", "blog/obsidian-git-sync.html"),
        ]:
            with self.subTest(term=term):
                matches = [page["url"] for page in pages if term in page["text"].lower()]
                self.assertEqual(matches, [url])


if __name__ == "__main__":
    unittest.main()

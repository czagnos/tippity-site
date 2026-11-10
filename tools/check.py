"""Checks the site before a change goes in: every page's Content Security Policy, no scripts, inline styles, forms or
frames, alt text on every image, nothing loaded from another site, no secrets, and images without metadata.

    python3 tools/check.py             # blanks still to fill are listed
    python3 tools/check.py --publish   # blanks still to fill fail the check too

Python's standard library only. Exit code 1 when something fails.
"""

import html.parser
import pathlib
import re
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CSP = ("default-src 'none'; style-src 'self'; img-src 'self'; font-src 'self'; base-uri 'none'; "
       "form-action 'none'; upgrade-insecure-requests")
SITE = "https://czagnos.github.io/tippity-site/"
# Links a visitor may follow out of the site. Nothing is ever loaded from another site.
OUTBOUND = ("https://docs.github.com/", "https://apps.apple.com/")
BANNED_TAGS = {"script", "style", "iframe", "frame", "object", "embed", "form", "input", "base", "applet"}
SECRETS = [
    (r"script\.google\.com", "an Apps Script address (the game's telemetry endpoint stays private)"),
    (r"AKfy[0-9A-Za-z_-]{20,}", "an Apps Script deployment ID"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "a private key"),
    (r"\bgh[pousr]_[0-9A-Za-z]{30,}|github_pat_[0-9A-Za-z_]{30,}", "a GitHub token"),
    (r"\bAIza[0-9A-Za-z_-]{30,}", "a Google API key"),
    (r"\bxox[abpr]-[0-9A-Za-z-]{10,}", "a Slack token"),
    (r"\.hgw\.local|\.local\b(?!host)", "a computer's local network name"),
]
TEXT = {".html", ".css", ".py", ".md", ".txt", ".json", ".xml", ".svg"}
PNG_KEEP = {b"IHDR", b"PLTE", b"IDAT", b"IEND", b"sRGB", b"gAMA", b"cHRM", b"tRNS"}

problems, blanks = [], []


class Page(html.parser.HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.csp = None

    def fail(self, text):
        problems.append(f"{self.path.relative_to(ROOT)}:{self.getpos()[0]}: {text}")

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in BANNED_TAGS:
            self.fail(f"<{tag}> is not allowed")
        for name, _ in attrs:
            if name.startswith("on") or name == "style":
                self.fail(f"inline {name}= is not allowed")
        if tag == "meta" and (a.get("http-equiv") or "").lower() == "content-security-policy":
            self.csp = a.get("content")
        if tag == "img" and "alt" not in a:
            self.fail("an image without alt")
        if tag == "mark" and "todo" in (a.get("class") or ""):
            blanks.append(f"{self.path.relative_to(ROOT)}:{self.getpos()[0]}")
        for name in ("src", "srcset", "poster", "data"):
            if a.get(name) and re.match(r"^([a-z][a-z0-9+.-]*:|//)", a[name], re.I):
                self.fail(f"{name}={a[name]!r} loads from outside the site")
        if tag == "link" and a.get("href") and re.match(r"^([a-z][a-z0-9+.-]*:|//)", a["href"], re.I) and not (
                a.get("rel") == "canonical" and a["href"].startswith(SITE)):
            self.fail(f"<link href={a['href']!r}> loads from outside the site")
        if tag == "a" and a.get("href"):
            href = a["href"]
            if re.match(r"^([a-z][a-z0-9+.-]*:|//)", href, re.I) and not (
                    href.startswith("mailto:") or href.startswith(OUTBOUND)):
                self.fail(f"a link to {href!r}, which is not on the list of outbound links")
            if a.get("target") == "_blank" and "noopener" not in (a.get("rel") or ""):
                self.fail("target=_blank without rel=noopener")


def check_pages():
    for path in sorted(ROOT.rglob("*.html")):
        if ".git" in path.parts:
            continue
        page = Page(path)
        page.feed(path.read_text(encoding="utf-8"))
        if page.csp != CSP:
            problems.append(f"{path.relative_to(ROOT)}: the Content Security Policy is missing or differs from {CSP!r}")


def check_css():
    css = (ROOT / "assets" / "site.css").read_text(encoding="utf-8")
    for url in re.findall(r"url\(\s*['\"]?([^'\")]+)", css):
        if re.match(r"^([a-z][a-z0-9+.-]*:|//)", url, re.I):
            problems.append(f"assets/site.css: url({url}) loads from outside the site")
    if "@import" in css:
        problems.append("assets/site.css: @import is not allowed")


def check_secrets():
    for path in sorted(ROOT.rglob("*")):
        if ".git" in path.parts or not path.is_file() or path.suffix not in TEXT:
            continue
        if path == pathlib.Path(__file__).resolve():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern, what in SECRETS:
            if re.search(pattern, text):
                problems.append(f"{path.relative_to(ROOT)}: looks like {what}")


def check_images():
    for path in sorted((ROOT / "assets" / "img").glob("*")):
        data = path.read_bytes()
        name = path.relative_to(ROOT)
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            at = 8
            while at < len(data):
                length = struct.unpack(">I", data[at:at + 4])[0]
                kind = data[at + 4:at + 8]
                if kind not in PNG_KEEP:
                    problems.append(f"{name}: PNG chunk {kind.decode('latin1')} (metadata) should be stripped")
                at += 12 + length
        elif data[:2] == b"\xff\xd8":
            at = 2
            while at < len(data) and data[at] == 0xFF and data[at + 1] != 0xDA:
                marker = data[at + 1]
                length = struct.unpack(">H", data[at + 2:at + 4])[0]
                if 0xE1 <= marker <= 0xEF or marker == 0xFE:
                    problems.append(f"{name}: JPEG segment {marker:#x} (metadata) should be stripped")
                at += 2 + length
        else:
            problems.append(f"{name}: only PNG and JPEG images are expected")


def main():
    publish = "--publish" in sys.argv[1:]
    check_pages()
    check_css()
    check_secrets()
    check_images()
    for line in problems:
        print("FAIL", line)
    for line in blanks:
        print("FAIL" if publish else "BLANK", line, "still to fill")
    failed = bool(problems) or (publish and bool(blanks))
    print(f"{len(problems)} problem(s), {len(blanks)} blank(s) to fill" + (" (allowed before publishing)" if blanks and not publish else ""))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

"""Writes privacy/index.html from the game's privacy policy, a Markdown file kept with the game's code
(docs/store/ios/privacy-policy.md).

    python3 tools/build_privacy.py path/to/privacy-policy.md

Only the Markdown the policy uses is read: a title (#), sections (##, ###), paragraphs, lists (- ), **bold**,
[links](https://...), email addresses (as mail links) and {{placeholders}}, which show as marked blanks until they
are filled. HTML comments are left
out. Everything else is escaped, so the page carries no markup the policy did not ask for. Python's standard library
only.
"""

import html
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "privacy" / "index.html"

HEAD = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'self'; img-src 'self'; font-src 'self'; base-uri 'none'; form-action 'none'; upgrade-insecure-requests">
  <meta name="referrer" content="no-referrer">
  <meta name="color-scheme" content="dark">
  <meta name="theme-color" content="#1C0F1C">
  <title>Privacy Policy · Tippity</title>
  <meta name="description" content="What Tippity collects, why, who receives it, how long it is kept and what you can do about it.">
  <link rel="icon" type="image/png" sizes="32x32" href="../assets/img/favicon-32.png">
  <link rel="icon" type="image/png" sizes="192x192" href="../assets/img/icon-192.png">
  <link rel="apple-touch-icon" href="../assets/img/apple-touch-icon.png">
  <link rel="stylesheet" href="../assets/site.css">
  <link rel="canonical" href="https://czagnos.github.io/tippity-site/privacy/">
</head>
<body>
  <a class="skip" href="#main">Skip to content</a>

  <header class="site-header">
    <div class="wrap">
      <a class="brand" href="../" aria-label="Tippity, home"><img src="../assets/img/icon-192.png" width="36" height="36" alt="">Tippity</a>
      <nav class="site-nav" aria-label="Site">
        <ul>
          <li class="wide"><a href="../#how">How it plays</a></li>
          <li><a href="../support/">Support</a></li>
          <li><a href="./" aria-current="page">Privacy</a></li>
        </ul>
      </nav>
    </div>
  </header>

  <main id="main" class="page">
    <div class="wrap">
      <article class="prose">
        <p class="kicker">Tippity</p>
"""

# The website itself, apart from the game's policy.
SITE = """
        <section class="card box" aria-labelledby="site-title">
          <h2 id="site-title">About this website</h2>
          <p>This website sets no cookies, has no analytics and loads nothing from other websites. It is hosted on
            GitHub Pages: when you visit, GitHub receives your IP address, as every web server does, and handles it
            under the <a href="https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement">GitHub General Privacy Statement</a>.
            We don't receive it.</p>
        </section>
"""

FOOT = """      </article>
    </div>
  </main>

  <footer class="site-footer">
    <div class="wrap">
      <p>© 2026 7 District Game</p>
      <ul>
        <li><a href="../support/">Support</a></li>
        <li><a href="./" aria-current="page">Privacy policy</a></li>
      </ul>
    </div>
  </footer>
</body>
</html>
"""


def inline(text):
    """Escapes a line of text, then turns **bold**, [links](https://...) and {{placeholders}} into markup."""
    out = html.escape(text, quote=False)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"\[([^\]]+)\]\((https://[^)\s\"<>]+)\)", lambda m: f'<a href="{html.escape(m.group(2))}">{m.group(1)}</a>', out)
    out = re.sub(r"\{\{(.+?)\}\}", r'<mark class="todo">\1</mark>', out)
    out = re.sub(r"(?<![\w.@\"/])([\w.+-]+@[\w-]+(?:\.[\w-]+)+)", r'<a href="mailto:\1">\1</a>', out)
    if re.search(r"\*\*|\]\(|\{\{|\}\}", out):
        raise SystemExit(f"Markdown this script does not read: {text!r}")
    return out


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def convert(markdown):
    """The policy's body as HTML lines, and its title."""
    markdown = re.sub(r"<!--.*?-->", "", markdown, flags=re.S)
    lines = markdown.splitlines()
    body, title = [], None
    para, items = [], []

    def flush():
        if para:
            text = " ".join(para)
            css = ' class="meta"' if text.startswith("Effective ") else ""
            body.append(f"        <p{css}>{inline(text)}</p>")
            para.clear()
        if items:
            body.append("        <ul>")
            body.extend(f"          <li>{inline(item)}</li>" for item in items)
            body.append("        </ul>")
            items.clear()

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            flush()
            continue
        if line.startswith("# "):
            flush()
            if title is not None:
                raise SystemExit("The policy has more than one title.")
            title = line[2:].strip()
            body.append(f"        <h1>{inline(title)}</h1>")
        elif line.startswith("## ") or line.startswith("### "):
            flush()
            level = 2 if line.startswith("## ") else 3
            text = line[level + 1:].strip()
            body.append(f'        <h{level} id="{slug(text)}">{inline(text)}</h{level}>')
        elif line.startswith("- "):
            if para:
                flush()
            items.append(line[2:].strip())
        elif line.startswith("  ") and items:
            items[-1] += " " + line.strip()
        elif line.startswith(("#", ">", "|", "```", "1.", "* ")):
            raise SystemExit(f"Markdown this script does not read: {line!r}")
        else:
            if items:
                flush()
            para.append(line.strip())
    flush()
    if title is None:
        raise SystemExit("The policy has no title.")
    return body


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    source = pathlib.Path(sys.argv[1])
    body = convert(source.read_text(encoding="utf-8"))
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(HEAD + "\n".join(body) + "\n" + SITE + FOOT, encoding="utf-8")
    blanks = sum(line.count('class="todo"') for line in body)
    print(f"wrote {OUT.relative_to(ROOT)} from {source}; {blanks} blank(s) still to fill")


if __name__ == "__main__":
    main()

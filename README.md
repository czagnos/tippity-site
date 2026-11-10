# Tippity's website

The website of Tippity, a puzzle game for iPhone by 7 District Game, at https://czagnos.github.io/tippity-site/: the
home page, the privacy policy (`privacy/`) and the support page (`support/`). GitHub Pages serves this repository's
`main` branch as it is: plain HTML and CSS, no build step and no scripts.

## Layout

```
index.html            the home page
privacy/index.html    the privacy policy, written by tools/build_privacy.py from the game's policy
support/index.html    the support page: contact, the Player ID, questions
404.html              page not found
assets/site.css       the site's style, in the game's Kadife colours
assets/fonts/         DM Serif Display and DM Sans, with their licenses (SIL OFL 1.1)
assets/img/           the game's icon and art
tools/                build_privacy.py and check.py (Python 3, standard library only)
```

## Preview

```
python3 -m http.server 8000 --bind 127.0.0.1
```

Then open http://127.0.0.1:8000/. The not-found page shows only on GitHub Pages: its links start from the site's
root, `/tippity-site/`, so that it works at any missing address.

## The privacy policy

Its source is the game's `docs/store/ios/privacy-policy.md`, kept with the game's code. When it changes, write the
page again rather than editing `privacy/index.html` by hand:

```
python3 tools/build_privacy.py path/to/privacy-policy.md
```

Blanks the policy still has (`{{...}}`) show as marked blanks. Below the policy, the page adds a short note about this
website itself.

## Security

- Static files only: no server code, no forms, no scripts, no cookies, no analytics, and nothing loaded from other
  websites; the fonts and the images are served from here.
- Every page carries a Content Security Policy that allows only this site's own styles, images and fonts, and no
  scripts at all. GitHub Pages can't send headers, so it is a `<meta>` tag.
- Nothing secret belongs here: the repository is public, and its history keeps everything ever committed. No keys,
  tokens or private service addresses.
- Images have their metadata (EXIF and the like) stripped before they are committed.
- Commits use GitHub's no-reply email address, so no personal address or computer name goes into the history.
- `python3 tools/check.py` checks all of this; run it before every commit. `--publish` also fails while a blank is
  left to fill.

## Before publishing

- Fill every marked blank (`class="todo"`): the developer's legal name, the effective date, the email addresses and
  the legal basis of the policy's Turkish law (KVKK) section, after its legal check.
- In the repository's settings: Pages deploys from `main`, the root folder, with HTTPS enforced.
- The site's address is in the pages' canonical and Open Graph tags, `404.html` and `tools/check.py`; a move to
  another address (a domain of the studio's own) changes them together.

## Licenses

The fonts: SIL Open Font License 1.1 (`assets/fonts/OFL-*.txt`). Everything else, the game's name, art, screenshots
and texts: © 2026 7 District Game, all rights reserved.

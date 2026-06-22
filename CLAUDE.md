# CLAUDE.md

## Project Overview

Static personal website hosted on **GitHub Pages** at `itpyi.github.io`. No build tools, no framework — plain HTML, CSS, and vanilla JS.

**Owner:** Wang Yifei (itpyi), PhD candidate in theoretical physics at IAS, Tsinghua University.

## Architecture

```
├── index.html          # Landing page: cover → two-route entrance
├── academics.html      # 治学 (formal CV: research + education + open source)
├── general.html        # 杂览 (fuller portrait: research + open source + reading + education + glossary)
├── research.html       # Research interests + publications (stub)
├── opensource.html     # Open source project details (English-only)
├── education.html      # Education list + commentary
├── about.html          # About me / site / symbol (zh-only for some sections)
├── booklist.html       # Book list (JS-rendered from JSON)
├── assets/
│   ├── css/styles.css  # Single shared stylesheet (CSS custom properties theme)
│   ├── js/
│   │   ├── script.js   # Lang switching, footer/subnav injection, homepage transition
│   │   └── booklist.js # Fetches books.json, renders book list
│   ├── partials/
│   │   ├── footer.html # Injected by script.js into <footer id="siteFooter">
│   │   └── subnav.html # Injected by script.js into <div id="siteSubnav">
│   ├── data/books.json # Book data for booklist.js
│   ├── images/         # favicon, avatar, icons
│   ├── fonts/          # Custom subset fonts (jhlst, title2)
│   └── docs/           # PDF files (thesis, etc.)
└── docs/superpowers/   # Historical design specs (homepage split)
```

## Key Patterns

### Language System

All multilingual content uses `data-lang="zh|en"` attributes. Default language is **zh** (汉语). The JS manages two levels:

- **Section-level switchers** (`.lang-switcher`): Each `.lang-switchable` section can have its own language menu. Switches `<h2>` titles and `.lang-content` blocks within that section only.
- **Global switcher** (`.global-lang-switcher` in navbar): Calls `switchGlobalLanguage(targetLang)` — updates `<html lang>`, `<title>`, `<meta>`, and all `[data-lang]` elements across the page, plus syncs all section-level states.

Elements with `data-lang` get `display: none` when not active. The JS toggles `display` and `.active` classes.

### Navigation Injection

- `index.html` has an **inline** topnav (just logo + global lang switcher, no nav links) — this is intentional.
- All subpages use `<div id="siteSubnav" data-subnav-title-zh="..." data-subnav-title-en="...">` which `script.js` replaces with the fetched `subnav.html` partial (with `{{TITLE_ZH}}`/`{{TITLE_EN}}` placeholders replaced).
- Footer injection: `<footer id="siteFooter"></footer>` → `script.js` fetches `footer.html`.

### Homepage Transition (index.html only)

`<body class="homepage-shell">` — two visual states:
1. **Cover state**: Full-screen `.home-cover` with vertical title overlay and "click to enter" prompt.
2. **Entered state**: `homepage-shell.home-entered` — cover panels slide outward (`translateX(±100%)`), revealing `.home-split` with two route panels: Academic (left) → `academics.html`, General (right) → `general.html`.

### Content Duplication (Intentional)

Research, open source, and education content appears on **both** `academics.html` and `general.html` by design. The academic page is a narrow formal dossier; the general page is the fuller portrait. Do not deduplicate.

## CSS Theme

CSS custom properties in `:root` define a traditional Chinese aesthetic:
- `--primary-color: #1B3144` (靛青/indigo)
- `--accent-color: #962A1F` (朱砂/vermillion)
- `--background-color: #F0E9D7` (宣纸/rice paper)
- `--body-text: #4A453A` (墨迹/ink)
- `--surface-color: #F7F3E8` (云帛/cloud silk)

## Rules for Changes

1. **No frameworks or build tools** — keep it plain HTML/CSS/JS.
2. **Never change visual behavior unless asked** — structural cleanup only.
3. **Default language is zh** — never switch the default to en.
4. **Keep the language architecture extensible** — don't collapse to a simple zh/en binary; pages may add more languages per section (e.g. about.html has fr and la).
5. **Do not deduplicate content across pages** — the overlap between academics and general is intentional.
6. **Commit in meaningful chunks** with descriptive messages. End with `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
7. **Deployment workflow**: After making content changes, update the "last updated" date in `assets/partials/footer.html` (both `data-lang="zh"` and `data-lang="en"` lines) to the current date. Ask the user for approval before committing and pushing.

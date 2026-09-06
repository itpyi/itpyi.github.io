# AGENTS.md

## Project Overview

This repository is a static personal website hosted on GitHub Pages at `itpyi.github.io`. It uses plain HTML, CSS, and vanilla JavaScript; there is no framework or build toolchain.

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
│   │   ├── script.js   # Language switching, navigation/footer injection, homepage transition
│   │   └── booklist.js # Fetches books.json and renders the book list
│   ├── partials/
│   │   ├── footer.html # Injected into <footer id="siteFooter">
│   │   └── subnav.html # Injected into <div id="siteSubnav">
│   ├── data/books.json # Book data for booklist.js
│   ├── images/         # Favicon, avatar, and icons
│   ├── fonts/          # Custom subset fonts (jhlst, title2)
│   └── docs/           # PDF files (thesis, etc.)
└── docs/superpowers/   # Historical design specs (homepage split)
```

## Language System

Multilingual content uses `data-lang="..."` attributes. Chinese (`zh`) is the default language. The architecture has two independent levels:

- **Page global language:** `.global-lang-switcher` calls `switchGlobalLanguage(targetLang)`, updating `<html lang>`, the active title and description, all page-level `[data-lang]` elements, and each section's compatible language.
- **Block language:** each `.lang-switchable` section may have its own `.lang-switcher`; it controls only that block's headings and `.lang-content` panels.

When a requested language is unavailable in a block, that block falls back to `zh`. When a requested language is unavailable on the target page (determined by the page's language-specific `<title>`), the target page's global language also falls back to `zh`.

### Internal-link language propagation

Every internal link to an HTML page carries the source language as the `lang` query parameter:

1. If the link is inside a language-independent `.lang-switchable` block, its source language is that block's currently active language.
2. Otherwise, its source language is the current page global language.
3. The target page reads `?lang=...` and uses it as its global language, falling back to Chinese when that page does not provide the requested language.

This rule applies equally to the homepage entrance doors and to navigation links, including a link back to the page currently being viewed. Hash anchors and external links are not language-propagated.

Keep the language system extensible: do not reduce it to a hard-coded zh/en-only design. Some sections (for example, `about.html`) provide additional languages such as `fr` and `la`.

## Navigation and Transitions

- `index.html` has an inline top navigation containing only the logo and global language switcher; this is intentional.
- Subpages use `<div id="siteSubnav" data-subnav-title-zh="..." data-subnav-title-en="...">`. `script.js` injects `assets/partials/subnav.html` and replaces `{{TITLE_ZH}}`/`{{TITLE_EN}}`.
- `<footer id="siteFooter"></footer>` is populated by the shared footer partial.
- On `index.html`, `.homepage-shell` transitions from the full-screen `.home-cover` to `.home-split` when `.cover-enter-zone` is activated. The two route panels lead to `academics.html` and `general.html`.

## Content and CSS

Research, open-source, and education content intentionally appears on both academic and general pages. Do not deduplicate it.

The traditional Chinese visual theme is defined by CSS custom properties in `:root`, including indigo `--primary-color`, vermilion `--accent-color`, rice-paper `--background-color`, ink `--body-text`, and cloud-silk `--surface-color`.

## Rules for Changes

1. Keep the site plain HTML/CSS/JS; do not add frameworks or build tools.
2. Do not change visual behavior unless the user requests it.
3. Keep `zh` as the default language.
4. Preserve the extensible language architecture and the internal-link propagation rules above.
5. Do not deduplicate intentionally duplicated content across pages.
6. Make focused, meaningful commits with descriptive messages when committing. Do not add tool- or vendor-specific co-author trailers unless explicitly requested.
7. After content changes, update both language lines in `assets/partials/footer.html` to the current date. Ask the user for approval before committing or pushing.

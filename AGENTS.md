# AGENTS.md

## Project Overview

This repository is a static personal website hosted on GitHub Pages at `itpyi.site`. Content is authored as Markdown and JSON data files, rendered by a small single-purpose Python build script (`build.py`) — a lightweight pipeline, not a static-site-generator framework. Output goes to `_site/` (gitignored); deployment is automated by `.github/workflows/deploy.yml` on every push to `main`.

**Owner:** Wang Yifei (itpyi), PhD candidate in theoretical physics at the Chen-Ning Yang Institute for Advanced Study, Tsinghua University.

## Architecture

```
├── build.py                     # THE build pipeline (documented step-by-step in its header)
├── requirements.txt             # PyYAML only
├── scripts/check_dom.py         # DOM structure comparator (ignores whitespace/comments)
├── .github/workflows/deploy.yml # build + deploy to Pages on push to main
├── content/                     # one markdown file per page (name = output page name)
│   ├── index.md                 #   homepage (front matter only; bespoke template)
│   ├── academics.md  general.md  about.md  education.md
│   └── booklist.md  opensource.md  research.md
├── templates/
│   ├── pages/page.html          # shared skeleton for all pages except index
│   ├── pages/index.html         # homepage skeleton
│   └── partials/footer.html     # rendered with dates → _site/assets/partials/footer.html
├── data/
│   └── site.json                # build configuration only: url, lang_labels, lang_unavailable
├── assets/                      # copied verbatim into _site/assets/
│   ├── css/  js/  images/  fonts/  docs/
│   ├── data/                    # the single home of all site CONTENT data:
│   │   ├── publications.bib     #   publications (client-rendered by assets/js/publications.js)
│   │   ├── books.json           #   book list (client-rendered by assets/js/booklist.js)
│   │   ├── education.json       #   education entries (education section kind)
│   │   ├── projects.json        #   open-source projects (projects / projects-group kinds)
│   │   └── links.json           #   links (links section kind)
│   └── partials/subnav.html     # client-side nav template ({{TITLE_ZH}} replaced at runtime)
└── _site/                       # build output (gitignored; the deployed artifact)
```

Content data lives together in `assets/data/` — content is not build configuration; it changes with the author's career. `data/` holds only true build configuration.

## Page Format (one markdown file per page)

Each page is a single file in `content/` whose name is the output page name (`academics.md` → `academics.html`). Front matter carries page metadata; the body is the page's sections, top to bottom.

```markdown
---
title: {zh: 履历, en: Curriculum Vitae}      # page title per language
meta:  {zh: …, en: …}                        # meta description per language
subnav: {zh: 履历, en: Curriculum Vitae}     # subnav title per language
scripts: [assets/js/publications.js]         # extra page scripts (script.js is always included)
section-class: cv-section                    # optional default class for all sections
---
<!-- section {title: {zh: 研究, en: Research}} -->
<!-- lang:zh -->
…markdown body…
<!-- lang:en -->
…markdown body…

<!-- section {kind: links, title: {zh: 相关链接, en: Links}} -->
```

Rules:

- **Sections**: `<!-- section {…} -->` opens a section; the next fence or end of file closes it. Section order in the file = order on the page; reorder by moving blocks.
- **Section attributes** (YAML flow mapping inside the fence):
  - `title` — `{lang: text}` dictionary for switchable sections (its keys are the language menu, in that order); a plain string for non-switchable sections.
  - `kind` — `content` (default) | `links` | `publications` | `projects` | `projects-group` | `education`.
  - `switchable: false` — plain section without language widgets.
  - `langs` — optional explicit menu language list (defaults to the title keys).
  - `class`, `id`, `data-section-id` — passthrough attributes; `list_class` (links only, `null` = unstyled ul); `group` (projects-group only: index into projects.json `opensource_groups`).
- **Language blocks**: `<!-- lang:xx -->` inside a section body. Any language code works (zh/en/fr/la/…). Menu labels come from `site.json` `lang_labels` (fallback: the code itself).
- **Markdown subset**: paragraphs, `- ` lists, `[text](url)` links, raw HTML lines (escape hatch for styled elements, e.g. `<p class="research-topic">…</p>`), backslash escapes. Anything else — write raw HTML.
- **Missing-language placeholder**: when a title declares a language whose body or JSON fields are missing, the build renders «该语言版本尚未开发» in that language (texts in `site.json` `lang_unavailable`). Blocks without a language config are unaffected by global language changes (runtime fallback in script.js).

## Data Files

- `assets/data/education.json` — `[{year: {lang: …}, institution: {lang: …}, details: {lang: [markdown strings]}}]`.
- `assets/data/projects.json` — projects keyed by id; `academics_items` orders the CV-page list; `opensource_groups` orders the opensource page; a project may carry a `page_en` view (title/metas/links) for the English opensource page.
- `assets/data/links.json` — `[{label, url}]` (labels are proper nouns, identical across languages).
- `assets/data/publications.bib` and `books.json` — rendered client-side; the build copies them as-is.

## Language System

Multilingual content uses `data-lang` attributes; Chinese is the default. Two independent levels: the page-global language (`.global-lang-switcher`) and per-block language (each `.lang-switchable` section's own switcher). When a requested language is unavailable in a block, that block falls back to `zh`; the page-global language falls back when the target page has no matching `<title data-lang>`. Internal links propagate `?lang=` from the source block/page. Keep the system extensible — never reduce it to hardcoded zh/en (about.html provides fr/la).

## Navigation and Transitions

- `index.html` keeps its bespoke template (`templates/pages/index.html`): inline topnav with logo + global switcher, cover → split transition. All its strings live in `content/index.md` front matter.
- Subpages use the shared skeleton `templates/pages/page.html` with `<div id="siteSubnav" data-subnav-title-*>`; `script.js` injects `assets/partials/subnav.html` and replaces its `{{TITLE_ZH}}`/`{{TITLE_EN}}` at runtime — the build must not touch those placeholders.
- `<footer id="siteFooter"></footer>` is filled by the generated `assets/partials/footer.html`.

## Content and CSS

The traditional Chinese visual theme is defined by CSS custom properties in `:root` (indigo primary, vermilion accent, rice-paper background, ink text, cloud-silk surface). Generated content must keep using the existing classes (`.body-list`, `.link-body`, `.proj-list`, `.edu-list`…) — the build's markdown post-processor adds them automatically; raw HTML should reuse them rather than invent new styling.

## Build and Preview

```
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # once
.venv/bin/python build.py                                            # build to _site/
python3 -m http.server 8000 -d _site                                 # local preview
```

The pipeline is documented step by step in `build.py`'s header. The footer «最后更新于» date is derived at build time from the latest git commit touching `content/ data/ templates/ assets/data/` (fallback: build date) — never edit it by hand.

## Deployment

Pushing to `main` triggers `.github/workflows/deploy.yml`, which builds and deploys `_site/` to GitHub Pages (the repository's Pages source is set to GitHub Actions). A push therefore deploys the live site.

## Rules for Changes

1. Do not change visual behavior unless the user requests it. Generated pages must reproduce the existing DOM contracts; verify structure with `scripts/check_dom.py`.
2. Keep `zh` as the default language; preserve the extensible language architecture and the internal-link propagation rules.
3. Content is page-local: each page's prose lives in its own `content/*.md`; shared structured content lives in `assets/data/`.
4. Make focused, meaningful commits with descriptive messages. Do not add tool- or vendor-specific co-author trailers unless explicitly requested.
5. Pushing to `main` deploys the live site — confirm with the user before pushing.

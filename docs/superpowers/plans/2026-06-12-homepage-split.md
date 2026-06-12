# Homepage Split Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the site entry flow so `index.html` becomes a two-state cover-to-split entrance, add a formal `Curriculum Vitae` route, add a general route that preserves the current homepage body, and simplify navigation while keeping the existing multilingual architecture intact.

**Architecture:** Keep the existing shared language-switching system and layered static-page structure. Split the current homepage into a cover state and a revealed split-entry state within `index.html`, move the old homepage body into a dedicated general page, introduce a new `curriculum-vitae.html` page that aggregates formal material, and simplify the shared navigation partial so every page points only to the homepage entrance and the blog.

**Tech Stack:** Static HTML, shared CSS in `assets/css/styles.css`, shared JavaScript in `assets/js/script.js`, shared navigation partials in `assets/partials/`

---

## File Structure

- Modify: `.gitignore`
  - Ignore `.superpowers/` and `.worktrees/` so local brainstorming/worktree artifacts stay out of git status.
- Modify: `index.html`
  - Replace the current combined cover + content layout with a two-state homepage entrance that preserves the cover shape and reveals two large route panels.
- Create: `curriculum-vitae.html`
  - Formal academic route page aggregating research, education list, and open source content using existing multilingual patterns.
- Create: `general.html`
  - General-interest destination containing the current homepage body content.
- Modify: `assets/partials/subnav.html`
  - Reduce navigation links to homepage and blog while preserving the global language switcher.
- Modify: `assets/css/styles.css`
  - Add homepage entrance state styles, split-entry styles, responsive behavior, and any shared route-panel styling needed by the new pages.
- Modify: `assets/js/script.js`
  - Add homepage state transition behavior and keep the existing global language switching working across the new homepage structure.

### Task 1: Prepare isolated workspace and baseline

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Verify `.worktrees/` is now ignored**

Run: `git check-ignore -q .worktrees .superpowers`
Expected: success exit status with no output

- [ ] **Step 2: Commit ignore-rule setup on the current branch before creating the worktree**

```bash
git add .gitignore docs/superpowers/specs/2026-06-12-homepage-split-design.md docs/superpowers/plans/2026-06-12-homepage-split.md
git commit -m "docs: add homepage split spec and plan"
```

- [ ] **Step 3: Create the worktree and feature branch**

```bash
mkdir -p .worktrees
git worktree add .worktrees/homepage-split -b feat/homepage-split
```

- [ ] **Step 4: Verify branch and workspace**

Run: `git -C .worktrees/homepage-split branch --show-current`
Expected: `feat/homepage-split`

- [ ] **Step 5: Check for project setup requirements**

Run: `rg --files -g 'package.json' -g 'Cargo.toml' -g 'requirements.txt' -g 'pyproject.toml'`
Expected: either no matches or the relevant project manifest list

### Task 2: Rebuild `index.html` into a two-state entrance page

**Files:**
- Modify: `index.html`
- Modify: `assets/css/styles.css`
- Modify: `assets/js/script.js`

- [ ] **Step 1: Write the failing structural expectation by inspection**

Target structure to add inside `index.html`:

```html
<body class="homepage-shell">
  <nav class="topnav">
    <!-- language switcher only -->
  </nav>

  <main class="homepage-main">
    <section class="home-cover" id="top">
      <button class="cover-enter-zone" type="button">
        <span data-lang="zh">点击任意位置以进入</span>
        <span data-lang="en" style="display: none;">Click anywhere to enter</span>
      </button>
      <div class="h1-container">...</div>
    </section>

    <section class="home-split" aria-labelledby="homeSplitTitle">
      <h2 id="homeSplitTitle" class="sr-only">Homepage routes</h2>
      <a class="route-panel route-panel-academic" href="curriculum-vitae.html">...</a>
      <a class="route-panel route-panel-general" href="general.html">...</a>
    </section>
  </main>
</body>
```

- [ ] **Step 2: Implement the new homepage markup**

```html
<div class="nav-right">
  <div class="global-lang-switcher">
    <button class="global-lang-button" aria-label="切换语言">
      <i class="fas fa-language"></i>
    </button>
    <ul class="global-lang-menu">
      <li data-lang="zh" class="active">汉语</li>
      <li data-lang="en">English</li>
    </ul>
  </div>
</div>
```

```html
<section class="home-split" aria-labelledby="homeSplitTitle">
  <h2 id="homeSplitTitle" class="sr-only">
    <span data-lang="zh">主页入口</span>
    <span data-lang="en" style="display: none;">Homepage Entrances</span>
  </h2>
  <a class="route-panel route-panel-academic" href="curriculum-vitae.html">
    <span class="route-kicker" data-lang="zh">给只看正式材料的人</span>
    <span class="route-kicker" data-lang="en" style="display: none;">For formal readers</span>
    <span class="route-title" data-lang="zh">治学</span>
    <span class="route-title" data-lang="en" style="display: none;">Academic</span>
  </a>
  <a class="route-panel route-panel-general" href="general.html">
    <span class="route-kicker" data-lang="zh">给想看全貌的人</span>
    <span class="route-kicker" data-lang="en" style="display: none;">For the fuller portrait</span>
    <span class="route-title" data-lang="zh">杂览</span>
    <span class="route-title" data-lang="en" style="display: none;">General</span>
  </a>
</section>
```

- [ ] **Step 3: Add homepage state classes and reveal animation styles**

```css
.homepage-shell {
    min-height: 100vh;
}

.home-cover {
    position: fixed;
    inset: 0;
    z-index: 20;
    cursor: pointer;
    overflow: hidden;
}

.home-cover::before,
.home-cover::after {
    content: "";
    position: absolute;
    top: 0;
    bottom: 0;
    width: 50%;
    background: var(--primary-color);
    transition: transform 0.8s ease;
}

.home-cover::before { left: 0; }
.home-cover::after { right: 0; }

.homepage-shell.home-entered .home-cover::before {
    transform: translateX(-100%);
}

.homepage-shell.home-entered .home-cover::after {
    transform: translateX(100%);
}
```

- [ ] **Step 4: Add interaction logic in `assets/js/script.js`**

```js
const homepageShell = document.querySelector('.homepage-shell');
const coverEnterZone = document.querySelector('.cover-enter-zone');

if (homepageShell && coverEnterZone) {
    const enterHomepage = () => {
        homepageShell.classList.add('home-entered');
        coverEnterZone.setAttribute('aria-hidden', 'true');
    };

    coverEnterZone.addEventListener('click', enterHomepage);
    coverEnterZone.addEventListener('keydown', e => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            enterHomepage();
        }
    });
}
```

- [ ] **Step 5: Run a static sanity check**

Run: `rg -n "cover-enter-zone|home-split|curriculum-vitae.html|general.html" index.html assets/css/styles.css assets/js/script.js`
Expected: matches in all three files

### Task 3: Create the `Curriculum Vitae` page

**Files:**
- Create: `curriculum-vitae.html`
- Modify: `assets/css/styles.css`

- [ ] **Step 1: Write the page scaffold using the existing subnav pattern**

```html
<div id="siteSubnav"
     data-subnav-title-zh="履历"
     data-subnav-title-en="Curriculum Vitae"></div>
```

- [ ] **Step 2: Implement multilingual formal sections**

```html
<section class="lang-switchable">
  <div class="section-header">
    <h2 data-lang="zh">研究</h2>
    <h2 data-lang="en" style="display: none;">Research</h2>
    <div class="lang-switcher">...</div>
  </div>
  <div class="lang-content active" data-lang="zh">...</div>
  <div class="lang-content" data-lang="en" style="display: none;">...</div>
</section>
```

Required content units:

- research: current interests, publications pointer, formal links
- education: list only, no commentary block
- open source: current project/resource listings

- [ ] **Step 3: Reuse and, if needed, lightly extend list styling**

```css
.cv-section .proj-list,
.cv-section .edu-list {
    margin-top: 16px;
}
```

- [ ] **Step 4: Run a static sanity check**

Run: `rg -n "Curriculum Vitae|履历|Research|Education|Open Source" curriculum-vitae.html`
Expected: all required sections present

### Task 4: Move the current homepage body into `general.html`

**Files:**
- Create: `general.html`

- [ ] **Step 1: Copy the current post-cover homepage sections into the new page scaffold**

```html
<div id="siteSubnav"
     data-subnav-title-zh="杂览"
     data-subnav-title-en="General"></div>
```

- [ ] **Step 2: Preserve the existing section-local multilingual structure**

Required sections to migrate from the old homepage body:

- research
- open source
- reading
- education

The migrated markup should retain the existing `.lang-switchable`, `.section-header`, `.lang-switcher`, `.lang-content`, and `data-lang` structure.

- [ ] **Step 3: Remove those body sections from `index.html` after migration**

Expected remaining homepage content:

- the fixed cover state
- the revealed route panels
- shared footer

- [ ] **Step 4: Run a static sanity check**

Run: `rg -n "data-section-id=\"research\"|开源|阅读|教育" general.html`
Expected: the migrated sections are present in `general.html`

### Task 5: Simplify shared navigation

**Files:**
- Modify: `assets/partials/subnav.html`

- [ ] **Step 1: Replace the current nav links with homepage + blog only**

```html
<div class="nav-links" id="navLinks">
  <a href="index.html">
    <span data-lang="zh">主页</span>
    <span data-lang="en" style="display: none;">Home</span>
  </a>
  <a href="https://itpyi.site/blog">
    <span data-lang="zh">博客</span>
    <span data-lang="en" style="display: none;">Blog</span>
  </a>
</div>
```

- [ ] **Step 2: Verify nav labels still participate in global language switching**

Run: `rg -n "主页|Home|博客|Blog" assets/partials/subnav.html`
Expected: one homepage link and one blog link only

### Task 6: Verify final state

**Files:**
- Modify: `index.html`
- Modify: `curriculum-vitae.html`
- Modify: `general.html`
- Modify: `assets/partials/subnav.html`
- Modify: `assets/css/styles.css`
- Modify: `assets/js/script.js`

- [ ] **Step 1: Run a final grep-based structure check**

Run: `rg -n "curriculum-vitae.html|general.html|Click anywhere to enter|点击任意位置以进入|主页|博客" index.html general.html curriculum-vitae.html assets/partials/subnav.html assets/js/script.js`
Expected: all new routes, prompt text, and simplified nav entries found

- [ ] **Step 2: Start a local static server for manual verification**

Run: `python3 -m http.server 8000`
Expected: server starts successfully on port 8000

- [ ] **Step 3: Manually verify in browser**

Check:

- homepage cover shape remains recognizably the current one
- homepage nav shows only language switcher
- clicking anywhere enters the split homepage
- split homepage links go to `curriculum-vitae.html` and `general.html`
- subpages show only homepage + blog in nav
- global language switcher still defaults to `汉语`

- [ ] **Step 4: Check git status in the worktree**

Run: `git status --short`
Expected: only the intended homepage-refactor files are modified or added

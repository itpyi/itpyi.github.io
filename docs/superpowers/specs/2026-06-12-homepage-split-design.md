# Homepage Split Design

## Goal

Restructure the site entry flow so the landing experience separates two audiences without abandoning the current cover-page identity. The homepage should first present the existing motto-led cover, then transition in place to a two-route entrance: one route for formal academic readers and one route for general-interest readers.

## Existing Context

- The current `index.html` combines the cover and the entire homepage body in one scrollable page.
- The cover has a distinct vertical layout that should be preserved in shape and overall visual composition.
- The site already has a global language system built around `data-lang="zh|en"` plus optional section-local language menus for pages that expose more languages.
- The site default is `zh` / `汉语`, not English.
- Subpages currently inject a common sub-navigation partial.

## Audience Split

The new landing structure should explicitly distinguish two reading modes:

- `治学 / Academic`: for visitors who only want formal professional material
- `杂览 / General`: for visitors who want the broader, more personal site

Content overlap between the two routes is intentional. The academic path is a narrow dossier; the general path is the fuller portrait.

## Homepage Behavior

`index.html` remains a single page but has two visual states.

### State 1: Cover

- Preserve the current cover-page shape, including the vertical title and motto layout.
- Remove all navigation links except the existing global language switcher.
- Replace the current auxiliary prompt with a multilingual enter prompt using the existing language-switching mechanism:
  - `zh`: `点击任意位置以进入`
  - `en`: `Click anywhere to enter`
- Clicking anywhere on the cover transitions the page into the next state.

### State 2: Revealed Split Homepage

- The page does not navigate away. Instead, `index.html` itself becomes the two-column entrance page.
- The cover retreats outward from the center line, revealing the homepage beneath it.
- The revealed homepage presents two large equal-weight entrance panels:
  - left: `治学` / `Academic`
  - right: `杂览` / `General`
- Each panel is a large clickable target.
- This split page should feel quiet, editorial, and restrained rather than heavily illustrative.

## Navigation Changes

All page navigation should be simplified.

- Keep the global language switcher.
- Keep a link to the homepage entrance page.
- Keep a link to the blog.
- Remove standalone navigation links to research and about.

This applies both to the homepage top navigation and to the shared subpage navigation partial.

## Academic Route

Create a new formal page titled `Curriculum Vitae`.

### Purpose

This page is the destination for the `治学 / Academic` entrance. It is a concise formal page for readers who only want professional information.

### Content

It aggregates material that is currently split across multiple pages:

- research
- education
- open source

### Presentation Rules

- Research content should be represented here in a compact formal way.
- Education should appear as a list only, without the discursive commentary currently present on the education page.
- Open-source content should appear as part of the same formal dossier.
- The page remains multilingual and should continue to use the site’s existing language architecture, leaving room for future sections that support more than `zh` and `en`.

## General Route

The `杂览 / General` route should lead to a page containing the current homepage body content.

### Purpose

This page is the fuller portrait page for general-interest readers.

### Content

It should contain what currently appears below the cover on `index.html`, including the existing sections such as:

- research
- open source
- reading
- education

Repetition with the `Curriculum Vitae` page is expected and should be preserved.

## Multilingual Requirements

The redesign must preserve the site’s extensive language architecture.

- Keep the current global `zh` / `en` switching logic intact.
- Default language remains `zh`.
- Use the existing menu labels and conventions already present in the project, including `汉语`.
- Do not collapse the architecture into a simple bilingual-only assumption.
- Pages that currently allow richer per-section language variation should continue to be structurally compatible with that approach.

## Responsive Behavior

The cover must remain visually faithful on narrow screens while still supporting the new interaction.

- The cover layout should preserve its current identity rather than being replaced by a different mobile hero.
- The enter prompt should not interfere with the vertical title block.
- The two-column revealed homepage may collapse into a vertical stack on narrow screens, but the sense of two equal entrances should remain clear.
- Touch interaction should work by tapping anywhere on the cover.

## Implementation Boundaries

- Reuse the existing `assets/js/script.js` language-switching behavior rather than introducing a second language system.
- Reuse shared styles where sensible, but add homepage-specific classes for the two-state interaction.
- Keep old pages unless they need to be repurposed as destinations in the new structure.
- Avoid unnecessary visual invention beyond what is required to support the new cover-to-split transition.

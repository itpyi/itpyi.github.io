#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build.py — 揽月阁（itpyi.site）站点构建脚本

把 Markdown 与 JSON 数据渲染为完整 HTML 页面，输出到 _site/ 目录
（_site/ 是纯产物，已 gitignore，可整体删除重建）。

依赖（见 requirements.txt）：仅 PyYAML（解析 front matter）。
Markdown 渲染器内置于本文件（render_markdown），是一个只覆盖站点内容
所需子集的轻量实现——段落、列表、链接、原始 HTML 透传。复杂样式请直接
在正文里写原始 HTML（如 <p class="research-topic">…</p>）。

流水线（按顺序执行，任何一步出错都立即报错退出）：

 1. 解析命令行参数（--output，默认 _site），清空旧输出目录。
 2. 加载 data/site.json —— 站点全局字符串（机构名、相关链接、语言显示名、
    站点 URL）。正文与数据文件里可用 {{ site.机构.语言 }} 引用其中任何值，
    例如 {{ site.institute.zh }}，实现「改一处，全站生效」。
 3. 逐页处理 templates/pages/*.html。每个模板 = YAML front matter
    （「页面清单」：标题、meta、子导航标题、脚本、节列表）+ HTML 骨架
    （含 {{ 大写占位符 }}）。骨架里的节内容由本脚本生成后替换进去。
 4. 按页面清单逐节渲染，按 kind 分发：
      content       Markdown 内容节。正文按「语言围栏」分块：
                    <!-- lang:zh --> … <!-- lang:en --> …
                    <!-- page:academics lang:zh --> … 是单页覆盖块
                    （默认块改一处全站生效；page: 块只改指定一页）。
                    渲染后做视觉保真后处理（见 render_markdown）。
      links         相关链接节（data/site.json 的 links 列表）。
      publications  学术论文节：只发占位 <div data-publications>，
                    内容由浏览器端 assets/js/publications.js 读取
                    assets/data/publications.bib 渲染（保持现状）。
      projects      开源项目节（academics 页视图，data/projects.json）。
      projects_page opensource.html 整页的英文分组视图（data/projects.json）。
      education     教育经历节（data/education.json）。
 5. 页面组装：把标题 / meta / 子导航 / 节 / 脚本替换进骨架。任何残留的
    未替换 {{ 占位符 }} 都会报错（宁吵勿静默）。
 6. 渲染 templates/partials/footer.html（注入「最后更新」日期与版权年份）
    到 _site/assets/partials/footer.html —— script.js 仍在浏览器端 fetch 它。
    「最后更新」日期 = content/ data/ templates/ 中最新一次提交的日期
    （git log），无提交记录时用构建当天。
 7. 静态拷贝 assets/ 整体到 _site/assets/（css/js/字体/图片/PDF/bib/books.json
    原样不动），并拷入 CNAME 与 Google 验证文件（自定义域名与站长验证依赖它们）。
 8. 生成 robots.txt 与 sitemap.xml（域名取自 site.json 的 url 字段，
    每个页面的 lastmod 用该页内容源的最近提交日期）。
 9. 结束：打印构建摘要。缺文件、坏 front matter、坏数据都会让构建失败。

用法：
    python3 build.py                        # 构建到 _site/
    python3 -m http.server 8000 -d _site    # 本地预览
"""

import argparse
import datetime
import html
import json
import re
import shutil
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

try:
    import yaml
except ImportError as exc:
    sys.exit(f"缺少构建依赖：{exc}\n请先运行：pip install -r requirements.txt")

ROOT = Path(__file__).resolve().parent
PAGES_DIR = ROOT / "templates" / "pages"
PARTIALS_DIR = ROOT / "templates" / "partials"
CONTENT_DIR = ROOT / "content"
DATA_DIR = ROOT / "data"
ASSETS_DIR = ROOT / "assets"

VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}

# 语言围栏：<!-- lang:zh --> 或 <!-- page:academics lang:en -->
LANG_FENCE = re.compile(r"^<!--\s*(?:page:([\w-]+)\s+)?lang:([\w-]+)\s*-->\s*$")

# {{ site.path }} —— 引用 site.json 中的值
SITE_PLACEHOLDER = re.compile(r"\{\{\s*site\.([\w.]+)\s*\}\}")

# 模板骨架中的 {{ 大写占位符 }}
TEMPLATE_PLACEHOLDER = re.compile(r"\{\{\s*([A-Z][A-Z0-9_]*)\s*\}\}")


class BuildError(Exception):
    """构建失败：信息直接面向站点维护者。"""


# ---------------------------------------------------------------- 小工具

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_front_matter(path):
    """读文件并解析 YAML front matter（文件开头的 --- 分隔块，对 .md 与
    .html 模板同样适用）。没有 front matter 时返回 ({}, 全文)。"""
    if not path.exists():
        raise BuildError(f"文件不存在：{path.relative_to(ROOT)}")
    raw = path.read_text(encoding="utf-8")
    if raw.startswith("---"):
        end = raw.find("\n---", 3)
        if end == -1:
            raise BuildError(f"{path.relative_to(ROOT)} 的 front matter 缺少结束标记 ---")
        metadata = yaml.safe_load(raw[3:end]) or {}
        body = raw[end + 4:].lstrip("\n")
        return metadata, body
    return {}, raw


def substitute_site(text, site):
    """把正文/数据里的 {{ site.path }} 替换成 site.json 中的对应字符串。"""

    def repl(m):
        node = site
        for key in m.group(1).split("."):
            if not isinstance(node, dict) or key not in node:
                raise BuildError(f"site.json 中没有键 site.{m.group(1)}")
            node = node[key]
        if not isinstance(node, str):
            raise BuildError(f"site.{m.group(1)} 不是字符串，无法替换进文本")
        return node

    return SITE_PLACEHOLDER.sub(repl, text)


def substitute_meta(obj, site):
    """递归替换 YAML front matter / JSON 数据中所有字符串里的 {{ site.* }}。"""
    if isinstance(obj, str):
        return substitute_site(obj, site)
    if isinstance(obj, list):
        return [substitute_meta(x, site) for x in obj]
    if isinstance(obj, dict):
        return {k: substitute_meta(v, site) for k, v in obj.items()}
    return obj


def git_last_commit_date(paths):
    """paths 中任一文件的最近提交日期（YYYY-MM-DD）；查不到则返回 None。"""
    existing = [str(p) for p in paths if p.exists()]
    if not existing:
        return None
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", *existing],
            cwd=ROOT, capture_output=True, text=True, check=True,
        )
    except (subprocess.CalledProcessError, OSError):
        return None
    date = out.stdout.strip()
    return date or None


# ---------------------------------------------------------------- Markdown 渲染

def split_lang_blocks(body):
    """把正文按语言围栏拆成 [(page, lang, text)]；page 为 None 表示默认块。"""
    blocks = []
    cur_page = cur_lang = None
    cur_lines = []

    def flush():
        nonlocal cur_page, cur_lang, cur_lines
        if cur_lang is not None and cur_lines:
            blocks.append((cur_page, cur_lang, "\n".join(cur_lines).strip("\n")))
        cur_page, cur_lang, cur_lines = None, None, []

    for line in body.splitlines():
        m = LANG_FENCE.match(line.strip())
        if m:
            flush()
            cur_page, cur_lang = m.group(1), m.group(2)
        elif cur_lang is not None:
            cur_lines.append(line)
    flush()
    return blocks


def select_block(blocks, page_id, lang):
    """为 (page_id, lang) 选正文块：page 限定块优先于默认块；同组内后者覆盖前者。"""
    chosen = None
    for bpage, blang, text in blocks:
        if blang != lang:
            continue
        if page_id is not None and bpage is not None and bpage != page_id:
            continue
        if page_id is not None and bpage == page_id:
            chosen = text
        elif bpage is None and chosen is None:
            chosen = text
    return chosen


def is_external_link(href):
    """绝对 http(s) 链接与相对的非 HTML 资源（如 PDF）都按外链处理：
    需要 target="_blank"（在新标签打开）。内部 .html 链接不加 target，
    因为 script.js 的 ?lang= 语言传播会跳过带 target 的链接。"""
    if not href:
        return False
    h = href.strip().lower()
    if h.startswith(("http://", "https://")):
        return True
    if h.startswith(("#", "mailto:")):
        return False
    if h.endswith(".html") or ".html#" in h or ".html?" in h:
        return False
    return True


class _PostProcessor(HTMLParser):
    """视觉保真后处理（对照 styles.css 验证过，缺了会改变观感）：

    1. 无 class 的 <a> → 加 class="link-body"（样式表没有裸 a 样式）；
    2. 无 class 的 <ul> → 加 class="body-list"（样式表没有裸 ul 样式）；
    3. 外链加 target="_blank" rel="noopener"（内部 .html 链接绝不动）。
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []

    def emit_start(self, tag, attrs, self_closing=False):
        a = dict(attrs)
        if tag == "a":
            if not a.get("class"):
                a["class"] = "link-body"
            if "target" not in a and is_external_link(a.get("href", "")):
                a["target"] = "_blank"
                if "rel" not in a:
                    a["rel"] = "noopener"
        elif tag == "ul":
            if not a.get("class"):
                a["class"] = "body-list"
        attr_str = "".join(f' {k}="{html.escape(v, quote=True)}"' for k, v in a.items())
        self.out.append(f"<{tag}{attr_str}{' /' if self_closing else ''}>")

    def handle_starttag(self, tag, attrs):
        self.emit_start(tag, attrs, tag in VOID_ELEMENTS)

    def handle_startendtag(self, tag, attrs):
        self.emit_start(tag, attrs, True)

    def handle_endtag(self, tag):
        if tag not in VOID_ELEMENTS:
            self.out.append(f"</{tag}>")

    def handle_data(self, data):
        self.out.append(html.escape(data, quote=False))

    def handle_comment(self, data):
        self.out.append(f"<!--{data}-->")


# 轻量 Markdown 渲染器（内置，无第三方依赖）。覆盖站点内容需要的子集：
#   - 空行分段 → <p>…</p>（同一段内的换行按软换行合并为一个空格）
#   - "- " 开头的连续行 → <ul>…</ul>
#   - [文本](链接) → <a href="…">文本</a>（链接内不能含空格与右括号）
#   - 以 < 开头、以 > 结尾的整行 → 原始 HTML 块，原样透传
#     （样式化元素的逃生口，如 <p class="research-topic">…</p>）
#   - 反斜杠转义（如 \* 输出字面星号）
# 不支持的语法（标题、嵌套列表、表格、加粗等）请直接用原始 HTML 代替。

_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")

_ESCAPE_RE = re.compile(r"\\([\\`*{}\[\]()#+.!_>-])")


def _inline(text):
    """行内渲染：先处理反斜杠转义，再处理 [文本](链接)，其余文本做 HTML 转义。"""
    text = _ESCAPE_RE.sub(r"\1", text)
    parts = []
    pos = 0
    for m in _LINK_RE.finditer(text):
        parts.append(html.escape(text[pos:m.start()]))
        parts.append(
            f'<a href="{html.escape(m.group(2), quote=True)}">{html.escape(m.group(1))}</a>'
        )
        pos = m.end()
    parts.append(html.escape(text[pos:]))
    return "".join(parts)


def _is_raw_html_line(line):
    return line.startswith("<") and line.endswith(">")


def render_markdown(text, site):
    """{{ site.* }} 替换 → 轻量 Markdown → HTML → 视觉保真后处理。"""
    lines = substitute_site(text, site).split("\n")
    blocks = []
    para = []

    def flush_para():
        if para:
            blocks.append("<p>" + _inline(" ".join(para)) + "</p>")
            para.clear()

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            flush_para()
            i += 1
            continue
        if line.startswith("- "):
            flush_para()
            items = []
            while i < len(lines) and lines[i].strip().startswith("- "):
                items.append("<li>" + _inline(lines[i].strip()[2:]) + "</li>")
                i += 1
            blocks.append("<ul>\n" + "\n".join(items) + "\n</ul>")
            continue
        if _is_raw_html_line(line):
            flush_para()
            blocks.append(line)
            i += 1
            continue
        para.append(line)
        i += 1
    flush_para()
    return _postprocess("\n".join(blocks))


def _postprocess(html_text):
    parser = _PostProcessor()
    parser.feed(html_text)
    parser.close()
    return "".join(parser.out)


def render_meta(text, site):
    """渲染单段文本（list-meta 里的内容）：与 render_markdown 相同，但剥掉外层
    <p>。契约：JSON 中的 summary / notes / metas 字段必须是恰好一段。"""
    html_text = render_markdown(text, site)
    if html_text.startswith("<p>") and html_text.endswith("</p>"):
        inner = html_text[3:-4]
        if "<p>" not in inner:
            return inner
    return html_text


# ---------------------------------------------------------------- 节渲染器

def assemble_switchable_section(title, langs, bodies, site,
                                extra_class=None, section_id=None,
                                data_section_id=None):
    """可切换语言节（.lang-switchable）。DOM 契约由 script.js / styles.css 决定，
    必须精确：

    - 只有默认语言（langs 第一个）的 h2 无内联样式，其余 h2 带
      style="display: none;"；
    - 只有默认语言的 .lang-content 有 class="lang-content active"，其余带
      class="lang-content" style="display: none;"；
    - .lang-menu 的 <li data-lang> 列表：默认语言在前且 class="active"，
      显示名取自 site.json 的 lang_labels（缺省时直接用语言码，可扩展）；
    - title: {lang: 标题}；bodies: {lang: html}，某语言无正文时只发
      h2 与菜单项、不发 lang-content（about 页「仅中文」节的现状）。
    """
    default = langs[0]
    classes = "lang-switchable" + (f" {extra_class}" if extra_class else "")
    attrs = f' class="{classes}"'
    if section_id:
        attrs += f' id="{section_id}"'
    if data_section_id:
        attrs += f' data-section-id="{data_section_id}"'

    lines = [f"<section{attrs}>", '    <div class="section-header">']
    for lang in langs:
        style = "" if lang == default else ' style="display: none;"'
        lines.append(f'        <h2 data-lang="{lang}"{style}>{title[lang]}</h2>')
    lines.extend([
        '        <div class="lang-switcher">',
        '            <button class="lang-button" aria-label="切换语言">',
        '                <i class="fas fa-language"></i>',
        "            </button>",
        '            <ul class="lang-menu">',
    ])
    labels = site.get("lang_labels", {})
    for lang in langs:
        active = ' class="active"' if lang == default else ""
        label = labels.get(lang, lang)
        lines.append(f'                <li data-lang="{lang}"{active}>{label}</li>')
    lines.extend([
        "            </ul>",
        "        </div>",
        "    </div>",
    ])
    for lang in langs:
        body = bodies.get(lang)
        if body is None:
            continue
        if lang == default:
            lines.append(f'    <div class="lang-content active" data-lang="{lang}">')
        else:
            lines.append(f'    <div class="lang-content" data-lang="{lang}" style="display: none;">')
        lines.append(body.strip("\n"))
        lines.append("    </div>")
    lines.append("</section>")
    return "\n".join(lines)


def assemble_plain_section(title, body, extra_class=None, section_id=None):
    """纯节（switchable: false）：<section><h2>标题</h2>正文</section>，
    不区分语言（如 research.html 的英文节、education.html 的「评论」节）。"""
    classes = extra_class or ""
    attrs = f' class="{classes}"' if classes else ""
    if section_id:
        attrs += f' id="{section_id}"'
    lines = [f"<section{attrs}>"]
    if title:
        lines.append(f"    <h2>{title}</h2>")
    if body:
        lines.append(body.strip("\n"))
    lines.append("</section>")
    return "\n".join(lines)


def render_content_section(entry, page_id, site, deps):
    """kind: content —— Markdown 内容节。

    页面清单可覆盖 md 自带 front matter 的以下键：
      switchable（默认 true，false 为纯节）、class、id、data-section-id、bare。
    """
    path = ROOT / entry["content"]
    deps.add(path)
    meta, body_text = load_front_matter(path)
    meta = substitute_meta(meta, site)

    title = meta.get("title", "")
    switchable = meta.get("switchable", entry.get("switchable", True))
    bare = meta.get("bare", entry.get("bare", False))
    blocks = split_lang_blocks(body_text)

    if not switchable:
        # 纯节：标题为字符串；正文取第一个围栏块（无围栏时取全文）
        if not isinstance(title, str):
            raise BuildError(f"{path.name} 是纯节，title 应为字符串而非多语言字典")
        text = blocks[0][2] if blocks else body_text
        body = render_markdown(text, site) if text.strip() else ""
        if bare:
            return body
        return assemble_plain_section(
            title, body,
            entry.get("class") or meta.get("class"),
            entry.get("id"),
        )

    if not isinstance(title, dict):
        raise BuildError(f"{path.name} 是可切换节，title 应为 {{语言: 标题}} 字典")
    langs = meta.get("langs") or list(title)
    bodies = {}
    for lang in langs:
        text = select_block(blocks, page_id, lang)
        if text is None or not text.strip():
            bodies[lang] = None
        else:
            bodies[lang] = render_markdown(text, site)
    if bare:
        return next((b for b in bodies.values() if b is not None), "")
    return assemble_switchable_section(
        title, langs, bodies, site,
        extra_class=entry.get("class") or meta.get("class"),
        section_id=entry.get("id"),
        data_section_id=entry.get("data-section-id"),
    )


def render_links_section(entry, page_id, site, deps):
    """kind: links —— 相关链接节（data/site.json 的 links 列表）。

    switchable（默认）: 双语可切换节，链接列表按语言各复制一份（与现状一致，
    链接名是专有名词，两种语言相同）；
    switchable: false + title 字符串: 纯节（research.html 的 More links）。
    list_class: ul 的 class，默认 body-list；null 表示裸 ul（research.html 现状）。
    """
    links = site.get("links", [])
    if not links:
        raise BuildError("site.json 缺少 links")
    if not entry.get("title"):
        raise BuildError(f"{page_id} 页的 links 节缺少 title")
    list_class = entry.get("list_class", "body-list")

    def render_ul():
        cls = f' class="{list_class}"' if list_class else ""
        items = "\n".join(
            f'        <li><a class="link-body" href="{l["url"]}" target="_blank" rel="noopener">{l["label"]}</a></li>'
            for l in links
        )
        return f"    <ul{cls}>\n{items}\n    </ul>"

    title = entry.get("title")
    if not entry.get("switchable", True):
        return assemble_plain_section(title, render_ul(), entry.get("class"), entry.get("id"))
    langs = list(title)
    return assemble_switchable_section(
        title, langs, {lang: render_ul() for lang in langs}, site,
        entry.get("class"), entry.get("id"),
    )


def render_publications_section(entry, page_id, site, deps):
    """kind: publications —— 学术论文节。只发占位 <div data-publications>，
    浏览器端 publications.js 读取 assets/data/publications.bib 渲染（保持现状）。"""
    if not entry.get("title"):
        raise BuildError(f"{page_id} 页的 publications 节缺少 title")
    title = entry["title"]
    langs = list(title)
    return assemble_switchable_section(
        title, langs, {lang: "<div data-publications></div>" for lang in langs},
        site, entry.get("class"), entry.get("id"),
    )


def render_projects_section(entry, page_id, site, deps):
    """kind: projects —— 开源项目节（academics 页的平铺视图，双语）。"""
    path = DATA_DIR / "projects.json"
    deps.add(path)
    data = load_json(path)
    if not entry.get("title"):
        raise BuildError(f"{page_id} 页的 projects 节缺少 title")
    title = entry["title"]
    langs = list(title)
    bodies = {}
    for lang in langs:
        parts = []
        if entry.get("intro"):
            ipath = ROOT / entry["intro"]
            deps.add(ipath)
            _, intro_body = load_front_matter(ipath)
            text = select_block(split_lang_blocks(intro_body), page_id, lang)
            if text and text.strip():
                parts.append(render_markdown(text, site))
        ul = ['    <ul class="proj-list">']
        for pid in data.get("academics_items", []):
            proj = data["projects"][pid]
            ul.append('        <li class="list-item">')
            ul.append(f'            <span class="list-title">{proj["title"][lang]}</span>')
            ul.append(f'            <div class="list-meta">{render_meta(proj["summary"][lang], site)}</div>')
            for note in proj.get("notes", {}).get(lang, []):
                ul.append(f'            <div class="list-meta">{render_meta(note, site)}</div>')
            ul.append('            <div class="list-links">')
            for l in proj.get("links", []):
                label = l["label"] if isinstance(l["label"], str) else l["label"][lang]
                ul.append(f'                <a href="{l["url"]}" class="list-link" target="_blank" rel="noopener">{label}</a>')
            ul.append('            </div>')
            ul.append('        </li>')
        ul.append("    </ul>")
        parts.append("\n".join(ul))
        bodies[lang] = "\n".join(parts)
    return assemble_switchable_section(title, langs, bodies, site, entry.get("class"), entry.get("id"))


def render_projects_page(entry, page_id, site, deps):
    """kind: projects_page —— opensource.html 整页：两个分组纯节（英文视图）。
    每个项目取 page_en 字段（缺省时回退 title.en / summary.en / links）。"""
    path = DATA_DIR / "projects.json"
    deps.add(path)
    data = load_json(path)
    projects = data["projects"]

    intro_html = ""
    if entry.get("intro"):
        ipath = ROOT / entry["intro"]
        deps.add(ipath)
        _, intro_body = load_front_matter(ipath)
        blocks = split_lang_blocks(intro_body)
        text = blocks[0][2] if blocks else intro_body
        intro_html = render_markdown(text, site)

    sections = []
    for idx, group in enumerate(data.get("opensource_groups", [])):
        parts = []
        if idx == 0 and intro_html:
            parts.append(intro_html)
        parts.append(f'    <h2>{group["title"]}</h2>')
        ul = ['    <ul class="proj-list">']
        for pid in group["projects"]:
            proj = projects[pid]
            view = proj.get("page_en", {})
            ptitle = view.get("title", proj.get("title", {}).get("en", pid))
            metas = view.get("metas", [proj.get("summary", {}).get("en", "")])
            links = view.get("links")
            if links is None:
                links = [
                    {"label": l["label"].get("en", l["label"]) if isinstance(l["label"], dict) else l["label"],
                     "url": l["url"]}
                    for l in proj.get("links", [])
                ]
            ul.append('        <li class="list-item">')
            ul.append(f'            <span class="list-title">{ptitle}</span>')
            for m in metas:
                ul.append(f'            <div class="list-meta">{render_meta(m, site)}</div>')
            ul.append('            <div class="list-links">')
            for l in links:
                ul.append(f'                <a href="{l["url"]}" class="list-link" target="_blank" rel="noopener">{l["label"]}</a>')
            ul.append('            </div>')
            ul.append('        </li>')
        ul.append("    </ul>")
        parts.append("\n".join(ul))
        sections.append("\n".join(["<section>", *parts, "</section>"]))
    return "\n".join(sections)


def render_education_section(entry, page_id, site, deps):
    """kind: education —— 教育经历节（data/education.json，每条 zh/en）。
    institution / year / details 支持 {{ site.* }} 引用。"""
    path = DATA_DIR / "education.json"
    deps.add(path)
    data = load_json(path)
    if not entry.get("title"):
        raise BuildError(f"{page_id} 页的 education 节缺少 title")
    title = entry["title"]
    langs = list(title)
    bodies = {}
    for lang in langs:
        items = []
        for e in data:
            year = substitute_site(e["year"][lang], site)
            inst = substitute_site(e["institution"][lang], site)
            items.append('    <div class="edu-item">')
            items.append(f'        <div class="edu-year">{year}</div>')
            items.append('        <div class="edu-details">')
            items.append(f'            <div class="edu-institution">{inst}</div>')
            for detail in e["details"][lang]:
                items.append("            " + render_markdown(detail, site).strip("\n"))
            items.append("        </div>")
            items.append("    </div>")
        bodies[lang] = '<div class="edu-list">\n' + "\n".join(items) + "\n</div>"
    return assemble_switchable_section(title, langs, bodies, site, entry.get("class"), entry.get("id"))


RENDERERS = {
    "content": render_content_section,
    "links": render_links_section,
    "publications": render_publications_section,
    "projects": render_projects_section,
    "projects_page": render_projects_page,
    "education": render_education_section,
}


# ---------------------------------------------------------------- 页面组装

def substitute_template(html_text, values):
    """替换 {{ 大写占位符 }}；未提供的占位符一律报错。"""

    def repl(m):
        key = m.group(1)
        if key not in values:
            raise BuildError(f"模板占位符 {{{{ {key} }}}} 没有对应的值")
        return values[key]

    return TEMPLATE_PLACEHOLDER.sub(repl, html_text)


def render_page(template_path, site, deps):
    """渲染一个普通页面（index.html 除外，见 render_index）。"""
    page_id = template_path.stem
    deps.add(template_path)
    manifest, skeleton = load_front_matter(template_path)
    manifest = substitute_meta(manifest, site)

    def field(key, lang):
        value = manifest.get(key, "")
        return value.get(lang, "") if isinstance(value, dict) else value

    sections = []
    for entry in manifest.get("sections", []):
        kind = entry.get("kind", "content")
        renderer = RENDERERS.get(kind)
        if renderer is None:
            raise BuildError(f"{page_id} 页面的节 kind 未知：{kind!r}")
        sections.append(renderer(entry, page_id, site, deps))

    scripts = manifest.get("scripts", [])
    extra_scripts = "\n".join(f'    <script src="{s}"></script>' for s in scripts)

    values = {
        "TITLE_ZH": html.escape(field("title", "zh"), quote=True),
        "TITLE_EN": html.escape(field("title", "en"), quote=True),
        "META_ZH": html.escape(field("meta", "zh"), quote=True),
        "META_EN": html.escape(field("meta", "en"), quote=True),
        "SUBNAV_ZH": html.escape(field("subnav", "zh"), quote=True),
        "SUBNAV_EN": html.escape(field("subnav", "en"), quote=True),
        "SECTIONS": "\n".join(sections),
        "EXTRA_SCRIPTS": extra_scripts,
    }
    result = substitute_template(skeleton, values)
    _reject_leftover_placeholders(result, page_id)
    return result


def render_index(template_path, site, deps):
    """渲染 index.html（首页）：整页骨架 + 全部字符串来自 content/index.md 的
    front matter。"""
    page_id = "index"
    deps.add(template_path)
    skeleton = template_path.read_text(encoding="utf-8")
    index_path = CONTENT_DIR / "index.md"
    deps.add(index_path)
    manifest, _ = load_front_matter(index_path)
    manifest = substitute_meta(manifest, site)

    def field(key, lang):
        value = manifest.get(key, "")
        return value.get(lang, "") if isinstance(value, dict) else value

    quotes = manifest.get("quotes", [])
    quote_html = "\n".join(
        f'                <h2 class="fade-in-{i + 2}"><span class="lead-circle">&#9675;</span>{q}</h2>'
        for i, q in enumerate(quotes)
    )
    routes_html = []
    for route in manifest.get("routes", []):
        title, copy = route["title"], route["copy"]
        routes_html.append(
            f'            <a class="{route["class"]}" href="{route["href"]}">\n'
            '                <span class="route-panel-inner">\n'
            f'                    <span class="route-title" data-lang="zh">{title["zh"]}</span>\n'
            f'                    <span class="route-title" data-lang="en" style="display: none;">{title["en"]}</span>\n'
            f'                    <span class="route-copy" data-lang="zh">{copy["zh"]}</span>\n'
            f'                    <span class="route-copy" data-lang="en" style="display: none;">{copy["en"]}</span>\n'
            "                </span>\n"
            "            </a>"
        )

    values = {
        "TITLE_ZH": html.escape(field("title", "zh"), quote=True),
        "TITLE_EN": html.escape(field("title", "en"), quote=True),
        "META_ZH": html.escape(field("meta", "zh"), quote=True),
        "META_EN": html.escape(field("meta", "en"), quote=True),
        "LOGO_ZH": field("logo", "zh"),
        "LOGO_EN": field("logo", "en"),
        "ENTER_HINT_ZH": field("enter_hint", "zh"),
        "ENTER_HINT_EN": field("enter_hint", "en"),
        "SR_TITLE_ZH": field("sr_title", "zh"),
        "SR_TITLE_EN": field("sr_title", "en"),
        "QUOTES": quote_html,
        "ROUTES": "\n".join(routes_html),
    }
    result = substitute_template(skeleton, values)
    _reject_leftover_placeholders(result, page_id)
    return result


def _reject_leftover_placeholders(text, page_id):
    leftover = TEMPLATE_PLACEHOLDER.search(text)
    if leftover:
        raise BuildError(
            f"{page_id} 页渲染后仍有未替换的占位符：{leftover.group(0)}"
        )


# ---------------------------------------------------------------- footer / robots / sitemap

def render_footer(site, footer_date):
    """渲染 templates/partials/footer.html：注入「最后更新」日期与版权年份。"""
    date = datetime.date.fromisoformat(footer_date)
    months = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]
    values = {
        "LAST_UPDATED_ZH": f"{date.year} 年 {date.month} 月 {date.day} 日",
        "LAST_UPDATED_EN": f"{date.day} {months[date.month - 1]} {date.year}",
        "YEAR": str(datetime.date.today().year),
    }
    path = PARTIALS_DIR / "footer.html"
    if not path.exists():
        raise BuildError(f"缺少页脚模板：{path.relative_to(ROOT)}")
    return substitute_template(path.read_text(encoding="utf-8"), values)


def render_robots(site):
    return (
        "User-agent: *\n"
        "Allow: /\n"
        f"Sitemap: {site['url'].rstrip('/')}/sitemap.xml\n"
    )


def render_sitemap(site, page_deps, fallback_date):
    """每个页面的 lastmod 用该页内容源的最近提交日期，查不到则用构建当天。"""
    url = site["url"].rstrip("/")
    today = fallback_date
    entries = []
    for page in sorted(page_deps):
        lastmod = git_last_commit_date(page_deps[page]) or today
        loc = url + "/" if page == "index" else f"{url}/{page}.html"
        entries.append(f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{lastmod}</lastmod>\n  </url>")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(entries)
        + "\n</urlset>\n"
    )


# ---------------------------------------------------------------- 主流程

def main():
    ap = argparse.ArgumentParser(description="揽月阁站点构建脚本（见文件头部流水线说明）")
    ap.add_argument("--output", default="_site", help="输出目录（默认 _site）")
    args = ap.parse_args()
    out = ROOT / args.output

    # 1. 清空旧输出（_site 是纯产物，可随时删除重建）
    if out.exists():
        shutil.rmtree(out)
    out.mkdir()

    # 2. 站点全局数据
    site = load_json(DATA_DIR / "site.json")
    if "url" not in site:
        raise BuildError("data/site.json 缺少 url 字段")

    # 3-5. 逐页渲染
    page_deps = {}
    for template_path in sorted(PAGES_DIR.glob("*.html")):
        deps = page_deps.setdefault(template_path.stem, set())
        if template_path.stem == "index":
            result = render_index(template_path, site, deps)
        else:
            result = render_page(template_path, site, deps)
        (out / template_path.name).write_text(result, encoding="utf-8")
        print(f"  {template_path.name}")

    # 7. 静态拷贝 assets（含 publications.bib、books.json、subnav.html 原样）
    shutil.copytree(ASSETS_DIR, out / "assets", dirs_exist_ok=True)

    # 6. 页脚（日期 = content/data/templates 最近一次提交，无提交记录用今天），
    #    覆盖上一步拷贝进来的旧 assets/partials/footer.html
    fallback_date = datetime.date.today().isoformat()
    footer_date = (
        git_last_commit_date([CONTENT_DIR, DATA_DIR, ROOT / "templates"])
        or fallback_date
    )
    (out / "assets" / "partials" / "footer.html").write_text(
        render_footer(site, footer_date), encoding="utf-8"
    )

    for name in ("CNAME", "googled77ae0d191b8a2f5.html"):
        src = ROOT / name
        if src.exists():
            shutil.copy2(src, out / name)

    # 8. robots.txt 与 sitemap.xml
    (out / "robots.txt").write_text(render_robots(site), encoding="utf-8")
    (out / "sitemap.xml").write_text(
        render_sitemap(site, page_deps, fallback_date), encoding="utf-8"
    )

    print(f"\n构建完成 → {out.relative_to(ROOT)}/")
    print(f"页脚「最后更新」日期：{footer_date}")
    print(f"本地预览：python3 -m http.server 8000 -d {out.name}")


if __name__ == "__main__":
    try:
        main()
    except BuildError as exc:
        print(f"构建失败：{exc}", file=sys.stderr)
        sys.exit(1)

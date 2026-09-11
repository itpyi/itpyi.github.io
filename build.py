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
 2. 加载 data/site.json —— 唯一的纯构建期配置（站点 URL、语言显示名）。
    内容数据（教育经历、开源项目、相关链接、书单、出版物 bib）都放在
    assets/data/ —— 内容不是构建期配置，会随维护更新，且 publications.bib
    与 books.json 本来就需要在浏览器端被 fetch，同处最自然。
 3. 逐页处理 content/*.md —— **一个页面 = 一个 Markdown 文件**：
      - front matter 是页面元数据（标题、meta、子导航标题、脚本列表、
        可选的 section-class 页面默认节 class）；
      - 正文自上而下就是页面的全部节：每个 `<!-- section {…YAML…} -->`
        围栏开启一节，节内用 `<!-- lang:xx -->` 分语言（语言菜单顺序 =
        语言块出现顺序）；下一节由下一个 section 围栏或文件尾界定。
        调整节顺序 = 拖动节块；加节 = 粘贴一个节块。
      index.md 例外：首页骨架特殊，其字符串全部来自 front matter。
 4. 按节围栏逐节渲染，按 kind 分发：
      content         Markdown 内容节（默认）。渲染后做视觉保真后处理
                      （见 render_markdown）。可切换节（switchable: true，
                      title 为 {语言: 标题} 字典）生成多语结构，语言菜单
                      = title 的键；标题声明了某语言但正文缺失时，该语言
                      显示「该语言版本尚未开发」占位消息。纯节
                      （switchable: false，title 为字符串）生成普通
                      <section>。
      links           相关链接节（assets/data/links.json）。
      publications    学术论文节：只发占位 <div data-publications>，
                      内容由浏览器端 assets/js/publications.js 读取
                      assets/data/publications.bib 渲染（保持现状）。
      projects        开源项目节（academics 页视图，assets/data/projects.json；
                      节正文 = 该节的中英引导段落）。
      projects-group  opensource.html 的英文分组视图（assets/data/projects.json，
                      属性 group: 0/1 指定分组，h2 标题来自数据）。
      education       教育经历节（assets/data/education.json）。
 5. 页面组装：把标题 / meta / 子导航 / 节 / 脚本替换进骨架（除 index 外
    全部页面共用 templates/pages/page.html）。任何残留的未替换
    {{ 占位符 }} 都会报错（宁吵勿静默）。
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
DATA_DIR = ROOT / "data"                    # 纯构建期配置（site.json）
ASSETS_DIR = ROOT / "assets"
CONTENT_DATA_DIR = ASSETS_DIR / "data"      # 站点内容数据（教育/项目/链接/书单/bib）

VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}

# 语言围栏：<!-- lang:zh -->
LANG_FENCE = re.compile(r"^<!--\s+lang:([\w-]+)\s*-->\s*$")

# 节围栏：<!-- section {title: {zh: 研究, en: Research}} -->（花括号内为 YAML flow map）
SECTION_FENCE = re.compile(r"^<!--\s+section\s+(\{.*\})\s*-->\s*$")

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
    """把节正文按语言围栏拆成 [(lang, text)]。围栏之前的内容记作 lang=None
    （纯节允许无围栏，此时整段正文是唯一一块）。"""
    blocks = []
    cur_lang = None
    cur_lines = []
    for line in body.splitlines():
        m = LANG_FENCE.match(line.strip())
        if m:
            blocks.append((cur_lang, "\n".join(cur_lines).strip("\n")))
            cur_lang, cur_lines = m.group(1), []
        else:
            cur_lines.append(line)
    blocks.append((cur_lang, "\n".join(cur_lines).strip("\n")))
    return [(lang, text) for lang, text in blocks if text]


def split_sections(body):
    """把页面 md 正文按节围栏拆成 [(节属性 dict, [(lang, text)])]。"""
    sections = []
    cur_meta = None
    cur_lines = []

    def flush():
        nonlocal cur_meta, cur_lines
        if cur_meta is not None:
            sections.append((cur_meta, split_lang_blocks("\n".join(cur_lines))))
        cur_meta, cur_lines = None, []

    for line in body.splitlines():
        m = SECTION_FENCE.match(line.strip())
        if m:
            flush()
            try:
                cur_meta = yaml.safe_load(m.group(1))
            except yaml.YAMLError as exc:
                raise BuildError(f"节围栏内的 YAML 无法解析：{line.strip()}（{exc}）")
            if not isinstance(cur_meta, dict):
                raise BuildError(f"节围栏内的 YAML 应为映射（{{…}}）：{line.strip()}")
        elif cur_meta is not None:
            cur_lines.append(line)
    flush()
    return sections


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


def render_markdown(text):
    """轻量 Markdown → HTML → 视觉保真后处理。"""
    lines = text.split("\n")
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


def render_meta(text):
    """渲染单段文本（list-meta 里的内容）：与 render_markdown 相同，但剥掉外层
    <p>。契约：JSON 中的 summary / notes / metas 字段必须是恰好一段。"""
    html_text = render_markdown(text)
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


def lang_unavailable_message(lang, site):
    """标题声明了某语言、但正文/数据没有该语言内容时的占位消息（用对应语言
    显示「该语言版本尚未开发」）。正常情况下不应出现，只是防止空白/崩溃的
    稳定性兜底；site.json 的 lang_unavailable 配置各语言文案。"""
    messages = site.get("lang_unavailable", {})
    text = messages.get(lang) or messages.get("en") or f"Language version {lang} is not yet available."
    return f"<p>{html.escape(text)}</p>"


def render_content_section(sec_meta, blocks, site, page_default_class=None):
    """kind: content —— Markdown 内容节（默认 kind）。

    节属性：title（{语言: 标题} 字典 = 可切换节；字符串 = 纯节）、
    switchable（默认 true）、langs（可选，覆盖菜单语言顺序）、class、id、
    data-section-id。页面的 section-class 作为默认 class。

    可切换节的语言菜单 = title 的键（顺序即菜单顺序）。标题声明了某语言
    但正文没有该语言的围栏块时，该语言显示占位消息（lang_unavailable_message）
    而不是空白；正文出现了标题没有声明的语言块则报错（明确的笔误）。"""
    title = sec_meta.get("title", "")
    switchable = sec_meta.get("switchable", True)
    extra_class = sec_meta.get("class") or page_default_class

    if not switchable:
        # 纯节：标题为字符串；正文取第一个语言块（无围栏时即整段正文）
        if not isinstance(title, str):
            raise BuildError("纯节（switchable: false）的 title 应为字符串")
        text = blocks[0][1] if blocks else ""
        body = render_markdown(text) if text.strip() else ""
        return assemble_plain_section(title, body, extra_class, sec_meta.get("id"))

    if not isinstance(title, dict):
        raise BuildError("可切换节的 title 应为 {语言: 标题} 字典")
    langs = sec_meta.get("langs") or list(title)
    if None in [lang for lang, _ in blocks]:
        raise BuildError("可切换节的正文必须用 <!-- lang:xx --> 围栏分块")
    undeclared = {lang for lang, _ in blocks} - set(langs)
    if undeclared:
        raise BuildError(f"节正文有语言块 {sorted(undeclared)}，但标题没有对应的语言键")
    bodies = {}
    for lang in langs:
        text = next((t for l, t in blocks if l == lang), None)
        if text and text.strip():
            bodies[lang] = render_markdown(text)
        else:
            bodies[lang] = lang_unavailable_message(lang, site)
    return assemble_switchable_section(
        title, langs, bodies, site,
        extra_class=extra_class,
        section_id=sec_meta.get("id"),
        data_section_id=sec_meta.get("data-section-id"),
    )


def render_links_section(sec_meta, blocks, site, page_default_class=None):
    """kind: links —— 相关链接节（data/site.json 的 links 列表）。

    可切换节（title 为字典）：链接列表按语言各复制一份（与现状一致，链接名
    是专有名词，两种语言相同）；
    纯节（title 为字符串 + switchable: false）：research.html 的 More links。
    list_class: ul 的 class，默认 body-list；null 表示裸 ul（research.html 现状）。
    """
    path = CONTENT_DATA_DIR / "links.json"
    links = load_json(path)
    if not links:
        raise BuildError("assets/data/links.json 为空")
    title = sec_meta.get("title")
    if not title:
        raise BuildError("links 节缺少 title")
    list_class = sec_meta.get("list_class", "body-list")

    def render_ul():
        cls = f' class="{list_class}"' if list_class else ""
        items = "\n".join(
            f'        <li><a class="link-body" href="{l["url"]}" target="_blank" rel="noopener">{l["label"]}</a></li>'
            for l in links
        )
        return f"    <ul{cls}>\n{items}\n    </ul>"

    extra_class = sec_meta.get("class") or page_default_class
    if not sec_meta.get("switchable", True):
        return assemble_plain_section(title, render_ul(), extra_class, sec_meta.get("id"))
    langs = list(title)
    return assemble_switchable_section(
        title, langs, {lang: render_ul() for lang in langs}, site,
        extra_class, sec_meta.get("id"),
    )


def render_publications_section(sec_meta, blocks, site, page_default_class=None):
    """kind: publications —— 学术论文节。只发占位 <div data-publications>，
    浏览器端 publications.js 读取 assets/data/publications.bib 渲染（保持现状）。"""
    title = sec_meta.get("title")
    if not title:
        raise BuildError("publications 节缺少 title")
    langs = list(title)
    return assemble_switchable_section(
        title, langs, {lang: "<div data-publications></div>" for lang in langs},
        site, sec_meta.get("class") or page_default_class, sec_meta.get("id"),
    )


def render_projects_section(sec_meta, blocks, site, page_default_class=None):
    """kind: projects —— 开源项目节（academics 页的平铺视图，双语）。
    节正文 = 该节的中英引导段落；其后接 projects.json 的 academics 列表。"""
    path = CONTENT_DATA_DIR / "projects.json"
    data = load_json(path)
    title = sec_meta.get("title")
    if not title:
        raise BuildError("projects 节缺少 title")
    langs = [lang for lang, _ in blocks] or list(title)
    bodies = {}
    for lang in langs:
        ids = data.get("academics_items", [])
        projects = data.get("projects", {})
        if any(lang not in projects[pid].get("title", {}) or lang not in projects[pid].get("summary", {})
               for pid in ids):
            bodies[lang] = lang_unavailable_message(lang, site)
            continue
        parts = []
        text = next((t for l, t in blocks if l == lang), None)
        if text and text.strip():
            parts.append(render_markdown(text))
        ul = ['    <ul class="proj-list">']
        for pid in data.get("academics_items", []):
            proj = data["projects"][pid]
            ul.append('        <li class="list-item">')
            ul.append(f'            <span class="list-title">{proj["title"][lang]}</span>')
            ul.append(f'            <div class="list-meta">{render_meta(proj["summary"][lang])}</div>')
            for note in proj.get("notes", {}).get(lang, []):
                ul.append(f'            <div class="list-meta">{render_meta(note)}</div>')
            ul.append('            <div class="list-links">')
            for l in proj.get("links", []):
                label = l["label"] if isinstance(l["label"], str) else l["label"][lang]
                ul.append(f'                <a href="{l["url"]}" class="list-link" target="_blank" rel="noopener">{label}</a>')
            ul.append('            </div>')
            ul.append('        </li>')
        ul.append("    </ul>")
        parts.append("\n".join(ul))
        bodies[lang] = "\n".join(parts)
    return assemble_switchable_section(
        title, langs, bodies, site,
        sec_meta.get("class") or page_default_class, sec_meta.get("id"),
    )


def render_projects_group(sec_meta, blocks, site, page_default_class=None):
    """kind: projects-group —— opensource.html 的英文分组纯节。
    属性 group: 0/1 指定 projects.json 的 opensource_groups 下标；
    h2 标题来自数据；节正文（如有）放在 h2 之前（页面引导段落）。
    每个项目取 page_en 字段（缺省时回退 title.en / summary.en / links）。"""
    path = CONTENT_DATA_DIR / "projects.json"
    data = load_json(path)
    groups = data.get("opensource_groups", [])
    group_idx = sec_meta.get("group")
    if group_idx is None or not (0 <= group_idx < len(groups)):
        raise BuildError(f"projects-group 节的 group 应为 0~{len(groups) - 1} 之间的整数")
    group = groups[group_idx]
    projects = data["projects"]

    parts = []
    text = blocks[0][1] if blocks else ""
    if text.strip():
        parts.append(render_markdown(text))
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
            ul.append(f'            <div class="list-meta">{render_meta(m)}</div>')
        ul.append('            <div class="list-links">')
        for l in links:
            ul.append(f'                <a href="{l["url"]}" class="list-link" target="_blank" rel="noopener">{l["label"]}</a>')
        ul.append('            </div>')
        ul.append('        </li>')
    ul.append("    </ul>")
    parts.append("\n".join(ul))
    return assemble_plain_section("", "\n".join(parts), sec_meta.get("class") or page_default_class, sec_meta.get("id"))


def render_education_section(sec_meta, blocks, site, page_default_class=None):
    """kind: education —— 教育经历节（assets/data/education.json）。
    每条数据的 year / institution / details 按语言提供；标题声明了某语言
    但数据缺少该语言字段时，该语言显示占位消息而不是报错。"""
    path = CONTENT_DATA_DIR / "education.json"
    data = load_json(path)
    title = sec_meta.get("title")
    if not title:
        raise BuildError("education 节缺少 title")
    langs = list(title)
    bodies = {}
    for lang in langs:
        has_all = all(
            lang in e.get("year", {}) and lang in e.get("institution", {}) and lang in e.get("details", {})
            for e in data
        )
        if not has_all:
            bodies[lang] = lang_unavailable_message(lang, site)
            continue
        items = []
        for e in data:
            items.append('    <div class="edu-item">')
            items.append(f'        <div class="edu-year">{e["year"][lang]}</div>')
            items.append('        <div class="edu-details">')
            items.append(f'            <div class="edu-institution">{e["institution"][lang]}</div>')
            for detail in e["details"][lang]:
                items.append("            " + render_markdown(detail).strip("\n"))
            items.append("        </div>")
            items.append("    </div>")
        bodies[lang] = '<div class="edu-list">\n' + "\n".join(items) + "\n</div>"
    return assemble_switchable_section(
        title, langs, bodies, site,
        sec_meta.get("class") or page_default_class, sec_meta.get("id"),
    )


RENDERERS = {
    "content": render_content_section,
    "links": render_links_section,
    "publications": render_publications_section,
    "projects": render_projects_section,
    "projects-group": render_projects_group,
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


def render_page(template_path, page_md_path, site, deps):
    """渲染一个普通页面（index.md 除外，见 render_index）：页面 md 提供
    元数据（front matter）与全部节（正文节围栏），模板只提供骨架。
    除 index 外全部页面共用 templates/pages/page.html。"""
    page_id = page_md_path.stem
    deps.add(page_md_path)
    deps.add(template_path)
    deps.add(DATA_DIR / "site.json")
    manifest, body = load_front_matter(page_md_path)
    skeleton = template_path.read_text(encoding="utf-8")

    def field(key, lang):
        value = manifest.get(key, "")
        return value.get(lang, "") if isinstance(value, dict) else value

    page_default_class = manifest.get("section-class")
    sections = []
    for sec_meta, blocks in split_sections(body):
        kind = sec_meta.get("kind", "content")
        if kind == "links":
            deps.add(CONTENT_DATA_DIR / "links.json")
        if kind == "education":
            deps.add(CONTENT_DATA_DIR / "education.json")
        if kind in ("projects", "projects-group"):
            deps.add(CONTENT_DATA_DIR / "projects.json")
        renderer = RENDERERS.get(kind)
        if renderer is None:
            raise BuildError(f"{page_id} 页面的节 kind 未知：{kind!r}")
        sections.append(renderer(sec_meta, blocks, site, page_default_class))

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
    deps.add(DATA_DIR / "site.json")
    skeleton = template_path.read_text(encoding="utf-8")
    index_path = CONTENT_DIR / "index.md"
    deps.add(index_path)
    manifest, _ = load_front_matter(index_path)

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

    # 3-5. 逐页渲染（一个页面 = 一个 content/*.md）
    page_deps = {}
    for md_path in sorted(CONTENT_DIR.glob("*.md")):
        page = md_path.stem
        deps = page_deps.setdefault(page, set())
        if page == "index":
            result = render_index(PAGES_DIR / "index.html", site, deps)
        else:
            result = render_page(PAGES_DIR / "page.html", md_path, site, deps)
        (out / f"{page}.html").write_text(result, encoding="utf-8")
        print(f"  {page}.html")

    # 7. 静态拷贝 assets（含 publications.bib、books.json、subnav.html 原样）
    shutil.copytree(ASSETS_DIR, out / "assets", dirs_exist_ok=True)

    # 6. 页脚（日期 = content/data/templates 最近一次提交，无提交记录用今天），
    #    覆盖上一步拷贝进来的旧 assets/partials/footer.html
    fallback_date = datetime.date.today().isoformat()
    footer_date = (
        git_last_commit_date([CONTENT_DIR, DATA_DIR, ROOT / "templates", CONTENT_DATA_DIR])
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

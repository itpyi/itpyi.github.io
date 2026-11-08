"""正文语法及站点渲染契约回归检查。"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build import load_json, render_content_section, render_markdown, BuildError, DATA_DIR


class MarkdownTests(unittest.TestCase):
    def test_commonmark_blocks_and_inline(self):
        rendered = render_markdown('### 标题\n\n**粗体**、*斜体*和 `x < y`\n\n'
                                   '> 引用\n\n1. 第一项\n2. 第二项\n\n'
                                   '- 外层\n  - 内层\n\n```python\nx < y\n```')
        for fragment in ('<h3>标题</h3>', '<strong>粗体</strong>', '<em>斜体</em>',
                         '<code>x &lt; y</code>', '<blockquote>', '<ol>',
                         '<pre><code class="language-python">x &lt; y\n</code></pre>'):
            self.assertIn(fragment, rendered)
        self.assertEqual(rendered.count('<ul class="body-list">'), 2)

    def test_links_and_escapes(self):
        rendered = render_markdown(r'[内部](general.html?lang=en#research) [外部](https://example.org/a_(b)) [PDF](assets/docs/cv.pdf) \*原样\*')
        self.assertIn('<a href="general.html?lang=en#research" class="link-body">内部</a>', rendered)
        self.assertIn('href="https://example.org/a_(b)" class="link-body" target="_blank" rel="noopener"', rendered)
        self.assertIn('href="assets/docs/cv.pdf" class="link-body" target="_blank" rel="noopener"', rendered)
        self.assertIn('*原样*', rendered)

    def test_research_heading_matches_legacy_html(self):
        self.assertEqual(render_markdown('### 容错量子计算', research_topics=True),
                         render_markdown('<p class="research-topic">容错量子计算</p>'))
        self.assertEqual(render_markdown('### 普通标题'), '<h3>普通标题</h3>')

    def test_paragraphs_and_soft_break(self):
        self.assertEqual(render_markdown('第一行\n第二行'), '<p>第一行 第二行</p>')
        self.assertEqual(render_markdown('**重点**'), '<p><strong>重点</strong></p>')
        self.assertEqual(render_markdown('甲\n\n乙'), '<p>甲</p>\n<p>乙</p>')

    def test_cards_content_and_link_contract(self):
        rendered = render_markdown(
            '介绍\n\n### **项目**\n\n说明 [正文链接](general.html)\n\n第二段\n\n'
            '- [站内](education.html)\n- [站外](https://example.org)\n\n### 另一个项目',
            layout='cards')
        self.assertTrue(rendered.startswith('<p>介绍</p>'))
        self.assertEqual(rendered.count('<li class="list-item">'), 2)
        self.assertIn('<span class="list-title"><strong>项目</strong></span>', rendered)
        self.assertIn('<div class="list-meta">第二段</div>', rendered)
        self.assertIn('href="general.html" class="link-body"', rendered)
        self.assertIn('<a href="education.html" class="list-link">站内</a>', rendered)
        self.assertIn('class="list-link" target="_blank" rel="noopener"', rendered)

    def test_timeline_keeps_code_headings_in_body(self):
        rendered = render_markdown('### 2022\n\n#### 大学\n\n博士\n\n'
                                   '```markdown\n### 不是条目\n```', layout='timeline')
        self.assertEqual(rendered.count('<div class="edu-item">'), 1)
        self.assertIn('<div class="edu-year">2022</div>', rendered)
        self.assertIn('<div class="edu-institution">大学</div>', rendered)
        self.assertIn('<p>博士</p>', rendered)
        self.assertIn('### 不是条目', rendered)

    def test_layout_errors_are_actionable(self):
        for text, layout in [('正文', 'cards'), ('### 年份\n\n缺少机构', 'timeline'),
                             ('### 标题\n\n- 不是链接', 'cards'),
                             ('### 标题\n\n- [链接](x.html)\n  - [嵌套](y.html)', 'cards'),
                             ('### 标题', 'unknown')]:
            with self.subTest(text=text, layout=layout), self.assertRaises(BuildError):
                render_markdown(text, layout=layout)

    def test_layout_languages_and_missing_translation(self):
        rendered = render_content_section(
            {'title': {'zh': '项目', 'la': 'Opera', 'fr': 'Projets'}, 'layout': 'cards'},
            [('zh', '### 项目\n\n中文简介'), ('la', '### Opus\n\nDescriptio')],
            load_json(DATA_DIR / 'site.json'))
        self.assertEqual(rendered.count('<ul class="proj-list">'), 2)
        self.assertIn('data-lang="la"', rendered)
        self.assertIn('Cette version de langue', rendered)
        self.assertIn('class="lang-content active" data-lang="zh"', rendered)

    def test_unstyled_list(self):
        self.assertEqual(render_markdown('- [链接](x.html)', list_class=None),
                         '<ul>\n<li><a href="x.html" class="link-body">链接</a></li>\n</ul>')

    def test_multilingual_section_and_placeholder(self):
        rendered = render_content_section(
            {'title': {'zh': '研究', 'en': 'Research', 'fr': 'Recherche'},
             'data-section-id': 'research'},
            [('zh', '### 量子\n\n[履历](academics.html)'), ('en', '### Quantum')],
            load_json(DATA_DIR / 'site.json'))
        self.assertIn('<p class="research-topic">量子</p>', rendered)
        self.assertIn('<p class="research-topic">Quantum</p>', rendered)
        for lang in ('zh', 'en', 'fr'):
            self.assertIn(f'data-lang="{lang}"', rendered)
        self.assertIn('Cette version de langue', rendered)
        self.assertIn('href="academics.html" class="link-body"', rendered)


if __name__ == '__main__':
    unittest.main()

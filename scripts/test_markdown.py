"""正文语法及站点渲染契约回归检查。"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build import load_json, render_content_section, render_markdown, render_meta, DATA_DIR


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

    def test_meta_and_soft_break(self):
        self.assertEqual(render_meta('第一行\n第二行'), '第一行 第二行')
        self.assertEqual(render_meta('**重点**'), '<strong>重点</strong>')
        self.assertEqual(render_meta('甲\n\n乙'), '<p>甲</p>\n<p>乙</p>')

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

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_dom.py — DOM 一致性校验器（仅标准库）

对比两个 HTML 文件的标签结构：忽略空白文本节点、HTML 注释与属性顺序，
只比较「标签流 + 非空白文本」。用于保证 build.py 生成的新页面与旧页面
DOM 结构一致（script.js / styles.css 依赖这些结构）。

用法：
    python3 scripts/check_dom.py _site/academics.html academics.html

差异会逐条打印；完全一致（或仅允许的差异）则退出码为 0，否则为 1。
"""

import sys
from html.parser import HTMLParser


class StreamParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stream = []

    def handle_starttag(self, tag, attrs):
        self.stream.append(("start", tag, tuple(sorted(attrs))))

    def handle_startendtag(self, tag, attrs):
        self.stream.append(("startend", tag, tuple(sorted(attrs))))

    def handle_endtag(self, tag):
        self.stream.append(("end", tag))

    def handle_data(self, data):
        stripped = data.strip()
        if stripped:
            self.stream.append(("data", stripped))

    # 注释差异不比较（新页面不保留旧页面里的 HTML 注释）


def parse(path):
    parser = StreamParser()
    with open(path, encoding="utf-8") as f:
        parser.feed(f.read())
    parser.close()
    return parser.stream


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    new_stream = parse(sys.argv[1])
    old_stream = parse(sys.argv[2])
    if new_stream == old_stream:
        print(f"一致：{sys.argv[1]} ≈ {sys.argv[2]}（{len(new_stream)} 个节点）")
        return
    print(f"存在差异（新 {len(new_stream)} 节点 / 旧 {len(old_stream)} 节点）：")
    for i in range(max(len(new_stream), len(old_stream))):
        new_item = new_stream[i] if i < len(new_stream) else "<缺少>"
        old_item = old_stream[i] if i < len(old_stream) else "<缺少>"
        if new_item != old_item:
            print(f"  第 {i + 1} 个节点：")
            print(f"    新: {new_item}")
            print(f"    旧: {old_item}")
            shown = 0
            j = i + 1
            while shown < 10 and j < max(len(new_stream), len(old_stream)):
                n = new_stream[j] if j < len(new_stream) else "<缺少>"
                o = old_stream[j] if j < len(old_stream) else "<缺少>"
                if n != o:
                    print(f"    新: {n}")
                    print(f"    旧: {o}")
                    shown += 1
                j += 1
            break
    sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_dom.py — DOM 一致性校验器（仅标准库）

对比两个 HTML 文件的标签结构：忽略空白文本节点、HTML 注释与属性顺序，
只比较「标签流 + 非空白文本」。用于保证 build.py 生成的新页面与旧页面
DOM 结构一致（script.js / styles.css 依赖这些结构）。

用法：
    python3 scripts/check_dom.py _site/academics.html academics.html
    python3 scripts/check_dom.py _site /tmp/site-before

目录模式递归比较全部 HTML，包括页脚和导航片段，并检查文件增删。

差异会逐条打印；完全一致（或仅允许的差异）则退出码为 0，否则为 1。
"""

import sys
from html.parser import HTMLParser
from pathlib import Path


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


def compare(new_path, old_path):
    new_stream = parse(new_path)
    old_stream = parse(old_path)
    if new_stream == old_stream:
        print(f"一致：{new_path} ≈ {old_path}（{len(new_stream)} 个节点）")
        return True
    print(f"存在差异：{new_path} / {old_path}")
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
    return False


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    new, old = map(Path, sys.argv[1:])
    if new.is_file() and old.is_file():
        sys.exit(0 if compare(new, old) else 1)
    if not (new.is_dir() and old.is_dir()):
        sys.exit("请提供两个存在的 HTML 文件或两个构建目录。")
    new_files = {p.relative_to(new) for p in new.rglob("*.html")}
    old_files = {p.relative_to(old) for p in old.rglob("*.html")}
    if not new_files or not old_files:
        sys.exit("构建目录中没有 HTML，无法进行对比。")
    equal = new_files == old_files
    for path in sorted(new_files - old_files):
        print(f"新增：{path}")
    for path in sorted(old_files - new_files):
        print(f"缺少：{path}")
    for path in sorted(new_files & old_files):
        if not compare(new / path, old / path):
            equal = False
    sys.exit(0 if equal else 1)


if __name__ == "__main__":
    main()

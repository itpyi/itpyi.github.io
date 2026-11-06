#!/bin/zsh
# macOS：双击启动；首次使用自动建立本地 Python 环境。
cd -- "${0:A:h}"
if [[ ! -x .venv/bin/python ]]; then
    python3 -m venv .venv || exit 1
fi
if ! .venv/bin/python -c 'import yaml' 2>/dev/null; then
    .venv/bin/python -m pip install -r requirements.txt || exit 1
fi
exec .venv/bin/python preview.py "$@"

#!/usr/bin/env python3
"""本地连续预览：python preview.py [--port 8000]。仅使用标准库及现有构建依赖。"""
import argparse
import io
import json
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WATCH = ('content', 'templates', 'data', 'assets', 'build.py', 'requirements.txt',
         'CNAME', 'googled77ae0d191b8a2f5.html')
CLIENT = '''<script>
(() => {
  let revision = null;
  const box = document.createElement('pre');
  box.style.cssText = 'position:fixed;bottom:0;left:0;right:0;z-index:2147483647;max-height:35vh;overflow:auto;margin:0;padding:16px;background:#320b0b;color:#fff;white-space:pre-wrap;font:14px monospace;display:none';
  document.body.appendChild(box);
  async function poll() {
    try {
      const response = await fetch('/__preview_status', {cache:'no-store'});
      const state = await response.json();
      if (revision !== null && revision !== state.revision) {
        location.reload(); return;
      }
      revision = state.revision;
      box.textContent = state.error ? '本地构建失败，显示上次成功的页面：\\n' + state.error : '';
      box.style.display = state.error ? 'block' : 'none';
    } catch (_) { /* 服务器重启后继续连接。 */ }
    setTimeout(poll, 700);
  }
  poll();
})();
</script>'''


def snapshot():
    result = {}
    for name in WATCH:
        path = ROOT / name
        for file in path.rglob('*') if path.is_dir() else [path]:
            try:
                if file.is_file():
                    stat = file.stat()
                    result[str(file)] = (stat.st_mtime_ns, stat.st_size)
            except FileNotFoundError:
                pass  # 编辑器原子替换文件时，下次轮询再检查。
    return result


class Preview:
    def __init__(self, workspace):
        self.workspace = workspace
        self.current = workspace / 'initial'
        self.current.mkdir()
        (self.current / 'index.html').write_text('<html><body>等待首次成功构建。</body></html>')
        self.revision = time.time_ns()
        self.error = ''
        self.lock = threading.RLock()
        self.stop = threading.Event()

    def build(self):
        target = Path(tempfile.mkdtemp(prefix='build-', dir=self.workspace))
        try:
            # 校验浏览器读取的数据，避免构建器仅复制坏 JSON 而误报成功。
            for path in (ROOT / 'assets' / 'data').glob('*.json'):
                json.loads(path.read_text(encoding='utf-8'))
            run = subprocess.run([sys.executable, str(ROOT / 'build.py'), '--output',
                                  str(target.relative_to(ROOT))], cwd=ROOT,
                                 capture_output=True, text=True)
            if run.returncode:
                raise RuntimeError(run.stdout + run.stderr)
        except Exception as exc:
            with self.lock:
                self.error = str(exc)
            print(f'构建失败：{exc}', flush=True)
            shutil.rmtree(target)
            return False
        with self.lock:
            previous = self.current
            self.current = target
            self.revision += 1
            self.error = ''
            shutil.rmtree(previous)
        print('构建完成，浏览器将自动刷新。', flush=True)
        return True

    def watch(self, previous):
        pending = None
        while not self.stop.wait(0.2):
            current = snapshot()
            if current != previous:
                previous, pending = current, time.monotonic()
            elif pending is not None and time.monotonic() - pending >= 0.3:
                pending = None
                self.build()


def handler_for(preview):
    class Handler(SimpleHTTPRequestHandler):
        def do_GET(self):
            with preview.lock:
                if self.path.split('?')[0] == '/__preview_status':
                    data = json.dumps({'revision': preview.revision, 'error': preview.error}).encode()
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Content-Length', str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                else:
                    self.directory = str(preview.current)
                    super().do_GET()

        def do_HEAD(self):
            with preview.lock:
                self.directory = str(preview.current)
                super().do_HEAD()

        def send_head(self):
            path = Path(self.translate_path(self.path))
            if path.is_dir() and self.path.split('?')[0].endswith('/'):
                path = path / 'index.html'
            if path.is_file() and path.suffix == '.html':
                text = path.read_text(encoding='utf-8')
                if '</body>' in text:
                    data = text.replace('</body>', CLIENT + '</body>').encode('utf-8')
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html; charset=utf-8')
                    self.send_header('Content-Length', str(len(data)))
                    self.end_headers()
                    return io.BytesIO(data)
            return super().send_head()

        def end_headers(self):
            self.send_header('Cache-Control', 'no-store')
            super().end_headers()

        def log_message(self, *_):
            pass
    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='.preview-', suffix='.tmp', dir=ROOT) as temp:
        preview = Preview(Path(temp))
        try:
            server = ThreadingHTTPServer(('127.0.0.1', args.port), handler_for(preview))
        except OSError as exc:
            sys.exit(f'无法启动预览：{exc}。可用 --port 8001 更换端口。')
        previous = snapshot()
        preview.build()
        worker = threading.Thread(target=preview.watch, args=(previous,), daemon=True)
        worker.start()
        print(f'本地预览：http://127.0.0.1:{args.port}/ （保存后自动刷新，Ctrl+C 停止）', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            preview.stop.set()
            worker.join()
            server.server_close()


if __name__ == '__main__':
    main()

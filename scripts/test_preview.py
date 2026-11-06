"""连续预览集成检查：python3 -m unittest discover -s scripts -p 'test_preview.py'。"""
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from urllib.request import urlopen
from http.server import ThreadingHTTPServer

spec = importlib.util.spec_from_file_location('preview', Path(__file__).resolve().parents[1] / 'preview.py')
preview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preview)


class PreviewTest(unittest.TestCase):
    def test_rebuild_failure_recovery_and_injection(self):
        original_root = preview.ROOT
        with tempfile.TemporaryDirectory() as tmp:
            preview.ROOT = root = Path(tmp)
            (root / 'content').mkdir()
            (root / 'assets/data').mkdir(parents=True)
            data = root / 'assets/data/books.json'
            data.write_text('{}')
            source = root / 'content/text.txt'
            source.write_text('initial')
            (root / 'build.py').write_text('''import pathlib,sys
root=pathlib.Path(__file__).parent
out=root/sys.argv[2]
text=(root/'content/text.txt').read_text()
if text == 'broken':
    sys.exit('intentional build failure')
(out/'index.html').write_text('<html><body>'+text+'</body></html>')
(out/'fragment.html').write_text('<nav>navigation</nav>')
''')
            workspace = root / 'work.tmp'
            workspace.mkdir()
            app = preview.Preview(workspace)
            self.assertTrue(app.build())
            server = ThreadingHTTPServer(('127.0.0.1', 0), preview.handler_for(app))
            serving = threading.Thread(target=server.serve_forever)
            watching = threading.Thread(target=app.watch, args=(preview.snapshot(),))
            serving.start()
            watching.start()
            url = f'http://127.0.0.1:{server.server_port}'

            def get(path='/'):
                with urlopen(url + path, timeout=3) as response:
                    self.assertEqual(response.headers['Cache-Control'], 'no-store')
                    return response.read().decode()

            def wait_for(predicate):
                deadline = time.monotonic() + 5
                while time.monotonic() < deadline:
                    if predicate():
                        return
                    time.sleep(0.05)
                self.fail('preview did not update')

            try:
                self.assertIn('/__preview_status', get('/?lang=en'))
                self.assertNotIn('/__preview_status', (app.current / 'index.html').read_text())
                self.assertEqual(get('/fragment.html'), '<nav>navigation</nav>')
                revision = app.revision
                source.write_text('updated')
                wait_for(lambda: app.revision > revision)
                self.assertIn('updated', get())
                revision = app.revision
                source.write_text('broken')
                wait_for(lambda: bool(app.error))
                self.assertEqual(app.revision, revision)
                self.assertIn('updated', get())
                self.assertIn('intentional build failure', json.loads(get('/__preview_status'))['error'])
                source.write_text('recovered')
                wait_for(lambda: app.revision > revision)
                self.assertFalse(app.error)
                self.assertIn('recovered', get())
                revision = app.revision
                data.write_text('invalid json')
                wait_for(lambda: bool(app.error))
                self.assertEqual(app.revision, revision)
                data.write_text('{}')
                wait_for(lambda: app.revision > revision)
                extra = root / 'content/new.txt'
                revision = app.revision
                extra.write_text('new')
                wait_for(lambda: app.revision > revision)
                revision = app.revision
                extra.unlink()
                wait_for(lambda: app.revision > revision)
            finally:
                app.stop.set()
                watching.join()
                server.shutdown()
                serving.join()
                server.server_close()
                preview.ROOT = original_root


if __name__ == '__main__':
    unittest.main()

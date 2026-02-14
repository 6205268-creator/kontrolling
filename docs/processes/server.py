#!/usr/bin/env python3
"""
Локальный сервер для BPMN Viewer с возможностью сохранения в проект.

Запуск: cd docs/processes && python server.py
Открыть: http://localhost:8888/bpmn-viewer.html

Кнопка «Сохранить в проект» POST-ит XML на /api/save — файл записывается в проект.
"""
import json
import os
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler


class BpmnRequestHandler(SimpleHTTPRequestHandler):
    """Обработчик: статика + GET /api/status + POST /api/save."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(os.path.abspath(__file__)), **kwargs)

    def do_GET(self):
        path = self.path.split('?')[0]
        if path == '/api/status':
            self._send_json(200, {'saveSupported': True})
            return
        super().do_GET()

    def do_POST(self):
        path = self.path.split('?')[0]
        if path == '/api/save':
            self._handle_save()
        else:
            self.send_error(404)

    def _handle_save(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            self._send_json(400, {'ok': False, 'error': 'Тело запроса пустое'})
            return

        try:
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)
        except (ValueError, UnicodeDecodeError) as e:
            self._send_json(400, {'ok': False, 'error': f'Неверный JSON: {e}'})
            return

        path = data.get('path')
        xml = data.get('xml')

        if not path or not isinstance(path, str):
            self._send_json(400, {'ok': False, 'error': 'path обязателен'})
            return
        if xml is None:
            self._send_json(400, {'ok': False, 'error': 'xml обязателен'})
            return

        # Нормализуем путь: только forward slashes, без ..
        path = path.replace('\\', '/').strip('/')
        if '..' in path or not path.endswith('.bpmn'):
            self._send_json(400, {'ok': False, 'error': 'Недопустимый путь'})
            return

        full_path = os.path.normpath(os.path.join(self.directory, path))
        base_dir = os.path.abspath(self.directory)
        if not full_path.startswith(base_dir):
            self._send_json(400, {'ok': False, 'error': 'Путь вне директории процессов'})
            return

        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(xml)
            self._send_json(200, {'ok': True, 'path': path})
        except OSError as e:
            self._send_json(500, {'ok': False, 'error': str(e)})

    def _send_json(self, status, obj):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(obj, ensure_ascii=False).encode('utf-8'))


def run(port=8888):
    server = HTTPServer(('127.0.0.1', port), BpmnRequestHandler)
    print(f'BPMN Viewer: http://127.0.0.1:{port}/bpmn-viewer.html')
    print('Кнопка «Сохранить в проект» сохранит файл в docs/processes/')
    server.serve_forever()


if __name__ == '__main__':
    run()

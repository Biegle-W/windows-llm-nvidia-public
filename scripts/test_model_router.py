"""Protocol/concurrency regressions using a fake worker; no GPU or weights loaded."""
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
import time
import unittest
from unittest.mock import patch

from model_router import ModelManager, RouterError, RouterServer


class FakeProcess:
    def poll(self):
        return None


class FakeWorker(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *_):
        pass

    def do_POST(self):
        if self.headers.get('Authorization') != 'Bearer worker-only':
            self.send_error(401)
            return
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        self.server.bodies.append(body)
        payload = {'model': body['model'], 'choices': [{'message': {'content': 'ROUTED'}}]}
        if body.get('stream'):
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Connection', 'close')
            self.end_headers()
            self.wfile.write(b'data: {"choices":[{"delta":{"content":"ROUTED"}}]}\n\n')
            self.wfile.flush()
            self.server.streaming.set()
            self.server.release.wait(3)
            self.wfile.write(b'data: [DONE]\n\n')
            self.wfile.flush()
            self.close_connection = True
        else:
            raw = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)


class FakeManager:
    request_body = ModelManager.request_body
    catalog = ModelManager.catalog

    def __init__(self, port):
        self.worker_port, self.key = port, 'worker-only'
        self.default = 'a'
        self.profiles = {name: {'id': name, 'label': name, 'context': 8192,
                               'requiresThinking': name == 'b'} for name in ('a', 'b', 'blocked')}
        self.lock = threading.Lock()
        self.loaded = self.process = None
        self.events = []

    def stop_worker(self):
        if self.loaded:
            self.events.append(('unload', self.loaded))
        self.loaded = self.process = None

    def ensure(self, model):
        if self.loaded == model:
            return
        self.stop_worker()
        if model == 'blocked':
            raise RouterError('Resource admission refused.', code='insufficient_resources')
        self.events.append(('load', model))
        self.loaded, self.process = model, FakeProcess()


class RouterTests(unittest.TestCase):
    def setUp(self):
        self.worker = ThreadingHTTPServer(('127.0.0.1', 0), FakeWorker)
        self.worker.daemon_threads = True
        self.worker.bodies = []
        self.worker.streaming = threading.Event()
        self.worker.release = threading.Event()
        self.manager = FakeManager(self.worker.server_port)
        self.router = RouterServer(('127.0.0.1', 0), self.manager, 'client-secret')
        self.threads = []
        for server in (self.worker, self.router):
            thread = threading.Thread(target=server.serve_forever, kwargs={'poll_interval': 0.02}, daemon=True)
            thread.start()
            self.threads.append(thread)

    def tearDown(self):
        self.worker.release.set()
        for server in (self.router, self.worker):
            server.shutdown()
            server.server_close()
        for thread in self.threads:
            thread.join(2)

    def request(self, path='/v1/chat/completions', body=None, key='client-secret', method='POST'):
        conn = http.client.HTTPConnection('127.0.0.1', self.router.server_port, timeout=3)
        conn.request(method, path, None if body is None else json.dumps(body),
                     {'Authorization': 'Bearer '+key, 'Content-Type': 'application/json'})
        response = conn.getresponse()
        result = response.status, json.loads(response.read())
        conn.close()
        return result

    def test_auth_and_catalog_do_not_load_weights(self):
        self.assertEqual(self.request('/v1/models', key='wrong', method='GET')[0], 401)
        status, data = self.request('/v1/models', method='GET')
        self.assertEqual(status, 200)
        self.assertEqual([r['id'] for r in data['data']], ['a', 'b', 'blocked'])
        self.assertEqual(self.manager.events, [])

    def test_switch_reuse_default_and_unload(self):
        for model in ('a', 'a', 'b', 'a'):
            status, data = self.request(body={'model': model, 'messages': []})
            self.assertEqual((status, data['model']), (200, model))
        self.assertEqual(self.manager.events, [('load', 'a'), ('unload', 'a'), ('load', 'b'),
                                              ('unload', 'b'), ('load', 'a')])
        self.assertEqual(self.request(body={'messages': []})[1]['model'], 'a')
        self.assertEqual(self.request('/router/unload', {})[0], 200)
        self.assertIsNone(self.manager.loaded)

    def test_unknown_model_and_invalid_json_do_not_switch(self):
        self.request(body={'model': 'a'})
        events = list(self.manager.events)
        self.assertEqual(self.request(body={'model': '../arbitrary.gguf'})[0], 404)
        self.assertEqual(self.request(body=[])[0], 400)
        self.assertEqual(self.manager.events, events)

    def test_model_specific_thinking_and_tool_payload_preserved(self):
        body = {'model': 'b', 'messages': [{'role': 'user', 'content': 'test'}],
                'chat_template_kwargs': {'enable_thinking': False},
                'tools': [{'type': 'function', 'function': {'name': 'echo'}}],
                'tool_choice': 'required', 'response_format': {'type': 'json_object'}}
        self.assertEqual(self.request(body=body)[0], 200)
        forwarded = self.worker.bodies[-1]
        self.assertNotIn('enable_thinking', forwarded['chat_template_kwargs'])
        for field in ('messages', 'tools', 'tool_choice', 'response_format'):
            self.assertEqual(forwarded[field], body[field])

    def test_resource_refusal_returns_openai_error_without_fallback(self):
        self.request(body={'model': 'a'})
        status, data = self.request(body={'model': 'blocked'})
        self.assertEqual((status, data['error']['code']), (503, 'insufficient_resources'))
        self.assertIsNone(self.manager.loaded)
        self.assertEqual(len(self.worker.bodies), 1)

    def test_streaming_holds_switch_lock_and_does_not_buffer_first_event(self):
        conn = http.client.HTTPConnection('127.0.0.1', self.router.server_port, timeout=3)
        conn.request('POST', '/v1/chat/completions', json.dumps({'model': 'a', 'stream': True}),
                     {'Authorization': 'Bearer client-secret', 'Content-Type': 'application/json'})
        response = conn.getresponse()
        self.assertEqual(response.status, 200)
        self.assertTrue(self.worker.streaming.wait(2))
        self.assertIn(b'ROUTED', response.readline())
        status, data = self.request(body={'model': 'b'})
        self.assertEqual((status, data['error']['code']), (503, 'router_busy'))
        self.assertEqual(self.manager.loaded, 'a')
        self.worker.release.set()
        self.assertIn(b'[DONE]', response.read())
        conn.close()
        deadline = time.monotonic()+2
        while self.manager.lock.locked() and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertEqual(self.request(body={'model': 'b'})[0], 200)

    def test_real_manager_stops_old_worker_before_admission_and_never_spawns_on_refusal(self):
        manager = ModelManager.__new__(ModelManager)
        manager.default = 'a'
        manager.profiles = {'a': {'id': 'a', 'minimumAvailableRAMGiB': 4}}
        manager.loaded = manager.process = None
        order = []
        with patch.object(manager, 'stop_worker', side_effect=lambda: order.append('unload')), \
             patch('hardware_guard.preflight', side_effect=RuntimeError('Insufficient memory')) as admission, \
             patch('model_router.subprocess.Popen') as spawn:
            with self.assertRaises(RouterError) as result:
                manager.ensure(manager.default)
            self.assertEqual(result.exception.code, 'insufficient_resources')
            self.assertEqual(order, ['unload'])
            admission.assert_called_once_with(profile=manager.profiles[manager.default])
            spawn.assert_not_called()


if __name__ == '__main__':
    unittest.main(verbosity=2)

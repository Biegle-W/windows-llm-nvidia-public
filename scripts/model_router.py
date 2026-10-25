"""Authenticated OpenAI-compatible router with one guarded llama.cpp worker."""
import argparse
import configparser
import hmac
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import secrets
import socket
import subprocess
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
MAX_BODY = 8 * 1024 * 1024


class RouterError(Exception):
    def __init__(self, message, status=503, code='model_unavailable'):
        super().__init__(message)
        self.status, self.code = status, code


class ModelManager:
    def __init__(self, root=ROOT):
        self.root = Path(root)
        self.stack = json.loads((self.root/'config/stack.json').read_text())
        if self.stack.get('backend') != 'cuda' or not (self.root/self.stack['runtime']).is_file():
            raise ValueError('The configured Windows CUDA runtime is required.')
        rows = json.loads((self.root/'config/selected-profiles.json').read_text())
        self.profiles = {}
        for row in rows:
            if not re.fullmatch(r'[A-Za-z0-9_.-]+', row['id']) or row['id'] in self.profiles:
                raise ValueError('Model IDs must be unique and safe filename components.')
            if not (self.root/row['path']).is_file():
                raise ValueError('A registered model file is missing.')
            self.profiles[row['id']] = row
        self.default = self.stack['defaultModel']
        if self.default not in self.profiles:
            raise ValueError('The default model is not registered.')
        self.settings = self.stack.get('router', {})
        self.worker_port = self.settings.get('workerPort', 10001)
        self.lock = threading.Lock()
        self.process = self.loaded = self.log = None
        self.guard_stop = threading.Event()
        self.guard_thread = None
        self.failure = None
        self.key = secrets.token_urlsafe(32)
        self.key_file = None
        ini = configparser.ConfigParser(interpolation=None)
        ini.read_string('[metadata]\n'+(self.root/'config/models.ini').read_text())
        self.common = dict(ini['*'])

    def catalog(self):
        return {'object': 'list', 'data': [
            {'id': p['id'], 'object': 'model', 'created': 0, 'owned_by': 'local',
             'name': p['label'], 'context_window': p['context']}
            for p in self.profiles.values()]}

    def stop_worker(self):
        self.guard_stop.set()
        if self.guard_thread:
            self.guard_thread.join(timeout=3)
            self.guard_thread = None
        if self.process is not None:
            if self.process.poll() is None:
                # Popen retains the process handle; never target an unrelated port occupant.
                subprocess.run(['taskkill.exe', '/PID', str(self.process.pid), '/T', '/F'],
                               capture_output=True, timeout=15,
                               creationflags=subprocess.CREATE_NO_WINDOW)
                self.process.wait(timeout=15)
            self.process = None
        if self.log:
            self.log.close()
            self.log = None
        self.loaded = None
        if self.key_file:
            self.key_file.unlink(missing_ok=True)
            self.key_file = None

    def _worker_json(self, path):
        conn = http.client.HTTPConnection('127.0.0.1', self.worker_port, timeout=3)
        try:
            conn.request('GET', path, headers={'Authorization': 'Bearer '+self.key})
            response = conn.getresponse()
            data = response.read()
            if response.status != 200:
                raise OSError('Worker not ready')
            return json.loads(data)
        finally:
            conn.close()

    def ensure(self, model):
        if self.loaded == model and self.process is not None and self.process.poll() is None:
            return
        self.stop_worker()
        self.failure = None
        profile = self.profiles[model]
        from hardware_guard import clean_environment, preflight, selected_gpu
        from test_models import memory
        try:
            # The old worker is gone before evaluating the incoming model's own budget.
            preflight(profile=profile)
        except RuntimeError as exc:
            raise RouterError(str(exc), code='insufficient_resources') from None
        with socket.socket() as probe:
            try:
                probe.bind(('127.0.0.1', self.worker_port))
            except OSError:
                raise RouterError('The private worker port is occupied; its owner was left untouched.',
                                  code='worker_port_in_use') from None
        options = {**self.common, **profile.get('options', {})}
        options.pop('load-on-startup', None)
        options.update(model=str((self.root/profile['path']).resolve()),
                       **{'ctx-size': profile['context'], 'fit-ctx': profile['context'],
                          'host': '127.0.0.1', 'port': self.worker_port, 'alias': model,
                          'timeout': 600, 'log-verbosity': 4})
        self.key_file = self.root/'data/credentials'/f'.router-worker-{secrets.token_hex(12)}.key'
        self.key_file.parent.mkdir(parents=True, exist_ok=True)
        self.key_file.write_text(self.key)
        options['api-key-file'] = str(self.key_file)
        command = [str(self.root/self.stack['runtime'])]
        for name, value in options.items():
            if str(value).lower() == 'true':
                command.append('--'+name)
            elif str(value).lower() != 'false':
                command.extend(['--'+name, str(value)])
        env = clean_environment()
        env['LLAMA_CACHE'] = str(self.root/'data/cache/router')
        Path(env['LLAMA_CACHE']).mkdir(parents=True, exist_ok=True)
        logs = self.root/'logs'
        logs.mkdir(exist_ok=True)
        self.log = (logs/f'worker-{model}.log').open('a', encoding='utf-8')
        print(f'Loading {model} ({profile["context"]} context)', flush=True)
        try:
            self.process = subprocess.Popen(command, cwd=self.root, env=env,
                                            stdout=self.log, stderr=self.log,
                                            creationflags=subprocess.CREATE_NO_WINDOW)
            process = self.process
            self.guard_stop = threading.Event()

            def guard():
                low = 0
                while not self.guard_stop.wait(1):
                    try:
                        low = low + 1 if memory()['physical_available_gib'] < 0.75 else 0
                        if low >= 5:
                            self.failure = 'Available RAM stayed below 0.75 GiB for five seconds.'
                            if process.poll() is None:
                                process.terminate()
                            return
                    except OSError:
                        self.failure = 'RAM monitoring failed.'
                        if process.poll() is None:
                            process.terminate()
                        return

            self.guard_thread = threading.Thread(target=guard, daemon=True)
            self.guard_thread.start()
            deadline = time.monotonic() + self.settings.get('loadTimeoutSeconds', 240)
            while True:
                if process.poll() is not None:
                    raise RouterError(self.failure or 'Model worker exited while loading; see its private log.')
                try:
                    if self._worker_json('/health').get('status') == 'ok':
                        break
                except (OSError, ValueError, http.client.HTTPException):
                    pass
                if time.monotonic() > deadline:
                    raise RouterError('Model loading timed out.', code='load_timeout')
                time.sleep(0.25)
            if self._worker_json('/props')['default_generation_settings']['n_ctx'] != profile['context']:
                raise RouterError('The worker context differs from its registered profile.')
            if selected_gpu()['free_mib'] < profile.get('minimumLoadedFreeVRAMMiB', 1024):
                raise RouterError('Loaded model left less than its required actual free VRAM.',
                                  code='insufficient_resources')
            self.loaded = model
            print(f'Ready: {model}', flush=True)
        except BaseException as exc:
            self.stop_worker()
            if isinstance(exc, RouterError) or not isinstance(exc, Exception):
                raise
            raise RouterError('Model startup failed; inspect its private worker log.') from None

    def request_body(self, model, body):
        profile = self.profiles[model]
        result = dict(body, model=model)
        supplied = result.get('chat_template_kwargs', {})
        if not isinstance(supplied, dict):
            raise RouterError('chat_template_kwargs must be an object.', 400, 'invalid_request_error')
        kwargs = {**profile.get('chatTemplateKwargs', {'enable_thinking': False}), **supplied}
        if profile.get('requiresThinking'):
            # LFM's template requires reasoning; ignore a stale client's global thinking toggle.
            kwargs.pop('enable_thinking', None)
        result['chat_template_kwargs'] = kwargs
        return result


class RouterServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(self, address, manager, key):
        self.manager, self.api_key = manager, key
        super().__init__(address, RouterHandler)


class RouterHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def setup(self):
        super().setup()
        self.connection.settimeout(15)

    def log_message(self, *_):
        pass  # Do not log prompts, URLs or Authorization headers.

    def send_json(self, status, data):
        raw = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Connection', 'close')
        if status == 503:
            self.send_header('Retry-After', '2')
        self.end_headers()
        self.close_connection = True
        self.wfile.write(raw)

    def error(self, message, status=400, code='invalid_request_error'):
        self.send_json(status, {'error': {'message': message, 'type': code, 'code': code, 'param': None}})

    def authorized(self):
        value = self.headers.get('Authorization', '')
        if not hmac.compare_digest(value.encode(), ('Bearer '+self.server.api_key).encode()):
            self.error('Invalid API key.', 401, 'invalid_api_key')
            return False
        return True

    def do_GET(self):
        if not self.authorized():
            return
        manager = self.server.manager
        if self.path in ('/v1/models', '/models'):
            self.send_json(200, manager.catalog())
        elif self.path in ('/health', '/router/status'):
            alive = manager.process is not None and manager.process.poll() is None
            self.send_json(200, {'status': 'ok', 'loaded_model': manager.loaded if alive else None,
                                 'busy': manager.lock.locked(), 'models_max': 1})
        else:
            self.error('Unknown API endpoint.', 404, 'not_found')

    def do_POST(self):
        if not self.authorized():
            return
        if self.path not in ('/v1/chat/completions', '/v1/completions', '/router/unload'):
            self.error('Unknown API endpoint.', 404, 'not_found')
            return
        try:
            if self.headers.get('Transfer-Encoding'):
                raise ValueError()
            size = int(self.headers.get('Content-Length', '0'))
            if size < 0 or size > MAX_BODY:
                self.error('Request body exceeds 8 MiB.', 413, 'request_too_large')
                return
            body = json.loads(self.rfile.read(size)) if size else {}
            if not isinstance(body, dict):
                raise ValueError()
        except (ValueError, UnicodeError):
            self.error('Expected a JSON object with Content-Length.')
            return
        except OSError:
            self.error('Timed out reading the request body.', 408, 'request_timeout')
            return
        manager = self.server.manager
        model = body.get('model', manager.default)
        if not isinstance(model, str) or model not in manager.profiles:
            self.error('Unknown model. Select an ID from /v1/models.', 404, 'model_not_found')
            return
        try:
            body = manager.request_body(model, body)
        except RouterError as exc:
            self.error(str(exc), exc.status, exc.code)
            return
        if not manager.lock.acquire(blocking=False):
            self.error('Another request or model switch is in progress; retry after it completes.',
                       503, 'router_busy')
            return
        conn = None
        started = False
        try:
            if self.path == '/router/unload':
                manager.stop_worker()
                self.send_json(200, {'status': 'ok', 'loaded_model': None})
                return
            manager.ensure(model)
            conn = http.client.HTTPConnection('127.0.0.1', manager.worker_port, timeout=600)
            raw = json.dumps(body).encode()
            conn.request('POST', self.path, raw, {'Authorization': 'Bearer '+manager.key,
                                                  'Content-Type': 'application/json'})
            response = conn.getresponse()
            self.send_response(response.status)
            for name in ('Content-Type', 'Content-Length'):
                if response.getheader(name):
                    self.send_header(name, response.getheader(name))
            self.send_header('Connection', 'close')
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.close_connection = True
            started = True
            while True:
                chunk = response.read1(65536)
                if not chunk:
                    break
                self.wfile.write(chunk)
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            # Cancel an abandoned generation before allowing a new model to load.
            manager.stop_worker()
        except RouterError as exc:
            if not started:
                self.error(str(exc), exc.status, exc.code)
        except (OSError, ValueError, http.client.HTTPException):
            manager.stop_worker()
            if not started:
                self.error('The model worker is unavailable; inspect the private worker log.', 503,
                           'model_unavailable')
        finally:
            if conn:
                conn.close()
            manager.lock.release()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-config', action='store_true')
    args = parser.parse_args()
    manager = ModelManager()
    if args.check_config:
        print(json.dumps({'passed': True, 'models': list(manager.profiles), 'default': manager.default}))
        return
    key = (ROOT/'data/credentials/.local-api-key').read_text().strip()
    if not key:
        raise SystemExit('The private API credential is empty.')
    server = RouterServer(('127.0.0.1', manager.settings.get('port', 10000)), manager, key)
    print('Local model router ready on http://127.0.0.1:10000/v1; models load on demand.', flush=True)
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        manager.stop_worker()
        server.server_close()


if __name__ == '__main__':
    main()

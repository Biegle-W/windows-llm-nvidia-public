"""Shared Strata measurement helpers; the historical Q2 drive workflow is retired."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import threading
import time
import urllib.error
import urllib.request

import psutil

ROOT = Path(__file__).resolve().parents[1]
BASE = 'http://127.0.0.1:8081'
DISKS = ('PhysicalDrive2', 'PhysicalDrive0')  # Verified C: NVMe and D: SATA.


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2), encoding='utf-8')


def api(path):
    with urllib.request.urlopen(BASE + path, timeout=5) as response:
        return json.load(response)


def disk_snapshot():
    disks = psutil.disk_io_counters(perdisk=True, nowrap=True)
    return {name: disks[name]._asdict() for name in DISKS}


def disk_delta(before, after):
    return {name: {key: after[name][key] - before[name][key] for key in before[name]}
            for name in DISKS}


class Monitor:
    def __enter__(self):
        self.samples = []
        self.started = time.perf_counter()
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()
        return self

    def run(self):
        while not self.stop_event.is_set():
            self.samples.append({'seconds': round(time.perf_counter() - self.started, 3),
                                 'available_ram_bytes': psutil.virtual_memory().available,
                                 'disks': disk_snapshot()})
            self.stop_event.wait(1)

    def __exit__(self, *_):
        self.stop_event.set()
        self.thread.join(3)


def launcher(mode):
    subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                    str(ROOT / 'scripts/Start-Strata.ps1'), '-Mode', mode],
                   cwd=ROOT, check=True, timeout=40)


def wait_stopped():
    deadline = time.monotonic() + 40
    while time.monotonic() < deadline:
        try:
            api('/health')
        except (OSError, urllib.error.URLError):
            # The server can exit shortly before its owned engine; wait for both.
            engines = [p for p in psutil.process_iter(['name', 'exe'])
                       if (p.info['name'] or '').lower() == 'strata.exe'
                       and str(ROOT / 'runtimes/Strata').lower() in (p.info['exe'] or '').lower()]
            if not engines:
                return
        time.sleep(1)
    raise RuntimeError('Strata did not release its server/engine')


def wait_ready():
    deadline = time.monotonic() + 600
    last_notice = 0
    while time.monotonic() < deadline:
        try:
            health = api('/health')
            if health.get('status') == 'ok':
                return health
        except (OSError, urllib.error.URLError):
            pass
        if time.monotonic() - last_notice > 30:
            print('Waiting for visible Strata to finish loading...', flush=True)
            last_notice = time.monotonic()
        time.sleep(1)
    raise RuntimeError('Strata did not become healthy within 10 minutes')


def gpu_snapshot(path):
    result = subprocess.run(['nvidia-smi', '--query-gpu=index,name,memory.used,memory.free,temperature.gpu',
                             '--format=csv'], capture_output=True, text=True, check=True)
    path.write_text(result.stdout, encoding='utf-8')


def chat(stage, name, prompt, model='qwen3.8-flash-next-iq3_xxs'):
    body = {'model': model, 'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 512, 'temperature': 0, 'seed': 42, 'stream': True,
            'chat_template_kwargs': {'enable_thinking': False}}
    request = urllib.request.Request(BASE + '/v1/chat/completions', data=json.dumps(body).encode(),
                                     headers={'Content-Type': 'application/json'})
    before = disk_snapshot()
    started = time.perf_counter()
    first_seconds = first_disks = None
    content, chunks, final = [], 0, None
    with Monitor() as monitor:
        with urllib.request.urlopen(request, timeout=300) as response:
            for line in response:
                if not line.startswith(b'data: '):
                    continue
                raw = line[6:].strip()
                if raw == b'[DONE]':
                    break
                chunk = json.loads(raw)
                if chunk.get('error'):
                    raise RuntimeError(chunk['error'])
                chunks += 1
                text = (chunk.get('choices') or [{}])[0].get('delta', {}).get('content', '')
                if text:
                    if first_seconds is None:
                        first_seconds = time.perf_counter() - started
                        first_disks = disk_snapshot()
                    content.append(text)
                if chunk.get('timings'):
                    final = chunk
    after = disk_snapshot()
    wall = time.perf_counter() - started
    if not content or not final:
        raise RuntimeError(f'{name}: missing generated text or engine timings')
    result = {'request': body, 'content': ''.join(content), 'final_chunk': final,
              'wall_seconds': round(wall, 3), 'first_text_seconds': round(first_seconds, 3),
              'chunks': chunks, 'disk_bytes_scope': 'Whole physical disk; includes other applications and OS I/O.',
              'disk_total_delta': disk_delta(before, after),
              'disk_before_first_text_delta': disk_delta(before, first_disks),
              'disk_after_first_text_delta': disk_delta(first_disks, after),
              'available_ram_min_bytes': min(s['available_ram_bytes'] for s in monitor.samples)}
    save(stage / (name + '.json'), result)
    save(stage / (name + '-monitor.json'), monitor.samples)
    timings = final['timings']
    print(f"{stage.name}/{name}: {timings['predicted_per_second']} tokens/s; "
          f"first text {first_seconds:.2f}s; D: reads {result['disk_total_delta']['PhysicalDrive0']['read_bytes'] / 2**20:.1f}MiB",
          flush=True)
    return {'name': name, 'timings': timings, 'usage': final['usage'],
            **{k: result[k] for k in ('wall_seconds', 'first_text_seconds', 'disk_total_delta',
                                     'disk_after_first_text_delta', 'available_ram_min_bytes')}}




def main():
    raise RuntimeError("The historical Q2 drive-comparison workflow is retired. Use saved reports; shared Q3 measurement helpers remain available.")


if __name__ == '__main__':
    main()

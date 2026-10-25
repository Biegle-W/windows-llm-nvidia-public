"""Check retrieval across a larger synthetic prompt on the visible Strata backend."""
import argparse
import datetime
import json
from pathlib import Path
import shutil
import time
import urllib.request

from test_strata_quant import memory_snapshot
from benchmark_strata_drives import gpu_snapshot

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--port', type=int, default=8081)
    opts = ap.parse_args()
    base = f'http://127.0.0.1:{opts.port}'

    def api(path, body=None):
        req = urllib.request.Request(base + path, data=json.dumps(body).encode() if body else None,
                                     headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=900) as response:
            return json.load(response)

    health = api('/health')
    before = api('/v1/status')
    if before['activity']['in_flight']:
        raise RuntimeError('A desktop request is in progress')
    model = api('/v1/models')['data'][0]['id']
    out = ROOT / 'reports/verification' / (model + '-context-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
    out.mkdir(parents=True)
    rows = [f'Record {i}: ordinary reference text for checking retrieval from a longer context.' for i in range(2000)]
    rows[7] = 'Record 7: verification code ALPHA-78219.'
    rows[1901] = 'Record 1901: verification code OMEGA-93157.'
    prompt = '\n'.join(rows) + '\nReturn only the verification codes in record 7 and record 1901.'
    request = dict(model=model, messages=[dict(role='user', content=prompt)], max_tokens=64,
                   temperature=0, seed=42, chat_template_kwargs={'enable_thinking': False})
    memory_before = memory_snapshot()
    started = time.perf_counter()
    response = api('/v1/chat/completions', request)
    content = response['choices'][0]['message'].get('content') or ''
    after = api('/v1/status')
    passed = all(code in content for code in ['ALPHA-78219', 'OMEGA-93157'])
    uncontaminated = after['activity']['requests'] - before['activity']['requests'] == 1
    result = dict(passed=passed and uncontaminated, health=health, request=request, response=response,
                  wall_seconds=round(time.perf_counter()-started, 3), memory_before=memory_before,
                  memory_after=memory_snapshot(), status_before=before, status_after=after,
                  limitation='Allocated 128K; this check tests only the prompt length reported by usage.prompt_tokens.')
    (out / 'result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    state = json.loads((ROOT / 'data/state/strata-process.json').read_text(encoding='utf-8-sig'))
    cfg = json.loads(Path(state['engineConfig']).read_text(encoding='utf-8-sig'))
    shutil.copy2(cfg['log'], out / 'engine.log')
    gpu_snapshot(out / 'gpu-after.csv')
    print(json.dumps(dict(passed=result['passed'], usage=response.get('usage'), seconds=result['wall_seconds'])), flush=True)
    print('Evidence:', out, flush=True)
    if not result['passed']:
        raise RuntimeError('Longer-context verification failed or was contaminated')


if __name__ == '__main__':
    main()

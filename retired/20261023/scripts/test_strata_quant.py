"""Measure the current visible Strata quant with the drive-comparison workloads."""
import datetime
import json
from pathlib import Path
import shutil
import subprocess

import psutil
import benchmark_strata_drives as benchmark
from benchmark_strata_drives import api, chat, gpu_snapshot, save

ROOT = Path(__file__).resolve().parents[1]


def memory_snapshot():
    state = json.loads((ROOT / 'data/state/strata-process.json').read_text(encoding='utf-8-sig'))
    server = psutil.Process(state['pid'])
    engine = next(p for p in server.children(recursive=True) if p.name().lower() == 'strata.exe')
    return {'engine_pid': engine.pid, 'engine_memory': engine.memory_info()._asdict(),
            'system_memory': psutil.virtual_memory()._asdict(), 'swap': psutil.swap_memory()._asdict()}


def main():
    state = json.loads((ROOT / 'data/state/strata-process.json').read_text(encoding='utf-8-sig'))
    cfg = json.loads(Path(state['engineConfig']).read_text(encoding='utf-8-sig'))
    benchmark.BASE = f"http://127.0.0.1:{cfg['port']}"
    status = api('/v1/status')
    if status['activity']['in_flight']:
        raise RuntimeError('Pause desktop requests before testing')
    model = api('/v1/models')['data'][0]['id']
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    out = ROOT / 'reports/verification' / (model + '-' + stamp)
    out.mkdir(parents=True)
    if not state.get('visible'):
        raise RuntimeError('Test requires the visible backend')
    save(out / 'engine-config.json', cfg)
    save(out / 'health.json', api('/health'))
    save(out / 'props.json', api('/props'))
    save(out / 'status-before.json', status)
    save(out / 'memory-before.json', memory_snapshot())
    gpu_snapshot(out / 'gpu-before.csv')
    prompts = [
        ('short-cpu', 'Explain how a computer uses CPU, RAM, GPU memory and SSD storage when running a large local language model. Write several detailed paragraphs.'),
        ('short-quant', 'Explain why quantization and mixture-of-experts architectures reduce the hardware needed for local language models. Write several detailed paragraphs.'),
        ('short-planning', 'Describe a careful experimental plan for comparing two local inference configurations. Explain workload selection, repeated measurements, throughput, latency and sources of variation in detail.'),
    ]
    rows = [f'Record {i}: ordinary reference text for checking retrieval from a longer context.' for i in range(250)]
    rows[122] = 'Record 122: the secret verification code is STRATA-482731.'
    prompts += [('long-4k', '\n'.join(rows) + '\nFirst state the code from record 122. Then explain in several detailed paragraphs how you retrieved it and how context length affects local language model inference.'), ('repeat-cpu', prompts[0][1])]
    measurements = []
    for name, prompt in prompts:
        measurements.append(chat(out, name, prompt, model=model))
        save(out / 'progress.json', {'measurements': measurements})
    after = api('/v1/status')
    save(out / 'status-after.json', after)
    if after['activity']['requests'] - status['activity']['requests'] != len(prompts):
        raise RuntimeError('Competing desktop requests contaminated the measurements')
    retrieved = json.loads((out / 'long-4k.json').read_text(encoding='utf-8'))['content']
    if 'STRATA-482731' not in retrieved:
        raise RuntimeError('Synthetic retrieval failed')
    save(out / 'memory-after.json', memory_snapshot())
    gpu_snapshot(out / 'gpu-after.csv')
    shutil.copy2(cfg['log'], out / 'engine.log')
    total = sum(x['timings']['predicted_n'] for x in measurements)
    seconds = sum(x['timings']['predicted_ms'] for x in measurements) / 1000
    result = {'passed': True, 'model': model, 'context': api('/health')['max_context'],
              'generation_weighted_tps': round(total / seconds, 3), 'measurements': measurements,
              'minimum_available_ram_gib': round(min(x['available_ram_min_bytes'] for x in measurements) / 2**30, 3),
              'limitation': 'Five bounded synthetic workloads; full context and broad model quality not tested.'}
    save(out / 'result.json', result)
    print(json.dumps({k: result[k] for k in ('passed', 'model', 'context', 'generation_weighted_tps', 'minimum_available_ram_gib')}), flush=True)
    print('Evidence:', out, flush=True)


if __name__ == '__main__':
    main()

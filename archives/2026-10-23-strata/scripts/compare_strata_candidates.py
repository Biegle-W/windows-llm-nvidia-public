"""Compare explicit Strata candidates in a visible terminal without changing saved settings."""
import argparse
import copy
import datetime
import json
import os
from pathlib import Path
import statistics
import sys
import threading
import time

import psutil

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / 'runtimes/Strata'
sys.path[:0] = [str(RUNTIME / 'tools'), str(RUNTIME)]
import calibrate as cal
from serve.server import StrataEngine, child_env
import strata_tokenizer as ST
from benchmark_strata_drives import Monitor, disk_snapshot, disk_delta, gpu_snapshot

PROMPTS = (*cal.PROMPTS,
           '用中文详细解释本地大语言模型的显存、系统内存和专家卸载，至少写八段。')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('plan', type=Path)
    opts = ap.parse_args()
    if not os.environ.get('WT_SESSION'):
        raise RuntimeError('Run this comparison in the visible Local-LLM terminal.')
    for proc in psutil.process_iter(['name', 'exe']):
        if (proc.info['name'] or '').lower() == 'strata.exe' and str(ROOT).lower() in (proc.info['exe'] or '').lower():
            raise RuntimeError('Stop the loaded Strata engine first.')
    plan = json.loads(opts.plan.read_text(encoding='utf-8-sig'))
    base = json.loads(Path(plan['config']).read_text(encoding='utf-8-sig'))
    out = ROOT / 'reports/verification' / ('strata-candidates-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
    out.mkdir(parents=True)

    def save(name, value):
        (out / name).write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')

    tp = Path(base['tokenizer'])
    vocab = json.loads((tp / 'vocab.json').read_text(encoding='utf-8'))
    tokens = [None] * len(vocab)
    for token, index in vocab.items():
        tokens[index] = token
    tok = ST.Tokenizer(tokens, (tp / 'merges.txt').read_text(encoding='utf-8').split('\n'),
                       json.loads((tp / 'token_type.json').read_text()))
    workloads = plan.get('workloads') or [{'name': str(i), 'prompt': p, 'max_new': plan.get('max_new', 256)}
                                         for i, p in enumerate(PROMPTS)]
    ids = [cal.chat_ids(tok, w['prompt']) for w in workloads]
    warm_ids = [cal.chat_ids(tok, p) for p in cal.PROMPTS]
    save('plan.json', plan)
    build = json.loads((RUNTIME / 'engine/BUILD.json').read_text())
    save('build.json', build)
    results = []
    for candidate in plan['candidates']:
        cfg = copy.deepcopy(base)
        cfg.update(candidate.get('config', {}))
        cfg['env'] = {**base.get('env', {}), **candidate.get('env', {})}
        args = cal.engine_args(cfg)
        for flag, value in candidate.get('options', {}).items():
            if isinstance(value, bool):
                args = [a for a in args if a != flag]
                if value:
                    args.append(flag)
            else:
                args = cal.with_arg(args, flag, None if value is None else str(value))
        name = candidate['name']
        save(name + '-config.json', dict(config=cfg, args=args))
        build_path = Path(cfg['exe']).parent / 'BUILD.json'
        if build_path.exists():
            save(name + '-build.json', json.loads(build_path.read_text()))
        print('Loading candidate:', name, flush=True)
        engine = None
        record = dict(name=name, candidate=candidate, rounds=[])
        try:
            engine = StrataEngine(cfg['exe'], args, cwd=cfg.get('cwd'), log=str(out / (name + '.log')), env=child_env(cfg))
            record['info'] = engine.info
            gpu_snapshot(out / (name + '-gpu.csv'))
            session = cal.Session(engine, warm_ids)
            session.warm_up(1)
            for round_number in range(plan.get('rounds', 2)):
                rows = []
                for workload, prompt_ids in zip(workloads, ids):
                    before = psutil.virtual_memory().available
                    disk_before = disk_snapshot()
                    started = time.perf_counter()
                    first = None
                    output_ids = []
                    with Monitor() as monitor:
                        for token in engine.generate(prompt_ids, workload['max_new'],
                                                     {'temperature': 0}, threading.Event()):
                            if token is not None:
                                if first is None:
                                    first = time.perf_counter() - started
                                output_ids.append(token)
                    generated = len(output_ids)
                    metrics = dict(engine.last or {})
                    decode_ms = metrics.get('decode_ms', 0)
                    row = dict(name=workload['name'], prompt=workload['prompt'], tokens=generated, metrics=metrics,
                                     tok_s=generated * 1000 / decode_ms if decode_ms else 0,
                                     first_token_seconds=first, wall_seconds=time.perf_counter() - started,
                                     disk_delta=disk_delta(disk_before, disk_snapshot()),
                                     disk_scope='Whole physical disk, including OS and other applications.',
                                     minimum_available_ram=min(s['available_ram_bytes'] for s in monitor.samples),
                                     available_ram_before=before, available_ram_after=psutil.virtual_memory().available)
                    if plan.get('save_text'):
                        row['text'] = tok.decode(output_ids)
                    rows.append(row)
                    print(f"{name}/{workload['name']}: {row['tok_s']:.2f} tok/s; first token {first:.2f}s; "
                          f"prompt {metrics.get('prompt_ms', 0):.0f}ms", flush=True)
                    save(name + '-progress.json', rows)
                record['rounds'].append(rows)
                all_rows = [r for round_rows in record['rounds'] for r in round_rows]
                seconds = sum(r['metrics'].get('decode_ms', 0) for r in all_rows) / 1000
                record['weighted_tok_s'] = sum(r['tokens'] for r in all_rows) / seconds if seconds else 0
                record['median_tok_s'] = statistics.median(r['tok_s'] for r in all_rows)
                print(f"{name}, round {round_number + 1}: weighted {record['weighted_tok_s']:.2f} tok/s", flush=True)
                save(name + '-result.json', record)
        except Exception as error:
            record['error'] = str(error)
            print(name, 'failed:', error, flush=True)
        finally:
            if engine is not None:
                cal.close(engine)
        results.append(record)
        save('result.json', results)
    if plan.get('pcie_screen'):
        # Only tune a successful current-build candidate, never the rollback engine.
        eligible = [r for r in results if 'weighted_tok_s' in r and r.get('info', {}).get('version') == build['version']]
        if eligible:
            winner = max(eligible, key=lambda r: r['weighted_tok_s'])
            chosen_cfg = json.loads((out / (winner['name'] + '-config.json')).read_text())
            cfg, args = chosen_cfg['config'], chosen_cfg['args']
            print('PCIe/draft screening on:', winner['name'], flush=True)
            engine = StrataEngine(cfg['exe'], args, cwd=cfg.get('cwd'), log=str(out / 'pcie-screen.log'), env=child_env(cfg))
            try:
                session = cal.Session(engine, ids)
                session.warm_up(1)
                default = (round(float(engine.info.get('pcie_frac', 0.55)), 2),
                           float(engine.info.get('spec_min_p', 0.5)))
                fractions = sorted(set((0, 0.2, 0.35, 0.55, 0.75, 1, default[0])))
                by_pcie = {f: [] for f in fractions}
                for order in (fractions, list(reversed(fractions))):
                    for fraction in order:
                        rate = session.rate({'pcie_frac': fraction, 'spec_min_p': default[1]}, max_new=128)
                        by_pcie[fraction].append(rate)
                        print(f'PCIe {fraction:.2f}: {rate:.2f} tok/s', flush=True)
                        save('pcie-progress.json', by_pcie)
                best_fraction = max(by_pcie, key=lambda f: statistics.median(by_pcie[f]))
                floors = (0.3, 0.5, 0.7)
                by_floor = {f: [] for f in floors}
                for order in (floors, tuple(reversed(floors))):
                    for floor in order:
                        rate = session.rate({'pcie_frac': best_fraction, 'spec_min_p': floor}, max_new=128)
                        by_floor[floor].append(rate)
                        print(f'Draft floor {floor:.2f}: {rate:.2f} tok/s', flush=True)
                candidate_pair = (best_fraction, max(by_floor, key=lambda f: statistics.median(by_floor[f])))
                confirmation = {default: [], candidate_pair: []}
                for _ in range(2):
                    for pair in dict.fromkeys((default, candidate_pair)):
                        confirmation[pair].append(session.rate({'pcie_frac': pair[0], 'spec_min_p': pair[1]}, max_new=256))
                        print(f'Confirm {pair}: {confirmation[pair][-1]:.2f} tok/s', flush=True)
                choice = cal.pick(confirmation, default)
                tuning_settings = ({'--pcie-frac': str(choice[0]), '--spec-min-p': str(choice[1])}
                                   if choice != default else {})
                save('pcie-result.json', dict(candidate=winner['name'], default=default, chosen=choice,
                     fractions=by_pcie, floors=by_floor, confirmation={str(k): v for k, v in confirmation.items()},
                     settings=tuning_settings, info=engine.info))
                print('Confirmed PCIe/draft choice:', choice, flush=True)
            finally:
                cal.close(engine)
    print('Evidence:', out, flush=True)
    (ROOT / 'data/state/strata-candidates-complete.json').write_text(json.dumps({'evidence': str(out)}), encoding='utf-8')
    if not any('weighted_tok_s' in r for r in results):
        raise RuntimeError('No candidate finished successfully.')


if __name__ == '__main__':
    main()

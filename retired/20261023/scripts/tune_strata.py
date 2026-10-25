"""Measure Strata's hardware settings and optional GPU split; never apply unconfirmed choices."""
import argparse
import datetime
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / 'runtimes/Strata'
sys.path[:0] = [str(RUNTIME / 'tools'), str(RUNTIME)]
import calibrate as cal
from serve.server import StrataEngine, child_env


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--profile', choices=['Default', 'Q3'], default='Default')
    ap.add_argument('--splits', nargs='*', help='Compare splits using previously calibrated settings')
    ap.add_argument('--settings', type=Path, help='Calibration result for split comparison')
    opts = ap.parse_args()
    source = ROOT / 'config' / 'strata.json'  # Both profile names select Q3.
    settings = json.loads(source.read_text())
    cfg = json.loads((RUNTIME / settings['engineConfig']).read_text(encoding='utf-8-sig'))
    out = ROOT / 'reports/verification' / ('strata-tuning-' + opts.profile.lower() + '-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
    out.mkdir(parents=True)
    count = 0

    def save(name, data):
        (out / name).write_text(json.dumps(data, indent=2), encoding='utf-8')

    def start(args):
        nonlocal count
        count += 1
        log = out / f'engine-{count}.log'
        engine = StrataEngine(cfg['exe'], args, cwd=cfg.get('cwd'), log=str(log), env=child_env(cfg))
        save(f'engine-{count}-info.json', dict(args=args, info=engine.info))
        return engine

    save('engine-config.json', cfg)
    save('build.json', json.loads((RUNTIME / 'engine/BUILD.json').read_text()))
    if opts.splits is None:
        result = cal.run(cfg, say=lambda message: print(message, flush=True), start_engine=start)
    else:
        import strata_tokenizer as ST
        tpath = Path(cfg['tokenizer'])
        vocab = json.loads((tpath / 'vocab.json').read_text(encoding='utf-8'))
        tokens = [None] * len(vocab)
        for token, index in vocab.items():
            tokens[index] = token
        tokenizer = ST.Tokenizer(tokens, (tpath / 'merges.txt').read_text(encoding='utf-8').split('\n'), json.loads((tpath / 'token_type.json').read_text()))
        ids = [cal.chat_ids(tokenizer, p) for p in cal.PROMPTS]
        previous = json.loads(opts.settings.read_text()) if opts.settings else {}
        tuned = previous.get('settings', {})
        args = cal.apply(cal.engine_args(cfg), tuned)
        measured = {}
        # Recheck auto last so warm files and background drift cannot favor a manual split alone.
        for split in ['auto', *opts.splits, 'auto']:
            engine = start(cal.with_arg(args, '--layer-split', split))
            try:
                session = cal.Session(engine, ids)
                session.warm_up(1)
                rates = [session.rate(), session.rate()]
                measured.setdefault(split, []).extend(rates)
                print(f'Split {split}: {statistics.median(rates):.2f} tok/s', flush=True)
                save('progress.json', measured)
            finally:
                cal.close(engine)
        winner = cal.pick(measured, 'auto')
        result = dict(settings=tuned, layerSplit=winner, rates=measured)
    save('result.json', result)
    print(json.dumps(result, indent=2), flush=True)
    print('Evidence:', out, flush=True)


if __name__ == '__main__':
    main()

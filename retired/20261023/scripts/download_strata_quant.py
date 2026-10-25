"""Download a verified Strata quant to its configured data drive, with resumable ranges."""
import argparse
import concurrent.futures as futures
import hashlib
import json
import os
from pathlib import Path
import threading
import time
import urllib.request

REPO = 'ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF'
CHUNK = 128 * 1024 * 1024


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, required=True)
    parser.add_argument('--quant', choices=['IQ3_XXS'], default='IQ3_XXS')
    parser.add_argument('--connections', type=int, default=24)
    args = parser.parse_args()
    root = args.data_dir.resolve() / 'models' / args.quant
    root.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(f'https://huggingface.co/api/models/{REPO}?blobs=true', timeout=60) as response:
        metadata = json.load(response)
    revision = metadata['sha']
    files = []
    # Download the two independent Q3 shards expected by upstream setup/pack tools.
    for index in (2, 1):
        name = f'Qwen3.8-Flash-Next-GSQ-RCO-{args.quant}-0000{index}-of-00002.gguf'
        info = next(x for x in metadata['siblings'] if x['rfilename'] == args.quant + '/' + name)
        size, sha = info['lfs']['size'], info['lfs']['sha256']
        final = root / name
        if final.exists():
            if final.stat().st_size != size or digest(final) != sha:
                raise RuntimeError(f'Existing model is incomplete or different; not overwritten: {final}')
        else:
            download(root, final, size, sha, revision, args.quant, args.connections)
        final.with_name(name + '.done').write_text('SHA-256 verified ' + sha, encoding='utf-8')
        files.append({'name': name, 'bytes': size, 'sha256': sha})
        evidence = {'repository': REPO, 'revision': revision, 'quantization': args.quant,
                    'data_directory': str(args.data_dir.resolve()), 'files': files, 'complete': len(files) == 2}
        (root / 'download-verification.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
    print('Complete: both shards SHA-256 verified against official LFS metadata.', flush=True)


def download(root, final, size, sha, revision, quant, connections):
    partial = final.with_name(final.name + '.ranges')
    journal = final.with_name(final.name + '.ranges.json')
    if journal.exists():
        state = json.loads(journal.read_text(encoding='utf-8'))
        if state['sha256'] != sha or state['size'] != size:
            raise RuntimeError('Resume journal belongs to a different model revision')
    else:
        print(f'Preparing incremental {size / 1e9:.2f}GB download on {root.drive}.', flush=True)
        # Windows CRT truncate zero-fills large exFAT files before downloading anything.
        # Let independent ranges grow the file instead; only journaled ranges count as received.
        with partial.open('wb'):
            pass
        state = {'sha256': sha, 'size': size, 'done': []}
        journal.write_text(json.dumps(state), encoding='utf-8')
    if not partial.exists() or partial.stat().st_size > size:
        raise RuntimeError('Resume data file is missing or incomplete')
    lock = threading.Lock()
    jobs = [(start, min(start + CHUNK, size) - 1) for start in range(0, size, CHUNK) if start not in state['done']]
    url = f'https://huggingface.co/{REPO}/resolve/{revision}/{quant}/{final.name}'

    def fetch(job):
        start, end = job
        for attempt in range(8):
            try:
                request = urllib.request.Request(url, headers={'Range': f'bytes={start}-{end}'})
                with urllib.request.urlopen(request, timeout=120) as response, partial.open('r+b') as stream:
                    expected = f'bytes {start}-{end}/{size}'
                    if response.status != 206 or response.headers.get('Content-Range') != expected:
                        raise RuntimeError('Incorrect HTTP byte range')
                    stream.seek(start)
                    remaining = end - start + 1
                    while remaining:
                        data = response.read(min(remaining, 4 * 1024 * 1024))
                        if not data:
                            raise RuntimeError('Short HTTP download')
                        stream.write(data)
                        remaining -= len(data)
                with lock:
                    state['done'].append(start)
                    temporary = journal.with_suffix('.tmp')
                    temporary.write_text(json.dumps(state), encoding='utf-8')
                    os.replace(temporary, journal)
                return
            except Exception as error:
                if attempt == 7:
                    raise RuntimeError(f'Range {start} failed ({type(error).__name__}); rerun to resume') from None
                time.sleep(min(2 ** attempt, 20))

    initial = sum(min(CHUNK, size - start) for start in state['done'])
    started = time.monotonic()
    print(f'Downloading {len(jobs)} resumable ranges with {connections} connections; revision {revision}.', flush=True)
    with futures.ThreadPoolExecutor(max_workers=connections) as pool:
        pending = {pool.submit(fetch, job) for job in jobs}
        while pending:
            completed, pending = futures.wait(pending, timeout=10)
            for future in completed:
                future.result()
            with lock:
                received = sum(min(CHUNK, size - start) for start in state['done'])
            rate = (received - initial) / max(1, time.monotonic() - started) / 1e6
            print(f'{received / 1e9:.2f} / {size / 1e9:.2f}GB complete ranges; {rate:.1f}MB/s average.', flush=True)
    print('Checking complete shard SHA-256...', flush=True)
    if partial.stat().st_size != size or digest(partial) != sha:
        raise RuntimeError('SHA-256 mismatch; partial file retained for diagnosis')
    partial.rename(final)
    print(f'Verified: {final.name}', flush=True)


if __name__ == '__main__':
    main()

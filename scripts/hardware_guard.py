"""Read-only RTX 3060/CUDA preflight; never stops another process."""
import argparse
import csv
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def clean_environment():
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(('LLAMA_ARG_', 'GGML_VK_'))
           and k not in ('CUDA_VISIBLE_DEVICES', 'HIP_VISIBLE_DEVICES',
                        'ROCR_VISIBLE_DEVICES', 'LLAMA_API_KEY')}
    env['CUDA_VISIBLE_DEVICES'] = selected_gpu()['uuid']
    return env

def selected_gpu():
    run = subprocess.run(['nvidia-smi', '--query-gpu=name,uuid,memory.total,memory.free',
                          '--format=csv,noheader,nounits'], capture_output=True, text=True,
                         timeout=15, creationflags=subprocess.CREATE_NO_WINDOW)
    if run.returncode:
        raise RuntimeError('NVIDIA driver is unavailable; check Device Manager.')
    matches = [r for r in csv.reader(run.stdout.splitlines())
               if len(r) == 4 and r[0].strip() == 'NVIDIA GeForce RTX 3060']
    if len(matches) != 1:
        raise RuntimeError('Exactly one RTX 3060 is required; another GPU is not substituted.')
    name, uuid, total, free = [v.strip() for v in matches[0]]
    return {'name': name, 'uuid': uuid, 'total_mib': int(total), 'free_mib': int(free)}

def validate_devices(text, minimum_free_mib=2048):
    rows = re.findall(r'^\s*(CUDA\d+): (.*?) \((\d+) MiB, (\d+) MiB free\)', text, re.M)
    if len(rows) != 1 or rows[0][0] != 'CUDA0':
        raise RuntimeError('The selected RTX 3060 must be the only visible CUDA device.')
    for device, name, total, free in rows:
        if name != 'NVIDIA GeForce RTX 3060' or int(total) < 12000:
            raise RuntimeError(f'{device} is not the expected 12 GB RTX 3060.')
        if int(free) < minimum_free_mib:
            raise RuntimeError('The RTX 3060 needs at least 2 GiB reported free VRAM.')
    return [{'device': d, 'name': n, 'total_mib': int(t), 'free_mib': int(f)} for d,n,t,f in rows]

def preflight(require_model=True, profile=None):
    from test_models import memory
    stack = json.loads((ROOT/'config/stack.json').read_text(encoding='utf-8'))
    if stack.get('backend') != 'cuda':
        raise RuntimeError('This Windows build requires the configured CUDA backend.')
    env = clean_environment()
    run = subprocess.run([str(ROOT/stack['runtime']), '--list-devices'],
                         capture_output=True, text=True, env=env,
                         timeout=30, creationflags=subprocess.CREATE_NO_WINDOW)
    if run.returncode:
        raise RuntimeError('CUDA device enumeration failed; check the NVIDIA driver/runtime.')
    devices = validate_devices(run.stdout + run.stderr)
    ram = memory()
    if ram['physical_available_gib'] < 2 or ram['commit_available_gib'] < 8:
        raise RuntimeError('Close unused applications: at least 2 GiB available RAM and 8 GiB commit headroom are required.')
    if require_model:
        profiles = [profile] if profile is not None else [p for p in json.loads(
            (ROOT/'config/selected-profiles.json').read_text(encoding='utf-8'))
            if p['id'] == stack.get('defaultModel')]
        if not profiles or (profile is None and stack.get('defaultModel') not in {p['id'] for p in profiles}):
            raise RuntimeError('No Windows model is registered. Run scripts/register_model.py with an existing GGUF path.')
        for p in profiles:
            if not (ROOT / p['path']).is_file():
                raise RuntimeError(f"Model file is missing for {p['id']}; register its Windows path again.")
        required_ram = max(p.get('minimumAvailableRAMGiB', 2) for p in profiles)
        required_commit = max(p.get('minimumCommitGiB', 8) for p in profiles)
        if ram['physical_available_gib'] < required_ram or ram['commit_available_gib'] < required_commit:
            raise RuntimeError(f'The registered profile requires {required_ram} GiB available system RAM and {required_commit} GiB commit headroom; close unused applications first.')
        required = max(p.get('minimumFreeVRAMMiB', 2048) for p in profiles)
        if selected_gpu()['free_mib'] < required:
            raise RuntimeError(f'The registered profile requires {required} MiB free on the RTX 3060; close GPU-heavy apps first.')
    return {'passed': True, 'devices': devices, 'memory': ram,
            'cudaVisibleDevices': env['CUDA_VISIBLE_DEVICES'], 'model_required': require_model}

if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument('--hardware-only', action='store_true')
        args = parser.parse_args()
        print(json.dumps(preflight(require_model=not args.hardware_only)))
    except Exception as exc:
        print(f'Hardware preflight: {exc}', file=sys.stderr)
        sys.exit(1)

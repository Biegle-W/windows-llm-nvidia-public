"""Register an existing Windows GGUF and regenerate CUDA/client catalogs."""
import argparse
import datetime
import json
from pathlib import Path
import re
import shutil
from build_configuration import build, ROOT

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', type=Path)
    parser.add_argument('--id', help='Stable API ID; defaults to the GGUF filename stem')
    parser.add_argument('--name', help='Display name before context/memory suffixes')
    parser.add_argument('--context', type=int, default=8192)
    parser.add_argument('--default', action='store_true')
    parser.add_argument('--full-gpu', action='store_true', help='Require all weights on the RTX 3060 and at least 8 GiB free VRAM')
    args = parser.parse_args()
    model = args.path.expanduser().resolve(strict=True)
    with model.open('rb') as file:
        if file.read(4) != b'GGUF' or model.stat().st_size < 100 * 2**20:
            raise ValueError('Provide a complete inference GGUF, not a vocabulary/projector fixture.')
    model_id = args.id or model.stem
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', model_id):
        raise ValueError('API IDs may contain letters, numbers, dots, underscores and hyphens.')
    if args.context < 512 or args.context > 262144:
        raise ValueError('Context must be between 512 and 262144 tokens; capacity still needs testing.')
    profile_file = ROOT/'config/selected-profiles.json'
    stack_file = ROOT/'config/stack.json'
    profiles = json.loads(profile_file.read_text(encoding='utf-8'))
    stack = json.loads(stack_file.read_text(encoding='utf-8'))
    backup = ROOT/'archive'/('before-model-registration-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    backup.mkdir(parents=True)
    for name in ['selected-profiles.json','stack.json','models.ini','harness-provider.json']:
        shutil.copy2(ROOT/'config'/name, backup/name)
    mode = 'Full GPU' if args.full_gpu else 'CUDA automatic fit'
    stored_path = model.relative_to(ROOT).as_posix() if model.is_relative_to(ROOT) else str(model)
    profile = {'id': model_id, 'label': f'{args.name or model.stem} | {args.context//1024}K | {mode}',
               'path': stored_path, 'context': args.context, 'options': {}}
    if args.full_gpu:
        profile.update(options={'fit':'off','gpu-layers':'all'},minimumFreeVRAMMiB=8192,requireFullGpu=True)
    profiles = [p for p in profiles if p['id'] != model_id] + [profile]
    if args.default or not stack.get('defaultModel'):
        stack['defaultModel'] = model_id
        stack['preferredFastModel'] = model_id
    stack.pop('status', None)
    try:
        profile_file.write_text(json.dumps(profiles, indent=2)+'\n', encoding='utf-8')
        stack_file.write_text(json.dumps(stack, indent=2)+'\n', encoding='utf-8')
        build()
    except BaseException:
        for name in ['selected-profiles.json','stack.json','models.ini','harness-provider.json']:
            shutil.copy2(backup/name, ROOT/'config'/name)
        raise
    print(f'Registered {model_id}; run Start Local LLM.cmd. Context and GPU placement require validation.')

if __name__ == '__main__':
    main()

"""Bounded API checks against the already-visible Strata server on localhost."""
import datetime
import argparse
import json
from pathlib import Path
import subprocess
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports' / 'verification' / ('strata-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
OUT.mkdir(parents=True, exist_ok=True)
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--port', type=int, default=8081)
args = parser.parse_args()
BASE = f'http://127.0.0.1:{args.port}'


def api(path, body=None):
    request = urllib.request.Request(BASE + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=900) as response:
        return json.load(response)


def save(name, data):
    (OUT / (name + '.json')).write_text(json.dumps(data, indent=2), encoding='utf-8')


save('health', api('/health'))
models = api('/v1/models')
save('models', models)
model = models['data'][0]['id']
save('props', api('/props'))
save('status-before', api('/v1/status'))


def chat(name, messages, **extra):
    body = dict(model=model, messages=messages, max_tokens=256,
                temperature=0, stream=False, chat_template_kwargs={'enable_thinking': False})
    body.update(extra)
    started = time.perf_counter()
    response = api('/v1/chat/completions', body)
    save(name, dict(request=body, response=response, wall_seconds=round(time.perf_counter() - started, 3)))
    print(name, json.dumps(response.get('timings', {})), flush=True)
    assert response.get('choices'), f'{name}: no choices'
    return response['choices'][0]['message']


for name, prompt in (
    ('generation-cold', 'Explain how a computer uses CPU, RAM, GPU memory and SSD storage when running a large local language model. Write several detailed paragraphs.'),
    ('generation-warm', 'Explain why quantization and mixture-of-experts architectures reduce the hardware needed for local language models. Write several detailed paragraphs.'),
):
    message = chat(name, [{'role': 'user', 'content': prompt}])
    assert message.get('content'), f'{name}: empty answer'

chinese = chat('generation-chinese', [{'role': 'user', 'content':
    '先用阿拉伯数字给出 8 × 7 的结果，再用两句中文解释显存和系统内存的区别。'}], max_tokens=128)
chinese_text = chinese.get('content') or ''
assert any('\u4e00' <= char <= '\u9fff' for char in chinese_text), 'No Chinese text returned'
assert '56' in chinese_text, 'Simple calculation failed'

tools = [{'type': 'function', 'function': {'name': 'get_temperature',
    'description': 'Get the current temperature in a named city.',
    'parameters': {'type': 'object', 'properties': {'city': {'type': 'string'}}, 'required': ['city']}}}]
messages = [{'role': 'user', 'content': 'Use get_temperature to look up the current temperature in Boston. Do not guess.'}]
call = chat('tool-call', messages, tools=tools, max_tokens=128)
assert call.get('tool_calls'), 'No tool call returned'
function = call['tool_calls'][0]
assert function['function']['name'] == 'get_temperature', 'Unexpected tool'
assert 'boston' in json.loads(function['function']['arguments'])['city'].lower(), 'Incorrect tool argument'
reply = chat('tool-result', messages + [call, {'role': 'tool', 'tool_call_id': function['id'],
    'content': '{"city":"Boston","temperature_c":19}'}], tools=tools, max_tokens=128)
assert '19' in (reply.get('content') or ''), 'Tool result was not used'

rows = [f'Record {i}: ordinary reference text for checking retrieval from a longer context.' for i in range(250)]
rows[122] = 'Record 122: the secret verification code is STRATA-482731.'
retrieval = chat('retrieval', [{'role': 'user', 'content': '\n'.join(rows) +
    '\nReturn only the secret verification code from record 122.'}], max_tokens=64)
assert 'STRATA-482731' in (retrieval.get('content') or ''), 'Retrieval mismatch'
save('status-after', api('/v1/status'))
gpu = subprocess.run(['nvidia-smi', '--query-gpu=index,name,memory.used,memory.free', '--format=csv'],
                     capture_output=True, text=True, check=True).stdout
(OUT / 'gpu-memory.csv').write_text(gpu, encoding='utf-8')
save('result', {'passed': True, 'model': model, 'checks': ['generation-cold', 'generation-warm', 'generation-chinese', 'tool-call', 'tool-result', 'retrieval'],
                'limitation': 'Short generation and bounded retrieval only; full allocated context not tested.'})
print(f'All checks passed. Evidence: {OUT}', flush=True)

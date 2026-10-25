"""Generate matching llama.cpp and DeepSeek Harness model catalogs."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent

def build():
    selected=json.loads((ROOT/'config'/'selected-profiles.json').read_text())
    if not selected or len({p['id'] for p in selected}) != len(selected):
        raise ValueError('Register at least one model with unique API IDs.')
    stack=json.loads((ROOT/'config'/'stack.json').read_text())
    if stack['defaultModel'] not in {p['id'] for p in selected}:
        raise ValueError('The default model must be registered.')
    common={
        'device':'CUDA0','split-mode':'none','main-gpu':0,'fit':'on','fit-target':1536,
        'gpu-layers':'auto',
        'parallel':1,'flash-attn':'on','cache-type-k':'q8_0','cache-type-v':'q8_0',
        'threads':6,'threads-batch':14,'batch-size':512,'ubatch-size':128,
        'load-mode':'none','cache-ram':0,'ctx-checkpoints':0,'jinja':'true',
        'chat-template-kwargs':'{"enable_thinking":false}',
        'reasoning-format':'deepseek','no-warmup':'true','temp':0.6,'top-p':0.95,
        'min-p':0.0,'repeat-penalty':1.0,'load-on-startup':'false'}
    ini=['version = 1','','; Generated from selected-profiles.json by build_configuration.py','[*]']
    ini.extend(f'{k} = {v}' for k,v in common.items())
    catalog=[]
    for p in selected:
        model = (ROOT / p['path']).resolve()
        if not model.is_file():raise FileNotFoundError(model)
        ini.extend(['',f"[{p['id']}]",f"model = {model.as_posix()}",f"ctx-size = {p['context']}",f"fit-ctx = {p['context']}"])
        ini.extend(f'{k} = {v}' for k,v in p.get('options',{}).items())
        catalog.append({'id':p['id'],'name':p['label'],'contextWindow':p['context'],
                        'maxTokens':p.get('maxTokens',8192),'input':['text'],'reasoningEfforts':False})
    (ROOT/'config'/'models.ini').write_text('\n'.join(ini)+'\n')
    provider={'displayName':'Local llama.cpp (RTX 3060 12 GB)',
              'api':'openai-completions','baseURL':'http://127.0.0.1:10000/v1',
              'apiKeyEnv':'LLAMA_CPP_API_KEY','timeoutMs':600000,'streamIdleTimeoutMs':600000,
              'compat':{'supportsDeveloperRole':False,'supportsStore':False,'supportsReasoningEffort':False,
                        'supportsStrictMode':False,'maxTokensField':'max_tokens','thinkingFormat':'chat-template'},'models':catalog}
    (ROOT/'config'/'harness-provider.json').write_text(json.dumps({'provider':provider,'defaultModel':stack['defaultModel']},indent=2))
    print(f'Generated {len(selected)} backend profiles and {len(catalog)} Harness profiles.')

if __name__=='__main__':build()

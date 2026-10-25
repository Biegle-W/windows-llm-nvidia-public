import json, time, urllib.request, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
KEY=(ROOT/'data'/'credentials'/'.local-api-key').read_text().strip()
MODEL=sys.argv[1] if len(sys.argv)>1 else json.loads((ROOT/'config'/'stack.json').read_text())['defaultModel']
profiles=json.loads((ROOT/'config'/'selected-profiles.json').read_text())
profile=next((p for p in profiles if p['id']==MODEL),None)
if not profile: raise SystemExit('Register an existing Windows model before running inference verification.')
def req(path,data=None,timeout=300):
    r=urllib.request.Request('http://127.0.0.1:10000'+path,None if data is None else json.dumps(data).encode(),{'Authorization':'Bearer '+KEY,'Content-Type':'application/json'})
    with urllib.request.urlopen(r,timeout=timeout) as f:return json.load(f)
def chat(messages,**kw):
    return req('/v1/chat/completions',{'model':MODEL,'messages':messages,'temperature':0,'seed':42,'max_tokens':1024,'chat_template_kwargs':{'enable_thinking':False},**kw})
result={'model':MODEL}
try:
    result['models']=[m['id'] for m in req('/v1/models')['data']]
    start=time.monotonic()
    response=chat([{'role':'user','content':'Reply with exactly LOCAL_BACKEND_OK.'}])
    result['initial']={'seconds':round(time.monotonic()-start,2),'response':response}
    assert 'LOCAL_BACKEND_OK' in response['choices'][0]['message'].get('content','')
    print('Backend chat passed',flush=True)
    tool={'type':'function','function':{'name':'local_echo','description':'Echo the provided text.','parameters':{'type':'object','properties':{'text':{'type':'string'}},'required':['text']}}}
    messages=[{'role':'user','content':'Call local_echo with text LOCAL_TOOL_OK. After the tool responds, reply with its returned text.'}]
    response=chat(messages,tools=[tool],tool_choice={'type':'function','function':{'name':'local_echo'}})
    msg=response['choices'][0]['message']; calls=msg.get('tool_calls',[])
    assert calls and calls[0]['function']['name']=='local_echo'
    assert json.loads(calls[0]['function']['arguments'])['text']=='LOCAL_TOOL_OK'
    result['tool_call']=response
    follow=chat(messages+[msg,{'role':'tool','tool_call_id':calls[0]['id'],'content':'LOCAL_TOOL_OK'}],tools=[tool])
    result['tool_followup']=follow
    assert 'LOCAL_TOOL_OK' in follow['choices'][0]['message'].get('content','')
    print('Tool-call round trip passed',flush=True)
    secret='LOCAL-CONTEXT-OK-7429'
    target=min(16384,profile['context']-2048)
    filler='This is filler text used to verify that the attention cache remains stable.\n'
    per_line=len(req('/tokenize',{'model':MODEL,'content':filler*100})['tokens'])/100
    prompt=f'The verification passphrase is {secret}.\n'+filler*max(1,int((target-150)/per_line))+'\nReturn only the verification passphrase from the beginning of this message.'
    response=chat([{'role':'user','content':prompt}],cache_prompt=False)
    result['long_prompt']=response
    assert secret in response['choices'][0]['message'].get('content','')
    assert response['usage']['prompt_tokens']>=target-512
    print('Long prompt passed: '+str(response['usage']['prompt_tokens'])+' tokens',flush=True)
    result['success']=True
except Exception as exc:
    result['success']=False;result['error']=str(exc)
    print('FAILED: '+str(exc),flush=True)
finally:
    (ROOT/'reports'/'verification'/f'stack-verification-{MODEL}.json').write_text(json.dumps(result,indent=2))
if not result['success']:raise SystemExit(1)

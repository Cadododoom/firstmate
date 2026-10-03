import os,json,subprocess,threading,http.server,urllib.request,urllib.error,pathlib,copy
root=pathlib.Path.cwd(); d=root/'.live-laya'; home=d/'home'; (home/'config').mkdir(parents=True,exist_ok=True); (home/'data').mkdir(exist_ok=True); (home/'state').mkdir(exist_ok=True)
evidence=pathlib.Path('/home/cadodolap_works/.no-mistakes/evidence/01M40GY10ZS9HAJHS15K9R9WXR')
base={k:v for k,v in os.environ.items() if not k.startswith(('FM_','LAYA_','TYPESAFE_','DISPATCH_','TASKS_AXI_'))}
base.update(FM_HOME=str(home),TMPDIR=str(d),LAYA_API_KEY='disposable-laya-key',DISPATCH_SYSTEMONE_PROVIDER='laya')
brief=d/'brief.md'; brief.write_text("# Task\nBOILERPLATE-PRIVATE\n## Captain's intent\nFix the off-by-one bug in pager.sh.\n## Firstmate spec\nChange <= to < so the pager emits exactly one page per call.\n## Delivery\nDELIVERY-PRIVATE\n")
profile={'harness':'codex','model':'gpt-6.1-sol','effort':'medium'}
rules={'rules':[{'when':'Fix the off-by-one bug in pager.sh.', 'use':profile,'why':'WHY-PRIVATE'}],'default':profile}
quota={'schemaVersion':5,'generatedAt':'2030-01-01T00:00:00Z','providers':[{'provider':'codex','state':{'status':'fresh'},'quotaSemantics':{'status':'known','effectiveAvailability':[{'scope':'all_models','status':'known','effectivePercentRemaining':80,'runway':{'status':'through_reset'},'selection':{'spendPriority':0.8}}]}}]}
(d/'quota.json').write_text(json.dumps(quota)); fake=d/'deps'; fake.mkdir(exist_ok=True)
(fake/'quota-axi').write_text('#!/usr/bin/env bash\ncat "'+str(d/'quota.json')+'"\n'); (fake/'quota-axi').chmod(0o755)
realcurl=subprocess.check_output(['which','curl'],text=True).strip()
(fake/'curl').write_text('#!/usr/bin/env python3\nimport os,sys,json\nfrom pathlib import Path\nsecret="disposable-laya-key"\nr={"argv":sys.argv[1:],"secret_in_argv":any(secret in x for x in sys.argv),"secret_in_environment":any(secret in v for v in os.environ.values())}\nwith open("'+str(evidence/'child-privacy.jsonl')+'","a") as f:f.write(json.dumps(r)+"\\n")\nos.execv("'+realcurl+'",["curl"]+sys.argv[1:])\n'); (fake/'curl').chmod(0o755)
base['PATH']=str(fake)+':'+os.environ['PATH']
mode={'kind':'real'}; requests=[]
answer={'model':'jev-compatible-boundary','answers':{'rule':{'type':'choice','choice':'rule_1','confidence':0.99,'probabilities':{'rule_1':0.99,'default':0.01}}},'usage':{'input_tokens':30,'output_tokens':3}}
class Proxy(http.server.BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_POST(self):
  body=self.rfile.read(int(self.headers['Content-Length'])); item={'path':self.path,'request':json.loads(body),'authenticated':self.headers.get('Authorization')=='Bearer disposable-laya-key','mode':mode['kind']}; requests.append(item)
  status=200
  if mode['kind']=='real':
   req=urllib.request.Request('http://127.0.0.1:18765'+self.path,data=body,headers={'Content-Type':'application/json','Authorization':self.headers.get('Authorization','')})
   try:
    with urllib.request.urlopen(req,timeout=60) as r: payload=r.read(); status=r.status
   except urllib.error.HTTPError as e:payload=e.read(); status=e.code
  elif mode['kind']=='500': status=500; payload=b'{"detail":"controlled outage"}'
  else:
   response=copy.deepcopy(answer)
   if mode['kind']=='low':response['answers']['rule']['confidence']=0.4
   if mode['kind']=='malformed':response={'answers':{}}
   payload=json.dumps(response).encode()
  item['status']=status; item['response']=json.loads(payload)
  self.send_response(status);self.end_headers();self.wfile.write(payload)
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Proxy); threading.Thread(target=server.serve_forever,daemon=True).start(); url='http://127.0.0.1:'+str(server.server_port)
base['LAYA_SYSTEMONE_BASE_URL']=url
results=[]
def run(name,expected,env=None,cfg=None,kind='real',no_network=False):
 mode['kind']=kind; (home/'config/crew-dispatch.json').write_text(json.dumps(cfg or rules)); before=len(requests)
 e=base.copy();e.update(env or {});
 p=subprocess.run(['bin/fm-dispatch-resolve.sh',str(brief),'--project','disposable-pager'],env=e,text=True,capture_output=True,timeout=45)
 ok=(expected in p.stdout or expected in p.stderr) and p.returncode==(2 if expected in ['DISPATCH_SYSTEMONE_PROVIDER must','each use profile must name a verified harness'] else 0)
 if no_network:ok=ok and len(requests)==before
 row={'name':name,'pass':ok,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'requests':len(requests)-before};results.append(row);print(json.dumps(row),flush=True)
 return p
try:
 run('Canonical Laya low confidence withholds a concrete profile','status: ambiguous')
 calibrated=copy.deepcopy(rules);calibrated['rules'][0]['min_confidence']=0.5
 run('Canonical Laya probability above declared floor returns concrete medium-effort profile','status: clear',cfg=calibrated)
 (home/'.env').write_text('DISPATCH_SYSTEMONE_PROVIDER=laya\nLAYA_SYSTEMONE_BASE_URL='+url+'\nLAYA_API_KEY=disposable-laya-key\n')
 run('Home .env activates Laya without TypeSafe key','status: clear',cfg=calibrated,env={'DISPATCH_SYSTEMONE_PROVIDER':'','LAYA_SYSTEMONE_BASE_URL':'','LAYA_API_KEY':''})
 run('Environment provider overrides home Laya provider','dispatch-resolve: off',env={'DISPATCH_SYSTEMONE_PROVIDER':'typesafe','TYPESAFE_API_KEY':''},no_network=True)
 (home/'.env').unlink()
 run('Default without TypeSafe key stays off despite Laya URL','dispatch-resolve: off',env={'DISPATCH_SYSTEMONE_PROVIDER':''},no_network=True)
 run('Missing explicit Laya URL reports error without fallback','LAYA_SYSTEMONE_BASE_URL absent',env={'LAYA_SYSTEMONE_BASE_URL':''},no_network=True)
 for invalid in ['http://example.com','https://user:pass@example.com','https://example.com/path','https://example.com?token=x','https://example.com/#x']:
  run('Reject unsafe endpoint '+invalid,'invalid LAYA_SYSTEMONE_BASE_URL',env={'LAYA_SYSTEMONE_BASE_URL':invalid},no_network=True)
 run('Unsupported provider is configuration error','DISPATCH_SYSTEMONE_PROVIDER must',env={'DISPATCH_SYSTEMONE_PROVIDER':'other'},no_network=True)
 for key in ['a\rb','a\nb']:
  run('Reject CR/LF bearer header injection '+repr(key),'provider API key contains a line break',env={'LAYA_API_KEY':key},no_network=True)
 run('Wrong Laya key returns authentication error without fallback','http 401',env={'LAYA_API_KEY':'wrong'})
 run('Laya server outage returns error without fallback','http 500',kind='500')
 run('Malformed response returns error without profile','response is not a rule Choice answer',kind='malformed')
 run('Low confidence returns ambiguity without profile','status: ambiguous',kind='low')
 gated=copy.deepcopy(rules);gated['rules'][0]['approval']='captain'
 run('Provider cannot bypass captain approval','status: escalate',cfg=gated,kind='high')
 q=copy.deepcopy(quota); q['providers'][0]['quotaSemantics']['effectiveAvailability'][0]['effectivePercentRemaining']=0;(d/'quota.json').write_text(json.dumps(q))
 run('Provider cannot select exhausted quota candidate','status: escalate',kind='high')
 (d/'quota.json').write_text(json.dumps(quota))
 floor=copy.deepcopy(rules);floor['rules'][0]['use']['floor']={'scope':'all_models','min_percent':90}
 run('Provider cannot bypass declared quota floor','status: escalate',cfg=floor,kind='high')
 (home/'config/dispatch-never-send').write_text('off-by-one\n')
 run('Never-send task content blocks Laya request','nothing sent',no_network=True)
 (home/'config/dispatch-never-send').unlink()
 cfg=copy.deepcopy(rules);cfg['rules'][0]['min_confidence']=1.0
 run('Per-rule probability floor returns ambiguity','status: ambiguous',cfg=cfg,kind='high')
 tie=copy.deepcopy(rules);tie['rules'][0]['use']=[profile,{'harness':'claude','model':'sonnet','effort':'medium'}]
 q=copy.deepcopy(quota); row=copy.deepcopy(q['providers'][0]);row['provider']='claude';q['providers'].append(row);(d/'quota.json').write_text(json.dumps(q))
 run('Equal spend priority does not choose by array order','status: escalate',cfg=tie,kind='high')
 invalid=copy.deepcopy(rules);invalid['rules'][0]['use']['harness']='not-real'
 run('Unverified harness rejected before network','each use profile must name a verified harness',cfg=invalid,no_network=True)

finally:
 server.shutdown(); (evidence/'resolver-scenarios.json').write_text(json.dumps(results,indent=2));(evidence/'laya-http.json').write_text(json.dumps(requests,indent=2))
 privacy=all('WHY-PRIVATE' not in json.dumps(r['request']) and 'BOILERPLATE-PRIVATE' not in json.dumps(r['request']) and 'DELIVERY-PRIVATE' not in json.dumps(r['request']) and 'gpt-6.1-sol' not in json.dumps(r['request']) and 'effectivePercentRemaining' not in json.dumps(r['request']) for r in requests)
 child=[json.loads(l) for l in (evidence/'child-privacy.jsonl').read_text().splitlines()]
 (evidence/'privacy-result.json').write_text(json.dumps({'request_privacy':privacy,'child_privacy':all(not r['secret_in_argv'] and not r['secret_in_environment'] for r in child)},indent=2))
 print('REQUEST_PRIVACY',privacy,'CHILD_PRIVACY',all(not r['secret_in_argv'] and not r['secret_in_environment'] for r in child))

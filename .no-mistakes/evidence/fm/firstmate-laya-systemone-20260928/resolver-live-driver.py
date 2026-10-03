import os,json,subprocess,http.server,threading,pathlib,copy
root=pathlib.Path.cwd();lab=root/'.validation-laya';home=lab/'home';(home/'config').mkdir(parents=True,exist_ok=True);bindir=lab/'bin';bindir.mkdir(exist_ok=True)
evidence=pathlib.Path('/home/cadodolap_works/.no-mistakes/evidence/01M41CN1Q4MM41MKFCQ2YRKCME')
quota={'schemaVersion':5,'generatedAt':'2026-10-03T00:00:00Z','providers':[{'provider':'codex','state':{'status':'fresh'},'quotaSemantics':{'status':'known','effectiveAvailability':[{'scope':'all_models','status':'known','effectivePercentRemaining':80,'runway':{'status':'through_reset'},'selection':{'spendPriority':0.7}}]}}]}
(lab/'quota.json').write_text(json.dumps(quota))
q=bindir/'quota-axi';q.write_text('#!/usr/bin/env python3\nimport os,json\nassert not os.environ.get("LAYA_API_KEY") and not os.environ.get("TYPESAFE_API_KEY")\nprint(open('+repr(str(lab/'quota.json'))+').read())\n');q.chmod(0o755)
brief=lab/'brief.md';brief.write_text("# Task\n## Captain's intent\nFix the pager off-by-one.\n## Firstmate spec\nUse inclusive bounds.\n## Rules\nDO-NOT-SEND-DELIVERY\n")
base={'rules':[{'when':'Fix pager bugs','use':{'harness':'codex','model':'gpt-6.1-sol','effort':'medium'},'why':'DO-NOT-SEND-WHY'}]}
requests=[];proxies=[];response={};http_status=200
class Endpoint(http.server.BaseHTTPRequestHandler):
 def do_POST(self):
  body=json.loads(self.rfile.read(int(self.headers['Content-Length'])));requests.append({'path':self.path,'auth_present':bool(self.headers.get('Authorization')),'body':body})
  self.send_response(http_status);self.end_headers();self.wfile.write(json.dumps(response).encode())
 def log_message(self,*args):pass
class Proxy(Endpoint):
 def do_POST(self):proxies.append(self.path);self.send_response(502);self.end_headers()
servers=[http.server.ThreadingHTTPServer(('127.0.0.1',0),c) for c in (Endpoint,Proxy)]
for s in servers:threading.Thread(target=s.serve_forever,daemon=True).start()
url=f'http://127.0.0.1:{servers[0].server_port}';proxy=f'http://127.0.0.1:{servers[1].server_port}'
env={k:v for k,v in os.environ.items() if not k.startswith(('FM_','LAYA_','TYPESAFE_','DISPATCH_'))};env.update(FM_HOME=str(home),PATH=str(bindir)+':'+os.environ['PATH'],DISPATCH_SYSTEMONE_PROVIDER='laya',LAYA_SYSTEMONE_BASE_URL=url,TYPESAFE_API_KEY='',LAYA_API_KEY='')
for name in ('HTTP_PROXY','http_proxy','HTTPS_PROXY','https_proxy','ALL_PROXY','all_proxy'):env[name]=proxy
env['no_proxy']=env['NO_PROXY']=''
def answer(conf=.95,p=.95):return {'model':'controlled-boundary-response','answers':{'rule':{'type':'choice','choice':'rule_1','confidence':conf,'probabilities':{'rule_1':p,'default':1-p}}},'usage':{'input_tokens':30,'output_tokens':10}}
log=[];results=[]
def run(name,expected,settings=None,cfg=None,resp=None,status=200,no_request=False):
 global response,http_status
 response=resp if resp is not None else answer();http_status=status;(home/'config/crew-dispatch.json').write_text(json.dumps(cfg or base));before=len(requests)
 e=dict(env);e.update(settings or {});r=subprocess.run([str(root/'bin/fm-dispatch-resolve.sh'),str(brief),'--project','lab'],env=e,capture_output=True,text=True,timeout=35)
 ok=expected in r.stdout+r.stderr
 if no_request:ok=ok and before==len(requests)
 if 'clear' in expected:ok=ok and 'gpt-6.1-sol' in r.stdout and 'medium' in r.stdout
 assert 'lab-bearer-key' not in r.stdout+r.stderr
 results.append({'name':name,'pass':ok,'exit':r.returncode,'requests':len(requests)-before});log.append(f'=== {name}: {"PASS" if ok else "FAIL"} ===\nexit={r.returncode}; requests={len(requests)-before}\n{r.stdout}{r.stderr}')
try:
 run('Local unauthenticated Laya request bypasses hostile proxies','status: clear')
 run('Local authenticated Laya request bypasses hostile proxies','status: clear',{'LAYA_API_KEY':'lab-bearer-key'})
 (home/'.env').write_text(f'DISPATCH_SYSTEMONE_PROVIDER=laya\nLAYA_SYSTEMONE_BASE_URL={url}\nLAYA_API_KEY=lab-bearer-key\n')
 run('Explicit empty provider disables home Laya selection','dispatch-resolve: off',{'DISPATCH_SYSTEMONE_PROVIDER':''},no_request=True)
 run('Explicit empty origin refuses home URL without fallback','status: error',{'LAYA_SYSTEMONE_BASE_URL':''},no_request=True)
 run('Explicit empty auth clears home bearer key','status: clear');assert not requests[-1]['auth_present']
 # Allow home selection by removing provider vars from the child environment.
 saved=dict(env)
 for k in ('DISPATCH_SYSTEMONE_PROVIDER','LAYA_SYSTEMONE_BASE_URL','LAYA_API_KEY'):env.pop(k,None)
 run('Home .env selects Laya without TypeSafe key','status: clear');assert requests[-1]['auth_present'];env.clear();env.update(saved)
 (home/'.env').unlink()
 for origin in ['http://example.com','https://user:secret@example.com','https://example.com/path','https://example.com?x=1','https://example.com#frag']:
  run('Reject unsafe origin '+origin,'invalid LAYA_SYSTEMONE_BASE_URL',{'LAYA_SYSTEMONE_BASE_URL':origin},no_request=True)
 run('Reject bearer header injection','contains a line break',{'LAYA_API_KEY':'x\ny'},no_request=True)
 run('Unknown provider is a configuration error','must be typesafe or laya',{'DISPATCH_SYSTEMONE_PROVIDER':'invalid'},no_request=True)
 run('Unavailable provider fails without fallback','status: error',{'LAYA_SYSTEMONE_BASE_URL':'http://127.0.0.1:1'})
 run('Unauthorized provider fails without fallback','status: error',status=401)
 run('Malformed model answer fails closed','status: error',resp={'answers':{}})
 run('Invalid probability mass fails closed','status: error',resp=answer(p=1.1))
 run('Confidence below global floor is ambiguous','status: ambiguous',resp=answer(conf=.599))
 run('Confidence at global floor can resolve','status: clear',resp=answer(conf=.6))
 cfg=copy.deepcopy(base);cfg['rules'][0]['min_confidence']=.8
 run('Declared probability below floor is ambiguous','status: ambiguous',cfg=cfg,resp=answer(p=.799))
 run('Declared probability at floor can resolve','status: clear',cfg=cfg,resp=answer(conf=.1,p=.8))
 cfg=copy.deepcopy(base);cfg['rules'][0]['approval']='captain'
 run('Captain approval rule escalates','status: escalate',cfg=cfg)
 quota['providers'][0]['quotaSemantics']['effectiveAvailability'][0]['effectivePercentRemaining']=0;(lab/'quota.json').write_text(json.dumps(quota))
 run('Exhausted quota vetoes profile outside inference','status: escalate')
 (home/'config/dispatch-never-send').write_text('pager off-by-one\n');run('Never-send matching brief prevents network','dispatch-resolve: off',no_request=True);(home/'config/dispatch-never-send').unlink()
 cfg=copy.deepcopy(base);cfg['rules'][0]['use']=[dict(base['rules'][0]['use']),dict(base['rules'][0]['use'],effort='high')]
 quota['providers'][0]['quotaSemantics']['effectiveAvailability'][0]['effectivePercentRemaining']=80;(lab/'quota.json').write_text(json.dumps(quota))
 run('Genuine quota tie escalates outside inference','status: escalate',cfg=cfg)
 cfg=copy.deepcopy(base);cfg['rules'][0]['use']['floor']={'scope':'all_models','min_percent':90}
 run('Profile quota floor vetoes candidate outside inference','status: escalate',cfg=cfg)
 body=json.dumps(requests[0]['body']);assert all(s not in body for s in ['DO-NOT-SEND-DELIVERY','DO-NOT-SEND-WHY','lab-bearer-key','gpt-6.1-sol','spendPriority','account']);assert not proxies
 log.append('Transport evidence: '+json.dumps({'endpoint_requests':len(requests),'proxy_requests':len(proxies),'first_request':requests[0],'secrets_profiles_and_quota_absent_from_request':True},indent=2))
finally:
 for s in servers:s.shutdown();s.server_close()
 (evidence/'resolver-live-transcript.log').write_text('\n'.join(log));(evidence/'resolver-live-results.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results,indent=2));assert all(r['pass'] for r in results)

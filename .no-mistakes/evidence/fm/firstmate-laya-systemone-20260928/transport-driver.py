import pathlib,json,os,subprocess,time,urllib.request
root=pathlib.Path.cwd();d=root/'.live-laya';home=d/'home';
for i in range(20):
 try:
  health=json.load(urllib.request.urlopen('http://127.0.0.1:18765/health',timeout=1));break
 except Exception:time.sleep(1)
else:raise RuntimeError('unauthenticated canonical server did not start')
(home/'config/crew-dispatch.json').write_text(json.dumps({'rules':[{'when':'Fix the off-by-one bug in pager.sh.','min_confidence':0.5,'use':{'harness':'codex','model':'gpt-6.1-sol','effort':'medium'}}],'default':{'harness':'codex','model':'gpt-6.1-sol','effort':'medium'}}))
e={k:v for k,v in os.environ.items() if not k.startswith(('FM_','LAYA_','TYPESAFE_','DISPATCH_','TASKS_AXI_'))}
e.update(FM_HOME=str(home),TMPDIR=str(d),PATH=str(d/'deps')+':'+os.environ['PATH'],DISPATCH_SYSTEMONE_PROVIDER='laya',LAYA_SYSTEMONE_BASE_URL='http://127.0.0.1:18765',LAYA_API_KEY='')
p=subprocess.run(['bin/fm-dispatch-resolve.sh',str(d/'brief.md'),'--project','disposable-pager'],env=e,capture_output=True,text=True,timeout=45)
e['LAYA_SYSTEMONE_BASE_URL']='http://127.0.0.1:18766'
p=subprocess.run(['bin/fm-dispatch-resolve.sh',str(d/'brief.md'),'--project','disposable-pager'],env=e,capture_output=True,text=True,timeout=45)
r={'name':'Unreachable Laya returns transport error without fallback','pass':p.returncode==0 and 'http 000' in p.stdout and 'profile:' not in p.stdout,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
pathlib.Path('/home/cadodolap_works/.no-mistakes/evidence/01M40GY10ZS9HAJHS15K9R9WXR/transport-failure.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))

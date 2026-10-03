import os,subprocess,pathlib,json
root=pathlib.Path.cwd(); home=root/'.live-laya/bootstrap-home'
for part in ['config','state','data','projects']: (home/part).mkdir(parents=True,exist_ok=True)
(home/'config/backlog-backend').write_text('manual\n')
(home/'config/crew-dispatch.json').write_text(json.dumps({'rules':[{'when':'Fix a bug','approval':'invalid-approval','use':{'harness':'codex','model':'gpt-6.1-sol','effort':'medium'}}]}))
env={k:v for k,v in os.environ.items() if not k.startswith(('FM_','LAYA_','TYPESAFE_','DISPATCH_','TASKS_AXI_'))}
env.update(FM_HOME=str(home),FM_ROOT_OVERRIDE=str(home),FM_BOOTSTRAP_DETECT_ONLY='1',FM_BOOTSTRAP_NETWORK='skip')
log=[]
for label,settings,envfile,expected in [('default off',{},'',False),('explicit Laya',{'DISPATCH_SYSTEMONE_PROVIDER':'laya','LAYA_API_KEY':'disposable-bootstrap-key'},'',True),('home .env Laya',{},'DISPATCH_SYSTEMONE_PROVIDER=laya\n',True),('environment TypeSafe overrides home Laya',{'DISPATCH_SYSTEMONE_PROVIDER':'typesafe'},'DISPATCH_SYSTEMONE_PROVIDER=laya\n',False)]:
 (home/'.env').write_text(envfile)
 e=env.copy();e.update(settings)
 p=subprocess.run(['bin/fm-bootstrap.sh'],env=e,capture_output=True,text=True,timeout=45)
 diag=[line for line in p.stdout.splitlines() if line.startswith('CREW_DISPATCH:')]
 ok=bool(diag)==expected and (not expected or 'approval must be "captain"' in '\n'.join(diag))
 log.append({'name':label,'pass':ok,'exit':p.returncode,'dispatch_diagnostics':diag,'stdout':p.stdout,'stderr':p.stderr})
 print(label,ok,diag,flush=True)
pathlib.Path('/home/cadodolap_works/.no-mistakes/evidence/01M40GY10ZS9HAJHS15K9R9WXR/bootstrap-scenarios.json').write_text(json.dumps(log,indent=2))

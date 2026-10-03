import os,pathlib,subprocess,json
root=pathlib.Path.cwd();home=root/'.validation-laya/bootstrap-home';(home/'config').mkdir(parents=True,exist_ok=True)
(home/'config/backlog-backend').write_text('manual\n');(home/'config/crew-dispatch.json').write_text('{"rules":[{"when":"bug","approval":"firstmate","use":{"harness":"codex"}}]}')
env={k:v for k,v in os.environ.items() if not k.startswith(('FM_','LAYA_','DISPATCH_','TYPESAFE_'))};env.update(FM_HOME=str(home),FM_ROOT_OVERRIDE=str(home),FM_BOOTSTRAP_DETECT_ONLY='1',FM_BOOTSTRAP_NETWORK='skip',TYPESAFE_API_KEY='')
logs=[]
for name,provider,dotenv,expected in [('Environment Laya enables typed validation','laya','',True),('Home Laya enables typed validation',None,'DISPATCH_SYSTEMONE_PROVIDER=laya\n',True),('Empty provider overrides home Laya','', 'DISPATCH_SYSTEMONE_PROVIDER=laya\n',False),('Empty TypeSafe key overrides home key','typesafe','TYPESAFE_API_KEY=home-key\n',False)]:
 (home/'.env').write_text(dotenv);e=dict(env)
 if provider is not None:e['DISPATCH_SYSTEMONE_PROVIDER']=provider
 p=subprocess.run([str(root/'bin/fm-bootstrap.sh')],env=e,capture_output=True,text=True,timeout=40)
 text=p.stdout+p.stderr;active='approval must be "captain" when present' in text
 logs.append(f'=== {name}: {"PASS" if active==expected else "FAIL"} ===\n{text}')
 assert active==expected,(name,text)
pathlib.Path('/home/cadodolap_works/.no-mistakes/evidence/01M41CN1Q4MM41MKFCQ2YRKCME/bootstrap-live.log').write_text('\n'.join(logs))
print('All four real bootstrap activation scenarios passed (detect-only, network skipped).')

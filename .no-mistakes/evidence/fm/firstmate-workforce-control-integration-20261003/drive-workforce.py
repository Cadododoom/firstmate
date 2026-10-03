import os,json,pathlib,subprocess,tempfile,shutil
root=pathlib.Path.cwd()
home=pathlib.Path(tempfile.mkdtemp(prefix='.workforce-live-',dir=root))
env={k:v for k,v in os.environ.items() if not k.startswith('FM_') and not k.startswith('TASKS_AXI')}
env.update(FM_HOME=str(home),GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_NOSYSTEM='1',CODEX_HOME=str(home/'catalog'))
def cmd(args,body=None,ok=True):
 r=subprocess.run(args,input=body,text=True,capture_output=True,env=env)
 print('$ '+' '.join(map(str,args)))
 if body: print('stdin: '+body)
 print('exit:',r.returncode);print(r.stdout.rstrip());print(r.stderr.rstrip())
 assert (r.returncode==0)==ok,(args,r.stdout,r.stderr)
 return r.stdout
cli=['python3',str(root/'bin/fm-workforce.py')]
def call(verb,value=None,ok=True):return json.loads(cmd(cli+verb,json.dumps(value) if value is not None else None,ok))
def req(rid,action,scope,payload):return dict(schema='fm-workforce-request.v1',request_id=rid,action=action,scope=scope,payload=payload)
try:
 cmd(['bash',str(root/'bin/fm-lab-home.sh'),'create',str(home)])
 (home/'data/projects.md').write_text('- demo [direct-PR] - isolated verification (added 2026-10-03)\n')
 project=home/'projects/demo';project.mkdir()
 def git(*args):return cmd(['git','-C',str(project),*args]).strip()
 git('init','-b','fm/batch');git('config','user.name','Disposable Test');git('config','user.email','test@example.invalid')
 (project/'batch.txt').write_text('completed batch\n');git('add','.');git('commit','-m','Completed disposable batch')
 head=git('rev-parse','HEAD')
 meta=f'project={project}\nspawn_gen=gen-1\nkind=ship\nharness=codex\nbackend=tmux\nbranch=fm/batch\nworktree={project}\nmode=direct-PR\nyolo=off\n'
 (home/'state/job.meta').write_text(meta)
 scope=dict(project='demo',job='job',batch='batch-v1',branch='fm/batch',head=head)
 request=req('batch-1','validation-request',scope,dict(posture='assistant',delivery_mode='no-mistakes'))
 note=call(['submit'],request);assert note['outcome']=='created'
 assert call(['submit'],request)['id']==note['id']
 call(['submit'],dict(request,payload=dict(posture='assistant',delivery_mode='direct-PR')),False)
 print('DURABLE WAKE:',(home/'state/.wake-queue').read_text())
 print('DURABLE NOTE:',(home/'state/inbox'/f"{note['id']}.note").read_text())
 reply=dict(decision='approved',reason='exact completed batch',scope=scope)
 call(['answer',note['id']],dict(reply,scope=dict(scope,batch='wrong')),False)
 call(['answer',note['id']],reply)
 call(['receipts','--all-replies'])
 cmd(['bash',str(root/'bin/fm-inbox.sh'),'drain','--ack',note['id']])
 assert call(['submit'],request)['acknowledged']
 nextnote=call(['submit'],dict(request,request_id='batch-2'))
 (project/'batch.txt').write_text('dirty\n')
 call(['answer',nextnote['id']],reply,False)
 git('add','.');git('commit','-m','New batch')
 call(['answer',nextnote['id']],reply,False)
 assert call(['submit'],request)['outcome']=='replay'
 for mode in ['local-only','direct-PR','no-mistakes']:
  for posture in ['assistant','autonomy']:
   call(['submit'],req('policy-'+mode+'-'+posture,'policy-request',dict(project='demo'),dict(posture=posture,delivery_mode=mode,merge_autonomy=True)))
 call(['submit'],req('injection','policy-request',dict(project='demo'),dict(posture='assistant',delivery_mode='local-only',merge_autonomy=False,executable='/bin/sh')),False)
 (home/'state/job.meta').write_text(meta.replace('mode=direct-PR','mode=local-only'))
 call(['submit'],dict(request,request_id='local-validation',scope=dict(scope,head=git('rev-parse','HEAD'))),False)
 (home/'state/job.meta').write_text(meta)
 view=call(['status'])
 for verb,c in view['windows'][0]['verbs'].items():
  payload=dict(verb=verb)
  if verb in ['send-instruction','relaunch']:payload['text']='checkpoint'
  call(['submit'],req('window-'+verb,'window-request',dict(project='demo',job='job',generation='gen-1'),payload),c['request_supported'])
 call(['submit'],req('stale-generation','window-request',dict(project='demo',job='job',generation='gen-0'),dict(verb='exit')),False)
 (home/'state/job.meta').write_text(meta.replace(f'project={project}',f'project={home}/secondmates/demo').replace('kind=ship','kind=secondmate').replace('harness=codex','harness=pi'))
 secondmate=call(['status']);assert all(not c['request_supported'] for c in secondmate['windows'][0]['verbs'].values())
 (home/'state/job.meta').write_text(meta)
 for level,extras in [('global',{}),('project',dict(project='demo')),('job',dict(project='demo',job='job',generation='gen-1'))]:
  ds=dict(level=level,**extras)
  good=call(['submit'],req('defaults-'+level,'defaults-request',ds,dict(harness='codex',effort='high')))
  call(['answer',good['id']],dict(decision='approved',reason='supported preferences',scope=ds))
  call(['submit'],req('ultra-'+level,'defaults-request',ds,dict(harness='codex',effort='ultra')),False)
 (home/'config/crew-harness').write_text('codex\n')
 explicit=call(['status']);assert explicit['preferences']['revision']!=view['preferences']['revision']
 assert (home/'state/job.meta').read_text()==meta
 (home/'config/crew-dispatch.json').write_text(json.dumps(dict(default=dict(harness='codex',model=123,effort='high'))))
 invalid=call(['status']);assert not invalid['preferences']['global']['dispatch_default']['configuration_valid']
 assert '+yolo' not in (home/'data/projects.md').read_text()
 assert not (home/'data/backlog.md').exists()
 assert git('remote')==''
 print('Verified: approved replies did not execute lifecycle, modify metadata/project policy, create backlog, or publish Git remotes.')
finally:
 shutil.rmtree(home)
 print('Disposable lab removed:',home)

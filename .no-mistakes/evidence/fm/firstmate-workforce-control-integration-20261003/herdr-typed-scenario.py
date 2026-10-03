import json, os, pathlib, subprocess
root=pathlib.Path.cwd(); home=pathlib.Path(os.environ['FM_HOME'])
helper=os.environ['HERDR_LAB_HELPER']; session=os.environ['HERDR_LAB_SESSION']
def named(*args):
 r=subprocess.run([helper,'run',session,*args],capture_output=True,text=True)
 print('HERDR',args,'exit',r.returncode,r.stdout,r.stderr,flush=True)
 assert r.returncode==0
 return json.loads(r.stdout)
created=named('workspace','create','--cwd',str(home),'--label','workforce-owned-test','--no-focus')
before=named('pane','list')
panes=before['result']['panes']; assert len(panes)==1,panes
print('OWNED PANE',panes,flush=True)
pane=panes[0]['pane_id']
def inventory(value):
 return [{k:p.get(k) for k in ['pane_id','tab_id','workspace_id','terminal_id','cwd','agent_status','focused']} for p in value['result']['panes']]
(home/'projects/demo').mkdir()
(home/'data/projects.md').write_text('- demo [local-only] - synthetic lab (added 2026-10-03)\n')
meta=f'project={home}/projects/demo\nspawn_gen=owned-gen\nkind=ship\nharness=codex\nbackend=herdr\nwindow={session}:{pane}\nmode=local-only\nyolo=off\n'
(home/'state/owned.meta').write_text(meta)
# The real CLI's backend reads also route through the named helper.
shim=home/'named-bin';shim.mkdir()
original_path=os.environ['PATH']
(shim/'herdr').write_text('''#!/usr/bin/env python3
import os,sys
args=sys.argv[1:]; clean=[]; i=0
while i<len(args):
 if args[i]=='--session':
  if i+1>=len(args) or args[i+1]!=os.environ['HERDR_LAB_SESSION']: sys.exit('foreign session refused')
  i+=2
 elif args[i].startswith('--session='):
  if args[i].split('=',1)[1]!=os.environ['HERDR_LAB_SESSION']: sys.exit('foreign session refused')
  i+=1
 else: clean.append(args[i]); i+=1
os.environ['PATH']=os.environ['HERDR_ORIGINAL_PATH']
os.execv(os.environ['HERDR_LAB_HELPER'],[os.environ['HERDR_LAB_HELPER'],'run',os.environ['HERDR_LAB_SESSION'],*clean])
''')
(shim/'herdr').chmod(0o700)
env=os.environ.copy();env.update(PATH=str(shim)+':'+original_path,HERDR_ORIGINAL_PATH=original_path)
def call(args,value=None,ok=True):
 r=subprocess.run(['python3',str(root/'bin/fm-workforce.py'),*args],input=json.dumps(value) if value else None,text=True,capture_output=True,env=env)
 print('WORKFORCE',args,'stdin',value,'exit',r.returncode,r.stdout,r.stderr,flush=True)
 assert (r.returncode==0)==ok
 return json.loads(r.stdout)
view=call(['status']);row=view['windows'][0]
assert row['job']=='owned' and row['backend']=='herdr'
scope=dict(project='demo',job='owned',generation='owned-gen')
for verb in ['send-instruction','interrupt','exit','relaunch']:
 assert row['verbs'][verb]['request_supported'] and not row['verbs'][verb]['direct_execution']
 payload=dict(verb=verb)
 if verb in ['send-instruction','relaunch']:payload['text']='synthetic owned checkpoint'
 request=dict(schema='fm-workforce-request.v1',request_id='named-'+verb,action='window-request',scope=scope,payload=payload)
 note=call(['submit'],request)
 assert call(['submit'],request)['id']==note['id']
 call(['answer',note['id']],dict(decision='approved',reason='synthetic supervisor scope check only',scope=scope))
 call(['submit'],dict(request,request_id='stale-'+verb,scope=dict(scope,generation='stale')),False)
 assert (home/'state/owned.meta').read_text()==meta
 assert inventory(named('pane','list'))==inventory(before)
call(['receipts','--all-replies'])
assert (home/'state/.wake-queue').exists()
assert not (home/'data/backlog.md').exists()
print('PASS: four typed window actions, replay, approved scoped replies, stale refusal, durable receipts/wake; no lifecycle execution or pane/metadata mutation',flush=True)

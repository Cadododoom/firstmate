import socket,json,sys,time,pathlib
base=pathlib.Path(__file__).parent
s=socket.socket(socket.AF_UNIX);s.connect(str(base/'g/q'));f=s.makefile('rwb',buffering=0)
def read():
 while True:
  o=json.loads(f.readline())
  if 'event' not in o:return o
def call(cmd,args={}):
 f.write((json.dumps(dict(execute=cmd,arguments=args))+'\n').encode());return read()
read();call('qmp_capabilities')
if sys.argv[1]=='shot':print(call('screendump',dict(filename=str(base/sys.argv[2]),format='png')))
elif sys.argv[1]=='key':
 for key in sys.argv[2:]:
  print(call('send-key',dict(keys=[dict(type='qcode',data=k) for k in key.split('+')],**{"hold-time":70})));time.sleep(.15)
elif sys.argv[1]=='type':
 mapping={'<':'shift+comma',',':'comma',' ':'spc','/':'slash','-':'minus','.':'dot','_':'shift+minus',':':'shift+semicolon',';':'semicolon','=':'equal','>':'shift+dot','|':'shift+backslash','(':'shift+9',')':'shift+0','"':'shift+apostrophe',"'":'apostrophe','&':'shift+7','$':'shift+4','!':'shift+1','\n':'ret'}
 for c in sys.argv[2]:
  key=mapping.get(c,'shift+'+c.lower() if c.isupper() else c)
  r=call('send-key',dict(keys=[dict(type='qcode',data=k) for k in key.split('+')],**{"hold-time":40}));time.sleep(.07)
 print(r)
else:print(call(sys.argv[1]))

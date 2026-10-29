"""Explicit live check in an approved, stopped native Autoverse simulation.

Drives only the owned Pygame window using X11 keyboard events, then closes it
and verifies complete owned cleanup. Requires contributor test dependencies.
The new private data directory contains credentials; export verification.json only.
"""
import argparse
import ctypes as C
import ctypes.util
import json, os, subprocess, time
from pathlib import Path
from fastapi.testclient import TestClient
from xverse_studio.api.app import create_app
from xverse_studio.providers.autoverse.adapter import AutoverseProvider
from xverse_studio.providers.autoverse.installation import enroll
from xverse_studio.storage.core import atomic, canonical

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--autoverse-root', type=Path, required=True)
parser.add_argument('--data-dir', type=Path, required=True)
args = parser.parse_args()
root = args.data_dir.resolve()
root.mkdir(mode=0o700, parents=True, exist_ok=False)
i = enroll(args.autoverse_root)
app = create_app(root, allowed_hosts=['testserver'], bootstrap_token='isolated-local-check', installed_providers={'autoverse.demo':AutoverseProvider(i)})
report = {'outcome':'failed', 'scope':'actual native Linux full demo with original Pygame keyboard input', 'observations':[]}
with TestClient(app) as c:
 c.headers['Origin']='http://testserver'
 login=c.post('/api/v1/session',json={'bootstrapToken':'isolated-local-check'});assert login.status_code==200
 c.headers['X-CSRF-Token']=login.json()['csrfToken']
 p=c.post('/api/v1/projects',json={'name':'Pygame native verification','blueprintRef':'autoverse-classic'}).json()
 pf=c.post('/api/v1/projects/'+p['projectId']+'/preflights',json={'revision':p['revision'],'providerId':'autoverse.demo'}).json()
 print('PREFLIGHT',pf['status'],flush=True);assert pf['status']=='ready',pf
 accepted=c.post('/api/v1/runs',json={'preflightId':pf['preflightId'],'snapshotId':pf['snapshotId']},headers={'Idempotency-Key':'native-pygame-check'})
 assert accepted.status_code==202,accepted.text
 rid=accepted.json()['runId'];print('RUN',rid,flush=True)
 run=lambda:c.get('/api/v1/runs/'+rid).json()
 try:
  deadline=time.monotonic()+540;last=None
  while time.monotonic()<deadline:
   v=run();phase=(v['state'],v.get('runtimeStatus',{}).get('phase'),v.get('reason'))
   if phase!=last: print('OBSERVED',phase,flush=True);last=phase
   if v['state']=='running':break
   assert v['state'] not in ('failed','stopped'),v
   time.sleep(1)
  assert v['state']=='running',v
  assert v['inputSurface']['kind']=='native-window'
  assert c.post('/api/v1/runs/'+rid+'/input/acquire',json={}).json()['code']=='CAPABILITY_UNSUPPORTED'
  ready=json.loads((root/'runs'/rid/'manual-window.private.json').read_text())
  import psutil
  owner=json.loads((root/'runs'/rid/'resources.private.json').read_text())['manual']
  proc=psutil.Process(ready['pid'])
  assert ready['pid']==owner['pid'] and proc.create_time()==owner['createTime']
  from xverse_studio.storage.core import digest
  assert digest(proc.cmdline())==owner['argvDigest']
  info=subprocess.check_output(['xwininfo','-id',str(ready['windowId'])],text=True)
  assert 'Vehicle Manual Control' in info and 'IsViewable' in info
  report['window']={k:ready[k] for k in ('title','keyboardOnly')};report['window']['viewable']=True
  x=C.CDLL(ctypes.util.find_library('X11'));xt=C.CDLL(ctypes.util.find_library('Xtst'))
  x.XOpenDisplay.restype=C.c_void_p;x.XOpenDisplay.argtypes=[C.c_char_p]
  display=x.XOpenDisplay(None);assert display
  x.XSetInputFocus.argtypes=[C.c_void_p,C.c_ulong,C.c_int,C.c_ulong]
  x.XRaiseWindow.argtypes=[C.c_void_p,C.c_ulong]
  x.XGetInputFocus.argtypes=[C.c_void_p,C.POINTER(C.c_ulong),C.POINTER(C.c_int)]
  x.XFlush.argtypes=[C.c_void_p]
  x.XStringToKeysym.argtypes=[C.c_char_p];x.XStringToKeysym.restype=C.c_ulong
  x.XKeysymToKeycode.argtypes=[C.c_void_p,C.c_ulong];x.XKeysymToKeycode.restype=C.c_uint
  xt.XTestFakeKeyEvent.argtypes=[C.c_void_p,C.c_uint,C.c_int,C.c_ulong]
  def focus():
   x.XRaiseWindow(display,ready['windowId']);x.XSetInputFocus(display,ready['windowId'],2,0);x.XFlush(display)
   assert proc.create_time()==owner['createTime'] and digest(proc.cmdline())==owner['argvDigest']
   actual=C.c_ulong();revert=C.c_int();x.XGetInputFocus(display,C.byref(actual),C.byref(revert));assert actual.value==ready['windowId']
  def key(name,pressed):
   focus();code=x.XKeysymToKeycode(display,x.XStringToKeysym(name.encode()));assert code
   assert xt.XTestFakeKeyEvent(display,code,int(pressed),0);x.XFlush(display)
  key('w',True)
  try:
   for _ in range(12):
    time.sleep(.3);v=run();report['observations'].append(v['inputTelemetry'])
    if (v['inputTelemetry']['items']['speed']['value'] or 0)>15:break
   speed=v['inputTelemetry']['items']['speed']['value'];print('ACTUAL_SPEED',speed,flush=True);assert speed>12,speed
   probe=subprocess.check_output(['/usr/bin/python3','-E',str(Path.cwd()/'services/studio-api/src/xverse_studio/providers/autoverse/carla_probe.py'),'--vehicle-status'],timeout=15,text=True)
   (root/'actual-carla-control.json').write_text(probe)
  finally:key('w',False)
  key('c',True);time.sleep(.15);key('c',False)
  deadline=time.monotonic()+20
  while time.monotonic()<deadline:
   v=run()
   if v['inputTelemetry']['items']['cruiseEngaged']['value'] is True:break
   time.sleep(.3)
  assert v['inputTelemetry']['items']['cruiseEngaged']['value'] is True,v['inputTelemetry']
  report['cruiseEngaged']=True
  key('s',True);time.sleep(3);key('s',False)
  print('NATIVE_WINDOW_DRIVING_AND_CRUISE_PASS',flush=True)
  key('Escape',True);time.sleep(.1);key('Escape',False)
  deadline=time.monotonic()+100
  while time.monotonic()<deadline:
   v=run()
   if v['state'] in ('stopped','failed'):break
   time.sleep(1)
  assert v['state']=='stopped' and v['cleanup']=='complete',v
  assert v.get('reason')=='AUTOVERSE_MANUAL_WINDOW_CLOSED',v
  report.update(outcome='passed',windowCloseStopsDemo=True,cleanup=v['cleanup'],actualKeyboardSpeed=speed)
 finally:
  v=run()
  if v['state'] in ('running','preparing','ready'):
   c.post('/api/v1/runs/'+rid+'/commands',json={'kind':'stop','expectedStateVersion':v['stateVersion']},headers={'Idempotency-Key':'native-pygame-final-stop'})
   for _ in range(100):
    time.sleep(1);v=run()
    if v['state'] in ('stopped','failed'):break
  print('FINAL',v['state'],v.get('cleanup'),v.get('reason'),flush=True)
  atomic(root/'final.json',canonical(v).encode());atomic(root/'verification.json',canonical(report).encode())

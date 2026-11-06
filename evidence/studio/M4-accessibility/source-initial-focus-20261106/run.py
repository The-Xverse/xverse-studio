from pathlib import Path
import subprocess
import sys
root=Path.cwd();state=Path(__file__).resolve().parent;prefix=root.parents[3]
phase=sys.argv[1]; width=sys.argv[2]; suite=sys.argv[3] if len(sys.argv)>3 else 'scenario-stimulus'
argv=[sys.executable,'-I','tests/live/autoverse_orca_browser.py','--recording',str(root/'.studio-local/t088-assessment-mapping/native-newenv-5/demo'),'--static-dir',str(root/'.studio-local/t097-source-initial-focus-20261106/ui2'),'--output',str(state/phase),'--node',str(prefix/'.xverse-studio-cache/node-v24.22.1-linux-x64/bin/node'),'--browser-cache',str(prefix/'.xverse-studio-cache/playwright'),'--xvfb',str(prefix/'.studio-test-e1e2e50a/virtual-display/package/usr/bin/Xvfb'),'--width',width,'--suite',suite]
if len(sys.argv)>4: argv.extend(['--source-exit',sys.argv[4]])
# Replace this trusted contributor supervisor, preserving the original tool handle.
import os
os.execv(sys.executable,argv)

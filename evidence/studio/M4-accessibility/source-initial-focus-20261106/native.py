from pathlib import Path
import os
import sys

root=Path.cwd();local=Path(__file__).resolve().parent;prefix=root.parents[3]
argv=[sys.executable,'-I','tests/live/autoverse_playback_browser.py','--suite','authoring','--recording',str(root/'.studio-local/t088-assessment-mapping/native-newenv-5/demo'),'--static-dir',str(local/'ui2'),'--output',str(local/sys.argv[1]),'--node',str(prefix/'.xverse-studio-cache/node-v24.22.1-linux-x64/bin/node'),'--playwright-cli','[MAIN_CHECKOUT]/node_modules/@playwright/test/cli.js','--browser-cache',str(prefix/'.xverse-studio-cache/playwright'),'--isolate-browser-devices']
if len(sys.argv)>2:argv.extend(['--case-filter',sys.argv[2]])
os.execv(sys.executable,argv)

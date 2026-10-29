"""Recognize only unchanged middleware scratch left by this Studio installation.

Scratch is retained after stop. A subsequent admitted native entry point may
reinitialize its own scratch. Never adopt an unrelated pre-existing namespace.
"""
from pathlib import Path
import hashlib
import json
import os
import stat
from xverse_studio.storage.core import atomic, canonical, digest

ROOTS = (Path('/tmp/mw_com_lola'), Path('/tmp/score-xverse'))


def receipt_path(installation):
    return Path('/tmp') / ('xverse-autoverse-' + str(os.getuid()) + '-' + hashlib.sha256(installation['root'].encode()).hexdigest()[:20] + '.scratch.json')


def inventory():
    rows = []
    size = 0
    for root in ROOTS:
        if not root.exists():
            continue
        pending = [root]
        while pending:
            path = pending.pop()
            info = path.lstat()
            if len(rows) >= 4096 or not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)):
                raise ValueError('AUTOVERSE_SCRATCH_UNKNOWN')
            entry = {'path':str(path), 'device':info.st_dev,'inode':info.st_ino,'mode':info.st_mode,'size':info.st_size,'mtimeNs':info.st_mtime_ns}
            if stat.S_ISDIR(info.st_mode):
                with os.scandir(path) as children:
                    for child in children:
                        if len(pending) + len(rows) >= 4096:
                            raise ValueError('AUTOVERSE_SCRATCH_LIMIT')
                        pending.append(Path(child.path))
            if stat.S_ISREG(info.st_mode):
                size += info.st_size
                if size > 8*1024*1024:
                    raise ValueError('AUTOVERSE_SCRATCH_LIMIT')
                fd = os.open(path,os.O_RDONLY | os.O_NOFOLLOW)
                with os.fdopen(fd,'rb') as stream:
                    if os.fstat(stream.fileno()).st_ino != info.st_ino:
                        raise ValueError('AUTOVERSE_SCRATCH_CHANGED')
                    entry['sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
            rows.append(entry)
    return sorted(rows,key=lambda row:row["path"])


def remember(installation, started_at):
    receipt={'scoreIdentityDigest':digest({'container':installation['containers']['score'],'files':installation['containerFiles']}),'containerStartedAt':started_at,'inventory':inventory()}
    path=receipt_path(installation)
    atomic(path,canonical(receipt).encode())
    path.chmod(0o600)


def recognized(installation, score_row):
    try:
        path=receipt_path(installation)
        info=path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077 or info.st_size>2*1024*1024:
            return False
        receipt=json.loads(path.read_text())
        return (receipt['scoreIdentityDigest']==digest({'container':installation['containers']['score'],'files':installation['containerFiles']}) and not score_row['State']['Running']
            and receipt['containerStartedAt']==score_row['State']['StartedAt'] and receipt['inventory']==inventory())
    except (OSError,ValueError,KeyError):
        return False

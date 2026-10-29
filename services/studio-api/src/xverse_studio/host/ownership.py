"""One native launcher or maintenance operation owns a private data root."""

from contextlib import contextmanager
import os
import stat


class RootOwnedError(OSError):
    pass


class RootUnsafeError(OSError):
    pass


@contextmanager
def own_root(root):
    path = root / "studio.lock"
    if path.is_symlink() or path.exists() and not path.is_file():
        raise RootUnsafeError("RECOVERY_UNSAFE_FILE")
    flags = (
        os.O_RDWR
        | os.O_CREAT
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    descriptor = os.open(path, flags, 0o600)
    if not stat.S_ISREG(os.fstat(descriptor).st_mode):
        os.close(descriptor)
        raise RootUnsafeError("RECOVERY_UNSAFE_FILE")
    lockfile = os.fdopen(descriptor, "r+b")
    try:
        try:
            if os.name == "nt":
                import msvcrt

                lockfile.seek(0)
                lockfile.write(b"0")
                lockfile.flush()
                lockfile.seek(0)
                msvcrt.locking(lockfile.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(lockfile.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise RootOwnedError("RECOVERY_ROOT_OWNED") from None
        yield
    finally:
        lockfile.close()

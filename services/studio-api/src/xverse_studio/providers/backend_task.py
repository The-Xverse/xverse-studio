"""Explicit native backend task ownership for installed in-process services.

A task owns no process signalling authority. Its identity is the actual backend
birth plus an opaque task ID, and liveness also requires the original task handle.
"""

import threading
import uuid

import psutil


class BackendTask:
    def __init__(self, target):
        process = psutil.Process()
        self.pid = process.pid
        self.create_time = process.create_time()
        self.argv = process.cmdline()
        self.task_id = "task-" + uuid.uuid4().hex
        self._done = threading.Event()
        self._started = False
        self._result = None

        def execute():
            try:
                self._result = int(target(self.task_id))
            except BaseException:
                self._result = 1
            finally:
                self._done.set()

        self._thread = threading.Thread(target=execute, name=self.task_id, daemon=True)

    def start(self):
        if self._started:
            raise RuntimeError("BACKEND_TASK_ALREADY_STARTED")
        self._started = True
        try:
            self._thread.start()
        except BaseException:
            self._result = 1
            self._done.set()
            raise

    def poll(self):
        return self._result if self._done.is_set() else None

    def wait(self, timeout=None):
        if not self._done.wait(timeout):
            raise TimeoutError("BACKEND_TASK_STILL_ACTIVE")
        return self._result
